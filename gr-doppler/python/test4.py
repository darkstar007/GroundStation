
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
import doppler_swig as doppler
import sys
sys.path.append('/home/matt/devel/GroundStation')

import GnuRadio2

class MyTestApp(grc_wxgui.top_block_gui):
    def __init__(self):
        grc_wxgui.top_block_gui.__init__(self, title = "Base Ground Station Receiver")
        _icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        fname = "/data/matt/mygnuradio/osmo2_Aeneas_SO50_ITUpSAT1_1536k_20130803142623_o436994178.383.dat"
        print '2'

        self.file_source = blocks.file_source(gr.sizeof_gr_complex*1,
                                                       fname, True)

        self.throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, 1536000)
        
        self.fftsink0 = fftsink2.fft_sink_c(
            self.GetWin(),
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=-35,
            ref_scale=2.0,
            sample_rate=1536000,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (All)",
            peak_hold=True,
            )
        self.Add(self.fftsink0.win)
        ds = GnuRadio2.ChannelDownsample(self.GetWin(), 'ITUpSAT', 1536000, -142e3, 'poo.dat')
        
        dop = doppler.doppler_c('1 35935U 09051E   13214.30935178  .00000351  00000-0  95268-4 0  2690',
                                '2 35935  98.3696 322.5545 0007075 281.7840  78.2562 14.53379957204541',
                                437.3e6, 1536000/6,
                                52.44332,-0.10982, 0.0,
                                2013, 8, 3, 13, 26, 23, 0)
        multiply =  gr.multiply_vcc(1)

        self.Add(ds.wxgui_fftsink0.win)

        self.fftsink1 = fftsink2.fft_sink_c(
            self.GetWin(),
            baseband_freq=0,
            y_per_div=5,
            y_divs=10,
            ref_level=-35,
            ref_scale=2.0,
            sample_rate=1536000/6,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot (UNDopplered)",
            peak_hold=True,
            )
        self.Add(self.fftsink1.win)
        self.connect(self.file_source, self.throttle_0)
        self.connect(self.throttle_0, self.fftsink0)
        self.connect(self.throttle_0, ds)
        self.connect(ds, (multiply, 0))
        self.connect(dop, (multiply, 1))
        self.connect(multiply, self.fftsink1)

        print '3'

        
if __name__ == '__main__':
    app = MyTestApp()
    app.Run()

