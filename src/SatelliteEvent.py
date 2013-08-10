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
# along with GroundStation; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
import ephem
from scipy.interpolate import interp1d
import scipy.constants
import time
import xmlrpclib
import math
from subprocess import Popen, call, PIPE
import os
import datetime
import atexit

import GnuRadio

class SatelliteEvent():
    def __init__(self, obs, sat, freq, mode):
        self.freq = freq
        self.if_freq = 33000.0
        self.cal_freq = (35000.0 - 5600.0)* freq / 437.0e6
        self.samp_rate = 1536000.0
        
        tobs = obs
        tr, azr, tt, altt, ts, azs = obs.next_pass(sat)
        tr=ephem.now()
        data_x = []
        data_y = []
        count = 0
        while tr < ts:
            obs.date = tr
            sat.compute(obs)
            if count % 10 == 0:
                print "%s | %4.1f %5.1f | %4.1f %+6.1f | %5.1f | %+6.1f" % \
                      (tr,
                       math.degrees(sat.alt),
                       math.degrees(sat.az),
                       math.degrees(sat.sublat),
                       math.degrees(sat.sublong),
                       sat.range/1000.,
                       sat.range_velocity * self.freq / scipy.constants.c)
            count += 1
            data_x.append(tr)
            data_y.append(sat.range_velocity * self.freq / scipy.constants.c)
            
            tr += 1.0 * ephem.second
        self.dopp_fn = interp1d(data_x, data_y, kind='cubic')
        self.pointReceiver(sat.alt, sat.az)
        self.rx_client = None
        self.tx_client = None
        self.fname = '/data/matt/mygnuradio/GroundStation_'+sat.name.replace(' ', '_').replace('/', '_')+'_'+ephem.now().datetime().strftime('%Y%m%d_%H%M%s')+'.dat'
        self.gr_stages = []
        self.fp_in = None
        self.fp_out = None
        atexit.register(self.cleanup)
        self.startReceiving(sat, mode)
        print 'output filename', self.fname
        
    def update(self, sat):
        self.pointReceiver(sat.alt, sat.az)
        try:
            self.tuneReceiver(self.dopp_fn(ephem.now()))
        except ValueError, e:
            print 'Value error....'
                          
    def finish(self):
        self.stopReceiving()

    # If only I had an antenna to steer!
    def pointReceiver(self, alt, az):
        pass
                
    def startReceiving(self, sat, mode):
        self.gr_stages.append(GnuRadio.GR_server(self.freq, self.cal_freq, self.samp_rate, self.if_freq))
        self.gr_stages.append(GnuRadio.GR_client_stage1(self.fname, self.samp_rate, self.freq, self.if_freq))

        need_decoder = False
        decoder_options = []
        
        if mode == 'APRS':
            print 'Doing APRS'
            self.gr_stages.append(GnuRadio.GR_client_stage2_fm())
            decoder_options.append('-A')
            need_decoder = True
            
        elif mode == '1k2_AFSK':
            print 'Doing 1200 AFSK'
            self.gr_stages.append(GnuRadio.GR_client_stage2_fm())
            decoder_options.append('-a')
            decoder_options.append('AFSK1200')
            need_decoder = True

        elif mode == '9k6_FSK':
            print 'Doing 9600 FSK'
            self.gr_stages.append(GnuRadio.GR_client_stage2_fm())
            decoder_options.append('-a')
            decoder_options.append('FSK9600')
            need_decoder = True

        else:
            print 'Doing SSB'
            self.gr_stages.append(GnuRadio.GR_client_stage2_ssb())
            
        self.gr_stages.append(GnuRadio.GR_client_audio(self.fname))
        
        if need_decoder:
            self.fp_in = open('/dev/null', 'rb')
            self.fp_out = open(self.fname[:-4]+'.txt', 'wb')
            pname = '/data/matt/mygnuradio/GroundStation_pipe'
            self.decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + [pname], bufsize=-1, stdin=self.fp_in,
                                 stderr=self.fp_out, stdout=self.fp_out)
            self.gr_stages[-1].usePipe(pname)

        self.gr_stages[-1].xmlserver.set_audio_fname(self.fname[:-4]+'_22.05k.raw')

        self.gr_stages[1].xmlserver.set_record(1)

        
    def tuneReceiver(self, dopp):
        try:
            self.gr_stages[1].xmlserver.set_if_freq(float(self.if_freq - dopp))
            self.gr_stages[1].xmlserver.set_freq(float(self.freq - dopp))
        except Exception,e:
            fp = open('satevent.log', 'a')
            fp.seek(0, os.SEEK_END)
            print 'Oh dear ', e
            fp.write(str(datetime.datetime.now())+' tuneRec() '+str(e)+'\n')
            fp.close()

    def cleanup(self):
        print 'Doing cleanup'
        try:
            self.decoder.terminate()
        except Exception, e:
            print 'Decoder ',e
        
        for p in self.gr_stages:
            p.shutdown()

        if self.fp_out is not None:
            self.fp_out.close()
        if self.fp_in is not None:
            self.fp_in.close()
            
    def stopReceiving(self):
        self.cleanup()
        
