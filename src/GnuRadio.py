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

import time
import xmlrpclib
import math
from subprocess import Popen, call, PIPE
import os
import datetime
import atexit

class GnuRadioFlowGraph():
    def __init__(self, name):
        self.xmlserver = None
        self.name = name
        self.fp_in = open('/dev/null', 'rb')
        self.fp_out = open('/dev/null', 'wb')
        self.makeGnuRadio(name)
        
    def makeGnuRadio(self, name):
        if not os.path.exists(name):
            try:
                os.mkdir(name)
            except Exception, e:
                print 'Failed to make directory', e
                raise e
            
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

    def startGnuRadioProcess(self, init):
        try:
            self.proc = Popen(['python', self.name+'/top_block.py'], bufsize=-1, stdin=self.fp_in, stderr=self.fp_out,
                               stdout=self.fp_out)
            time.sleep(2)   # is there a neater/more robust way of doing this?
            init()
            
        except Exception,e:
            fp = open('satevent.log', 'a')
            fp.seek(0, os.SEEK_END)
            print 'Oh dear ', e
            fp.write(str(datetime.datetime.now())+' init('+self.name+') '+str(e)+' = '+str(self.proc.poll())+'\n')
            fp.close()
            try:
                if self.proc.poll() == None:
                    time.sleep(2)
                    init()
                else:
                    raise ValueError
            except Exception,e2:
                fp = open('satevent.log', 'a')
                fp.seek(0, os.SEEK_END)
                print 'Oh dear2 ', e2
                fp.write(str(datetime.datetime.now())+' init('+self.name+') '+str(e)+' = '+str(self.proc.poll())+'\n')
                fp.close()
                raise ValueError

    def shutdown(self):
        if self.proc is not None and self.proc.poll() == None and self.xmlserver is not None:
            #self.xmlserver.stop()
            self.xmlserver = None
            
        if self.proc is not None:
            time.sleep(1)

            try:
                self.proc.kill()
                print 'Shut down', self.name
            except Exception, e:
                print 'Shut down error',self.name,':',e, self.proc.poll(), self.proc.pid
            del self.proc
            self.proc = None

        self.fp_in.close()
        self.fp_out.close()

class GR_server(GnuRadioFlowGraph):
    def __init__(self, freq, cal_freq, samp_rate, if_freq):
        GnuRadioFlowGraph.__init__(self, 'rx_server')
        self.freq = freq
        self.cal_freq = cal_freq
        self.samp_rate = samp_rate
        self.if_freq = if_freq
        self.startGnuRadioProcess(self.initServer)
        
    def initServer(self):
        try:
            self.xmlserver = xmlrpclib.ServerProxy('http://localhost:8084')
            self.xmlserver.set_freq(self.freq+self.cal_freq)
            self.xmlserver.set_samp_rate(self.samp_rate)
            self.xmlserver.set_if_freq(self.if_freq)
            self.xmlserver.set_rf_gain(30)

        except Exception, e:
            raise e
    
class GR_client_stage1(GnuRadioFlowGraph):
    def __init__(self, fname, samp_rate, freq, if_freq):
        GnuRadioFlowGraph.__init__(self, 'rx_client_stage1')
        self.fname = fname
        self.samp_rate = samp_rate
        self.if_freq = if_freq
        self.startGnuRadioProcess(self.initStage1)

    def initStage1(self):
        try:
            self.xmlserver = xmlrpclib.ServerProxy('http://localhost:8093')
            self.xmlserver.set_fname(self.fname)
            self.xmlserver.set_fname2(self.fname[:-4]+"_sub.dat")
            #self.xmlserver.set_record(1)
            self.xmlserver.set_samp_rate(self.samp_rate)
            self.xmlserver.set_if_freq(self.if_freq)
            #self.xmlserver.set_freq(self.freq)
            #
        except Exception, e:
            raise e

class GR_client_stage2_ssb(GnuRadioFlowGraph):
    def __init__(self):
        GnuRadioFlowGraph.__init__(self, 'rx_client_stage2_ssb')
        self.startGnuRadioProcess(self.initStage2_ssb)

    def initStage2_ssb(self):
        try:
            self.xmlserver = xmlrpclib.ServerProxy('http://localhost:8098')
        except Exception, e:
            raise e

class GR_client_stage2_fm(GnuRadioFlowGraph):
    def __init__(self):
        GnuRadioFlowGraph.__init__(self, 'rx_client_stage2_fm')
        self.startGnuRadioProcess(self.initStage2_fm)

    def initStage2_fm(self):
        try:
            self.xmlserver = xmlrpclib.ServerProxy('http://localhost:8099')
        except Exception, e:
            raise e

class GR_client_audio(GnuRadioFlowGraph):
    def __init__(self, fname):
        GnuRadioFlowGraph.__init__(self, 'rx_client_audio')
        self.fname = fname
        self.startGnuRadioProcess(self.initAudio)

    def initAudio(self):
        try:
            self.xmlserver = xmlrpclib.ServerProxy('http://localhost:8091')
        except Exception, e:
            raise e

    def usePipe(self, pname):
        self.xmlserver.set_use_pipe(1)
        self.xmlserver.set_pipe_fname(pname)

