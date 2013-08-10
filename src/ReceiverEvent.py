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
import GnuRadio2

class ReceiverEvent():
    def __init__(self, time, duration, frequency, bandwidth):
        self.freq = frequency
        self.duration = 60.0 * duration   # Lets keep it in seconds.
        self.bandwidth = bandwidth
        self.channels = []
        self.timerInterval = (time - ephem.now()) * 24.0 * 60.0 * 60.0 * 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.startReceiving)
        self.timer.setSingleShot(True)
        self.timer.start(self.timerInterval)

    def addChannel(self, channel):
        self.channels.append(channel)

    def startReceiving(self):
        self.timer.stop()
        self.timer.timeout.connect(self.stopReceiving)
        self.timer.start(self.duration * 1000)
        for c in self.channels:
            c.startCountdown()
        self.rx = GnuRadio2.Receiver(frequency, bandwidth)
        self.rx.start()
        
    def stopReceiving(self):
        # Loop through all the channels and make sure they're dead?...
        self.rx.stop()
        

    
