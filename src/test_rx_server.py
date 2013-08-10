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


rx_server = Popen(['python', 'rx_server/top_block.py'])
time.sleep(2)
rx_serverXML = xmlrpclib.Server('http://localhost:8084')
rx_serverXML.set_freq(101.9e6)
rx_serverXML.set_samp_rate(1536000)
rx_serverXML.set_if_freq(25000.0)
rx_serverXML.set_rf_gain(30)
rx_serverXML.run()

time.sleep(20)
rx_server.terminate()
