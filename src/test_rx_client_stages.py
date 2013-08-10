import xmlrpclib
from subprocess import Popen, call
import os
import time

def makeGnuRadio(name):
    if not os.path.exists(name):
        try:
            os.mkdir(name)
        except Exception, e:
            print e

    tb_exists = os.path.exists(name+'/top_block.py') 

    tb_old = False
    if tb_exists:
        stat_tb = os.stat(name+'/top_block.py')
        stat_grc = os.stat(name+'.grc')
        if stat_grc.st_mtime > stat_tb.st_mtime:
            print 'GRC is older than top_block for ', name
            tb_old = True

    if not tb_exists or tb_old:
        sts = call('grcc -d '+name+' '+name+'.grc', shell=True)
        if sts < 0:
            print 'Oh status, grc '+name+'.grc failed!'

rx_server = None
rx_client_stage1 = None
rx_client_stage2 = None
rx_client_audio = None
decoder = None
#global rx_server, rx_client_stage1, rx_client_stage2, decoder

def cleanup():
    global rx_server, rx_client_stage1, rx_client_stage2, rx_client_audio, decoder
    print 'Doing cleanup'
    
    if rx_server is not None:
        rx_server.terminate()
        del rx_server

    if rx_client_stage1 is not None:
        rx_client_stage1.terminate()
        del rx_client_stage1

    if rx_client_stage2 is not None:
        rx_client_stage2.terminate()
        del rx_client_stage2

    if rx_client_audio is not None:
        rx_client_audio.terminate()
        del rx_client_audio

    if decoder is not None:
        decoder.terminate()
        decoder = None

    
import atexit
atexit.register(cleanup)

procs = ['rx_server_test', 'rx_client_stage1', 'rx_client_stage2_fm', 'rx_client_audio']

for p in procs:
    makeGnuRadio(p)

xml = {}

fp_in = open('/dev/null', 'rb')
fp_out = open('/dev/null', 'wb')

try:
    rx_server = Popen(['python', 'rx_server_test/top_block.py'], bufsize=-1, stdin=fp_in, stderr=fp_out, stdout=fp_out)
    time.sleep(1)
    rx_serverXML = xmlrpclib.ServerProxy('http://localhost:8084')
    rx_serverXML.set_freq(101.9e6)
    rx_serverXML.set_samp_rate(1536000)
    rx_serverXML.set_if_freq(35000.0)
    rx_serverXML.set_rf_gain(30)
    print 'server'
    
    rx_client_stage1 = Popen(['python', 'rx_client_stage1/top_block.py'], bufsize=-1, stdin=fp_in, stderr=fp_out, stdout=fp_out)
    time.sleep(1)
    rx_clientXML_stage1 = xmlrpclib.ServerProxy('http://localhost:8093')
    time.sleep(0.5)
    rx_clientXML_stage1.set_fname("pants.dat")
    rx_clientXML_stage1.set_fname2("pants2.dat")
    rx_clientXML_stage1.set_samp_rate(1536000)
    rx_clientXML_stage1.set_if_freq(11000.0)
    #rx_clientXML_stage1.set_rf_gain(30)
    #rx_clientXML_stage1.set_record(1)
    print 'client s1'
    
    rx_client_stage2 = Popen(['python', 'rx_client_stage2_ssb/top_block.py'], bufsize=-1, stdin=fp_in, stderr=fp_out, stdout=fp_out)
    time.sleep(1)
    #rx_clientXML_stage2 = xmlrpclib.ServerProxy('http://localhost:8099')
    #rx_clientXML_stage2.set_mode(1)
    print 'client s2'
    
    rx_client_audio = Popen(['python', 'rx_client_audio/top_block.py'], bufsize=-1, stdin=fp_in, stderr=fp_out, stdout=fp_out)
    time.sleep(1)
    #rx_clientXML_audio = xmlrpclib.ServerProxy('http://localhost:8091')
    #rx_clientXML_audio.set_af_gain(0.2)
    print 'clinet audio'

    decoder = Popen(['multimon-ng', '-t', 'raw',  '-A', '/data/matt/mygnuradio/GroundStation_pipe'])
    time.sleep(600)
except Exception, e:
    print 'quack', e

print 'Done'

cleanup()

print 'Terminated'

time.sleep(30)

