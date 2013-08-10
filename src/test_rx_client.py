import xmlrpclib
from subprocess import Popen, call
import os
import time

try:
    os.mkdir('rx_server')
except Exception, e:
    print e
sts = call('grcc -d rx_server rx_server.grc', shell=True)
if sts < 0:
    print 'Oh status, grc rx_server.grc failed!'

try:
    os.mkdir('rx_client')
except Exception, e:
    print e
sts = call('grcc -d rx_client rx_client.grc', shell=True)
if sts < 0:
    print 'Oh status, grc rx_client.grc failed!'

rx_server = None
rx_client = None

try:
    rx_server = Popen(['python', 'rx_server/top_block.py'])
    time.sleep(1)
    rx_serverXML = xmlrpclib.Server('http://localhost:8084')
    rx_serverXML.set_freq(101.9e6)
    rx_serverXML.set_samp_rate(1536000)
    rx_serverXML.set_if_freq(35000.0)
    rx_serverXML.set_rf_gain(30)
    rx_serverXML.run()

    rx_client = Popen(['python', 'rx_client/top_block.py'])
    time.sleep(1)
    rx_clientXML = xmlrpclib.Server('http://localhost:8092')
    rx_clientXML.set_fname("pants.dat")
    rx_clientXML.set_samp_rate(1536000)
    rx_clientXML.set_if_freq(35000.0)
    #rx_clientXML.set_rf_gain(30)
    rx_clientXML.set_mode(0)
    rx_clientXML.set_record(1)
    
    time.sleep(20)
except Exception, e:
    print e

if rx_server is not None:
    rx_server.terminate()

if rx_client is not None:
    rx_client.terminate()

