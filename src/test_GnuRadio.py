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

gr_stages = []

def cleanup():
    print 'Doing cleanup'
    for p in gr_stages:
        p.shutdown()

atexit.register(cleanup)

freq = 437.5e6
if_freq = 33000.0
cal_freq = (35000.0 - 5600.0)* freq / 437.0e6
samp_rate = 1536000.0
fname='mypants.dat'
mode = 'SSB'

gr_stages.append(GnuRadio.GR_server(freq, cal_freq, samp_rate, if_freq))
gr_stages.append(GnuRadio.GR_client_stage1(fname, samp_rate, if_freq))

need_decoder = False
decoder_options = []

if mode == 'APRS':
    print 'Doing APRS'
    gr_stages.append(GnuRadio.GR_client_stage2_fm())
    decoder_options.append('-A')
    need_decoder = True

elif mode == '1k2_AFSK':
    print 'Doing 1200 AFSK'
    gr_stages.append(GnuRadio.GR_client_stage2_fm())
    decoder_options.append('-a')
    decoder_options.append('AFSK1200')
    need_decoder = True

elif mode == '9k6_FSK':
    print 'Doing 9600 FSK'
    gr_stages.append(GnuRadio.GR_client_stage2_fm())
    decoder_options.append('-a')
    decoder_options.append('FSK9600')
    need_decoder = True

else:
    print 'Doing SSB'
    gr_stages.append(GnuRadio.GR_client_stage2_ssb())

if need_decoder:
    #fp_in = open('/dev/null', 'rb')
    #fp_out = open('/dev/null', 'wb')

    decoder = Popen(['multimon-ng', '-t', 'raw'] + decoder_options + ['/data/matt/mygnuradio/GroundStation_pipe'])
print 'post decoder'

print 'Pre audio'
gr_stages.append(GnuRadio.GR_client_audio(fname, need_decoder))
print 'post audio'


gr_stages[1].xmlserver.set_record(1)
print 'sleeping'

time.sleep(100)
