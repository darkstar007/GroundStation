#
# Copyright 2013 Matthew Nottingham
#
# This file is part of GroundStation
#
# GroundStation is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GroundStation is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import audio
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import blocks
from gnuradio import blks2
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import blks2 as grc_blks2
from grc_gnuradio import wxgui as grc_wxgui
from gnuradio.wxgui import fftsink2
from optparse import OptionParser
import SimpleXMLRPCServer
import osmosdr
import threading
import wx
from multiprocessing import Process
import time
import math
from subprocess import Popen, call, PIPE
import os
import datetime
import atexit
import cjson
import doppler
import datetime


class Receiver(gr.top_block):
    def __init__(self, frequency, sample_rate = 1.536e6, rf_gain = 0, port=7890):
        gr.top_block.__init__(self, "Groundstation_receiver")
        self.sample_rate = sample_rate
        self.rf_gain = rf_gain
        self.freq = frequency
        self.port = port
        
        self.osmosdr_source_c_0 = osmosdr.source_c( args="nchan=" + str(1) + " " + ""  )
        self.osmosdr_source_c_0.set_sample_rate(self.sample_rate)
        self.osmosdr_source_c_0.set_center_freq(self.freq, 0)
        self.osmosdr_source_c_0.set_freq_corr(0, 0)
        self.osmosdr_source_c_0.set_gain_mode(0, 0)
        self.osmosdr_source_c_0.set_gain(rf_gain, 0)
        self.blks2_tcp_sink_0 = grc_blks2.tcp_sink(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=self.port,
            server=True,
            )

        self.connect((self.osmosdr_source_c_0, 0), (self.blks2_tcp_sink_0, 0))

class ReceiverTest(gr.top_block):
    def __init__(self, frequency, sample_rate = 1.536e6, rf_gain = 0, port=7890):
        gr.top_block.__init__(self, "Groundstation receiver test")

        self.sample_rate = sample_rate
        self.rf_gain = rf_gain
        self.freq = frequency
        self.port = port
        #fname = "/data/matt/mygnuradio/GroundStation_Aeneas_20130714_19131373825603.dat"
        #fname = "/data/matt/mygnuradio/osmo2_Aeneas_SO50_ITUpSAT1_1536k_20130803142623_o436994178.383.dat"
        fname = "/data/matt/mygnuradio/osmo2_Aeneas_1536k_20130804145025_oNA.dat"

        self.file_source = blocks.file_source(gr.sizeof_gr_complex*1,
                                              fname,
                                              repeat=False)

        self.tcp_sink = grc_blks2.tcp_sink(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=self.port,
            server=True,
            )

        self.connect((self.file_source, 0), (self.tcp_sink, 0))


class ChannelDownsample(gr.hier_block2):
    def __init__(self, win, sat_name, sample_rate, frequency_offset, filename_raw,
                 frequency, line1, line2, lat, lon, alt, when):
        gr.hier_block2.__init__(self, "Channel "+str(sat_name),
                                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                                gr.io_signature(1, 1, gr.sizeof_gr_complex))
        
        self.sample_rate = sample_rate
        self.freq_offset = frequency_offset
        self.fname = filename_raw
        self.decim = 6
        if isinstance(when, dict):
            when = datetime.datetime(when['year'], when['month'], when['day'],
                                     when['hour'], when['minute'], when['second'], when['microsecond'])
            
        self.dop = doppler.doppler_c(line1, line2, frequency, self.sample_rate / self.decim,
                                     lat, lon, alt/1000.0,
                                     when.year, when.month, when.day, when.hour, when.minute,
                                     when.second, when.microsecond)
        self.mult2 = gr.multiply_vcc(1)
        
        self.wxgui_fftsink0 = fftsink2.fft_sink_c(
            win,
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=-35,
            ref_scale=2.0,
            sample_rate=self.sample_rate/(self.decim),
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (Downsampled - "+sat_name+")",
            peak_hold=True,
            )

        self.low_pass_filter = gr.fir_filter_ccf(self.decim,
                                                 firdes.low_pass(1, sample_rate, 120000, 5000, firdes.WIN_HAMMING, 6.76))
        self.sig_source = gr.sig_source_c(sample_rate, gr.GR_COS_WAVE, -(self.freq_offset), 1, 0)
        self.mult1 = gr.multiply_vcc(1)

        self.file_sink_raw = gr.file_sink(gr.sizeof_gr_complex*1, str(filename_raw))
        self.file_sink_raw.set_unbuffered(False)

        self.connect(self, (self.mult1, 0))
        self.connect((self.sig_source, 0), (self.mult1, 1))
        self.connect((self.mult1, 0), (self.low_pass_filter, 0))
        self.connect((self.low_pass_filter, 0), (self.mult2, 0))
        self.connect((self.dop, 0), (self.mult2, 1))
        self.connect((self.low_pass_filter, 0), (self.file_sink_raw, 0))
        self.connect((self.mult2, 0), (self.wxgui_fftsink0, 0))
        self.connect((self.mult2, 0), self)

class ChannelDemodFM(gr.hier_block2):
    def __init__(self, win, sat_name, nbfm = True):
        gr.hier_block2.__init__(self, "Channel "+str(sat_name)+" FM",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                                gr.io_signature(1, 1, gr.sizeof_gr_complex))

        self.trans_fm = trans_fm = 1500
        self.samp_rate = samp_rate = 1536000
        self.mode = mode = 1
        self.decim = decim = 6

        self.low_pass_filter = gr.fir_filter_ccf(4, firdes.low_pass(
            1, samp_rate/decim, 10000, trans_fm, firdes.WIN_HAMMING, 6.76))

        if nbfm:
            self.fm_demod = blks2.fm_demod_cf(
                channel_rate=64000,
                audio_decim=2,
                deviation=5000,
                audio_pass=4500,
                audio_stop=4900,
                gain=1.0,
                tau=75e-6,
                )
        else:
            self.fm_demod = blks2.fm_demod_cf(
                channel_rate=64000,
                audio_decim=2,
                deviation=45000,
                audio_pass=17000,
                audio_stop=18000,
                gain=1.0,
                tau=75e-6,
		)
        self.fftsink_audio = fftsink2.fft_sink_f(
            win,
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=0,
            ref_scale=2.0,
            sample_rate=32000,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (Audio - "+sat_name+")",
            peak_hold=True,
            )

        self.connect(self, (self.low_pass_filter, 0))
        self.connect((self.low_pass_filter, 0), (self.fm_demod, 0))
        self.connect((self.fm_demod, 0), (self.fftsink_audio, 0))
        self.connect((self.fm_demod, 0), self)

class ChannelDemodSSB(gr.hier_block2):
    def __init__(self, win, sat_name):
        gr.hier_block2.__init__(self, "Channel "+str(sat_name)+" SSB",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                                gr.io_signature(1, 1, gr.sizeof_gr_complex))

        self.trans = trans = 500
        self.sample_rate = sample_rate = 1536000
        self.low_ssb = low_ssb = 200
        self.high_ssb = high_ssb = 2800
        self.decim = decim = 6
        self.agc_decay = agc_decay = 50e-6

        ##################################################
        # Blocks
        ##################################################
        self.fftsink_audio = fftsink2.fft_sink_f(
            win,
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=-20,
            ref_scale=2.0,
            sample_rate=32000,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (Audio - "+sat_name+")",
            peak_hold=True,
            )

        self.gr_multiply_const_vxx_1_0 = blocks.multiply_const_vff((64, ))
        self.gr_complex_to_real_0 = gr.complex_to_real(1)

        self.blks2_rational_resampler_xxx_1 = blks2.rational_resampler_ccc(
            interpolation=32,
            decimation=64,
            taps=None,
            fractional_bw=None,
            )
        self.band_pass_filter = gr.fir_filter_ccc(4, firdes.complex_band_pass(
            1, sample_rate/decim, low_ssb, high_ssb, trans, firdes.WIN_HAMMING, 6.76))
        self.agc = gr.agc2_cc(0.1, agc_decay, 0.9, 1.0, 1.0)
        
        ##################################################
        # Connections
        ##################################################
        #self.connect(self, (self.gr_throttle_0, 0))

        self.connect(self, (self.band_pass_filter, 0))
        self.connect((self.band_pass_filter, 0), (self.agc, 0))
        self.connect((self.agc, 0), (self.blks2_rational_resampler_xxx_1, 0))
        self.connect((self.blks2_rational_resampler_xxx_1, 0), (self.gr_complex_to_real_0, 0))
        self.connect((self.gr_complex_to_real_0, 0), (self.gr_multiply_const_vxx_1_0, 0))
        self.connect((self.gr_multiply_const_vxx_1_0, 0), (self.fftsink_audio, 0))
        self.connect((self.gr_multiply_const_vxx_1_0, 0), self)

class ChannelAudio(gr.hier_block2):
    def __init__(self, win, sat_name, audio_fname, pipe_fname = None, rec_gain = 50000, af_gain = 0.1):
        gr.hier_block2.__init__(self, "Channel "+str(sat_name)+" Audio",
                                gr.io_signature(1, 1, gr.sizeof_gr_complex),
                                gr.io_signature(0, 0, 0))
        
        self.sample_rate = sample_rate = 32000
        self.rec_gain = rec_gain
        self.af_gain = af_gain

        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((af_gain, ))
        self.blocks_float_to_short_0 = blocks.float_to_short(1, rec_gain)
        self.blocks_file_sink_file = blocks.file_sink(gr.sizeof_short*1, str(audio_fname))
        self.blocks_file_sink_file.set_unbuffered(False)
        if pipe_fname is not None:
            self.blocks_file_sink_pipe = blocks.file_sink(gr.sizeof_short*1, str(pipe_fname))
            self.blocks_file_sink_pipe.set_unbuffered(False)

        self.blks2_rational_resampler_xxx_1_0_0 = blks2.rational_resampler_fff(
            interpolation=48,
            decimation=32,
            taps=None,
            fractional_bw=None,
            )
        self.blks2_rational_resampler_xxx_1_0 = blks2.rational_resampler_fff(
            interpolation=2205,
            decimation=sample_rate/10,
            taps=None,
            fractional_bw=None,
            )
        self.audio_sink_0 = audio.sink(48000, "pulse", True)

        ##################################################
        # Connections
        ##################################################

        self.connect(self, (self.blks2_rational_resampler_xxx_1_0, 0))
        self.connect(self, (self.blks2_rational_resampler_xxx_1_0_0, 0))
        self.connect((self.blks2_rational_resampler_xxx_1_0_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.audio_sink_0, 0))
        self.connect((self.blks2_rational_resampler_xxx_1_0, 0), (self.blocks_float_to_short_0, 0))
        if pipe_fname is not None:
            self.connect((self.blocks_float_to_short_0, 0), (self.blocks_file_sink_pipe, 0))
        self.connect((self.blocks_float_to_short_0, 0), (self.blocks_file_sink_file, 0))


class ReceiverStage1(gr.hier_block2):
    def __init__(self, win, filename_raw, sample_rate):
        gr.hier_block2.__init__(self, "Receiver Stage 1",
                                gr.io_signature(0, 0, 0),
                                gr.io_signature(1, 1, gr.sizeof_gr_complex))
        
        self.sample_rate = sample_rate
        self.fname = filename_raw
        self.decim = 6

    
        self.wxgui_fftsink2_1 = fftsink2.fft_sink_c(
            win,
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=-35,
            ref_scale=2.0,
            sample_rate=self.sample_rate,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (input)",
            peak_hold=True,
            )

        self.blks2_tcp_source_0 = grc_blks2.tcp_source(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=7890,
            server=False,
            )
        self.gr_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, sample_rate)

        if filename_raw is not None:
            self.file_sink_raw = blocks.file_sink(gr.sizeof_short*1, str(filename_raw))
            self.file_sink_raw.set_unbuffered(False)
            
        ##################################################
        # Connections
        ##################################################
        self.connect((self.blks2_tcp_source_0, 0), (self.gr_throttle_0, 0))
        self.connect((self.gr_throttle_0, 0), (self.wxgui_fftsink2_1, 0))
        if filename_raw is not None:
            self.connect((self.gr_throttle_0, 0), (self.file_sink_raw, 0))
        self.connect((self.gr_throttle_0, 0), self)


class Base_RX(grc_wxgui.top_block_gui):
    def __init__(self, filename_raw, sample_rate):
        grc_wxgui.top_block_gui.__init__(self, title = "Base Ground Station Receiver")
        _icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        self.front = ReceiverStage1(self.GetWin(), filename_raw, sample_rate)
        self.Add(self.front.wxgui_fftsink2_1.win)
        self.default_sink = blocks.null_sink(gr.sizeof_gr_complex*1)

        self.connect((self.front,0), (self.default_sink, 0))
        self.active_channels = []
        self.port = 9010
        
    def add_channel(self, channel, args, kwords):
        self.stop()
        self.wait()
        kwords['port'] = self.port
        #threading.Thread(target=run_channel, args=(channel, args,kwords)).start()
        Process(target=run_channel, args=(channel, args, kwords)).start()
        print 'made newchan'
        print 'lock'
        newport = grc_blks2.tcp_sink(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=self.port,
            server=True,
            )
        print 'made sink'
        self.active_channels.append((self.port, newport))
        idx = len(self.active_channels) - 1
        print 'pre connect'
        self.connect((self.front,0), (newport, 0))
        print 'connect'
        self.start()
        print 'unlock'
        self.port +=1
        return idx
    
    
    def del_channel(self, idx):
        self.disconnect(self.active_channel[idx])
        del self.active_channel[idx]
        
class SSB_RX_Channel(grc_wxgui.top_block_gui):
    def __init__(self, sat_name, audio_fname, frequency, line1, line2, lat, lon, alt, when,
                 port = 0, pipe_fname = None, sample_rate=1536000,
                 frequency_offset = 0, filename_raw = 'pants_raw_ssb.dat', audio = True):

        grc_wxgui.top_block_gui.__init__(self, title = "SSB Channel "+sat_name)
        _icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        self.tcp_source = grc_blks2.tcp_source(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=port,
            server=False,
            )
        self.gr_throttle = blocks.throttle(gr.sizeof_gr_complex*1, sample_rate)

        self.chandown = ChannelDownsample(self.GetWin(), sat_name, sample_rate, frequency_offset, filename_raw,
                                          frequency, line1, line2, lat, lon, alt, when)
        self.Add(self.chandown.wxgui_fftsink0.win)
        self.demod = ChannelDemodSSB(self.GetWin(), sat_name)
        self.Add(self.demod.fftsink_audio.win)
        if audio:
            self.audio = ChannelAudio(sat_name, audio_fname, pipe_fname)
        else:
            self.audio = blocks.null_sink(gr.sizeof_gr_complex*1)

        self.connect(self.tcp_source, self.gr_throttle)
        self.connect(self.gr_throttle, self.chandown)
        self.connect(self.chandown, self.demod)
        self.connect(self.demod, self.audio)

class FM_RX_Channel(grc_wxgui.top_block_gui):
    def __init__(self, sat_name, audio_fname, frequency, line1, line2, lat, lon, alt, when,
                 port = 0, pipe_fname = None, sample_rate=1536000,
                 frequency_offset = 0, filename_raw = 'pants_raw_fm.dat', audio = True):

        grc_wxgui.top_block_gui.__init__(self, title = "FM Channel "+sat_name)
        _icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        self.tcp_source = grc_blks2.tcp_source(
            itemsize=gr.sizeof_gr_complex*1,
            addr="127.0.0.1",
            port=port,
            server=False,
            )
        self.gr_throttle = blocks.throttle(gr.sizeof_gr_complex*1, sample_rate)

        self.chandown = ChannelDownsample(self.GetWin(), sat_name, sample_rate, frequency_offset, filename_raw,
                                          frequency, line1, line2, lat, lon, alt, when)
        self.Add(self.chandown.wxgui_fftsink0.win)
        self.demod = ChannelDemodFM(self.GetWin(), sat_name)
        self.Add(self.demod.fftsink_audio.win)
        if audio:
            self.audio = ChannelAudio(sat_name, audio_fname, pipe_fname)
        else:
            self.audio = blocks.null_sink(gr.sizeof_gr_complex*1)

        self.connect(self.tcp_source, self.gr_throttle)
        self.connect(self.gr_throttle, self.chandown)
        self.connect(self.chandown, self.demod)
        self.connect(self.demod, self.audio)


def run_capture(freq):
    cpt = ReceiverTest(freq)
    print 'Starting cpt 1'
    cpt.run()
    print 'Finished (cpt)'

def run_rx(rx):
    rx.Run()

def run_channel(channel, args, kwords):
    print 'make chan'
    tmp = []
    for x in args:
        if isinstance(x, datetime.datetime):
            tmp2 = {'year':x.year, 'month':x.month, 'day':x.day,
                    'hour':x.hour, 'minute':x.minute, 'second':x.second, 'microsecond':x.microsecond}
            tmp.append(tmp2)
        else:
            tmp.append(x)
    proc = Popen(['python', 'run_channel.py', str(channel.__name__), cjson.encode(tmp), cjson.encode(kwords)], bufsize=-1)
    print 'run chan'
    #newchan.Run()
    print 'completed chan'


def orig():
    print 'Starting capture'
    threading.Thread(target=run_capture, args=(1.0,)).start()

    print 'Starting the base receiver' 
    rx = Base_RX(None, 1536000)
    threading.Thread(target=run_rx, args=(rx,)).start()

    print 'Started base rx'
    
    time.sleep(5)
    print 'Starting channel decoder'

    args = ('pants', 'pants1.dat', 437.6e6,
            '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 01547',
            '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.81879662026327',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 7, 14, 19, 6, 50, 100))
    kwords = {'frequency_offset':21000.0}
    mchan = rx.add_channel(SSB_RX_Channel, args, kwords)

    print 'Waiting'
    time.sleep(60)
    print 'Next channel'

    args = ('pants3', 'pants3.dat', 437.6e6,
            '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 01547',
            '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.81879662026327',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 7, 14, 19, 7, 20, 100))
    pname = '/data/matt/mygnuradio/GroundStation_pipe'
    kwords = {'frequency_offset':21000.0, 'pipe_fname': pname}
    mchan = rx.add_channel(FM_RX_Channel, args, kwords)
    decoder_options = []
    decoder_options.append('-a')
    decoder_options.append('AFSK1200')

    decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + [pname], bufsize=-1)

def latest():
    print 'Starting capture'
    threading.Thread(target=run_capture, args=(1.0,)).start()

    print 'Starting the base receiver' 
    rx = Base_RX(None, 1536000)
    threading.Thread(target=run_rx, args=(rx,)).start()
    freq = 436994178.383 - 55e3
    cal_freq = (35000.0 - 5600.0)*freq  / 437.0e6
    print 'Started base rx'
    
    time.sleep(5)
    print 'Starting channel decoder'

    args = ('SO50', 'SO50.dat', 437.6e6,
            '1 27607U 02058C   13214.23063743  .00000368  00000-0  77602-4 0  1306',
            '2 27607  64.5573 123.9608 0039787 148.1557 354.4510 14.73014401570490',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 8, 3, 13, 26, 23, 100))
    kwords = {'frequency_offset':(436.795e6 -freq)}
    mchan = rx.add_channel(SSB_RX_Channel, args, kwords)

    print 'Waiting'
    time.sleep(1)
    print 'Next channel'

    args = ('ITUpsat', 'itupsat.dat', 437.6e6,
            '1 35935U 09051E   13214.30935178  .00000351  00000-0  95268-4 0  2690',
            '2 35935  98.3696 322.5545 0007075 281.7840  78.2562 14.53379957204541',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 8, 3, 13, 26, 23, 100))
    pname = '/data/matt/mygnuradio/GroundStation_pipe'
    kwords = {'frequency_offset':(437.325e6-freq)}    #, 'pipe_fname': pname}
    mchan = rx.add_channel(FM_RX_Channel, args, kwords)
    #decoder_options = []
    #decoder_options.append('-a')
    #decoder_options.append('AFSK1200')

    #decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + [pname], bufsize=-1)


    time.sleep(1)
    print 'Next channel'

    args = ('Aeneas', 'aeneas.dat', 437.6e6,
            '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 01547',
            '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.81879662026327',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 8, 3, 13, 21, 23, 100))
    pname = '/data/matt/mygnuradio/GroundStation_pipe'
    kwords = {'frequency_offset':(437.6e6+6.5e3-freq), 'pipe_fname': pname}
    mchan = rx.add_channel(FM_RX_Channel, args, kwords)
    decoder_options = []
    decoder_options.append('-a')
    decoder_options.append('AFSK1200')

    decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + [pname], bufsize=-1)

def latest2():
    print 'Starting capture'
    threading.Thread(target=run_capture, args=(1.0,)).start()

    print 'Starting the base receiver' 
    rx = Base_RX(None, 1536000)
    threading.Thread(target=run_rx, args=(rx,)).start()
    freq=437.6e6
    cal_freq = (35000.0 - 5600.0)*freq  / 437.0e6
    freq = freq - cal_freq - 25e3
    print 'Started base rx'
    
    time.sleep(5)
    print 'Starting channel decoder'

    args = ('SO50', 'SO50.dat', 437.6e6,
            '1 27607U 02058C   13214.23063743  .00000368  00000-0  77602-4 0  1306',
            '2 27607  64.5573 123.9608 0039787 148.1557 354.4510 14.73014401570490',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 8, 4, 13, 50, 25, 100))
    kwords = {'frequency_offset':(436.795e6 -1e3-freq)}
    mchan = rx.add_channel(SSB_RX_Channel, args, kwords)

    print 'Waiting'
    time.sleep(1)
    print 'Next channel'

    time.sleep(1)
    print 'Next channel'

    args = ('Aeneas', 'aeneas.dat', 437.6e6,
            '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 01547',
            '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.81879662026327',
            52.44332,-0.10982, 5.0,
            datetime.datetime(2013, 8, 4, 13, 42, 25, 100))
    pname = '/data/matt/mygnuradio/GroundStation_pipe'
    kwords = {'frequency_offset':(437.6e6-freq), 'pipe_fname': pname}
    mchan = rx.add_channel(FM_RX_Channel, args, kwords)
    decoder_options = []
    decoder_options.append('-a')
    decoder_options.append('AFSK1200')

    decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + [pname], bufsize=-1)
    
if __name__ == '__main__':
    #orig()
    latest2()
    
