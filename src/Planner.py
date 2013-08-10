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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtOpenGL
import ephem
import math
import datetime

class PlannerSat(QtGui.QGraphicsRectItem):
    def __init__(self, x, y, w, h, sat):   #, marker_id, pen, brush, font, db, parent):
        QtGui.QGraphicsRectItem.__init__(self, x, y, w, h)
        brush = QtGui.QBrush()
        
        brush.setStyle(QtCore.Qt.SolidPattern)
        
        if sat.mode == 'APRS':
            brush.setColor(QtGui.QColor(240, 10, 210, 100))
        elif sat.mode == '1k2_AFSK':
            brush.setColor(QtGui.QColor(10, 10, 210, 100))
        elif sat.mode == 'CW':
            brush.setColor(QtGui.QColor(120, 10, 110, 100))
        elif sat.mode == '9k6_GMSK':
            brush.setColor(QtGui.QColor(140, 110, 10, 100))
        else:
            brush.setColor(QtGui.QColor(140, 240, 240, 100))    
        self.setBrush(brush)
        self.setToolTip(sat.sat.name+' : '+sat.mode)
        self.name = sat.sat.name
        self.mode = sat.mode
        self.freq = sat.freq

    def setParams(self, params):
        self.params = params[:]
        
class PlannerReceiver(QtGui.QGraphicsRectItem):
    def __init__(self, scene, bw):
        QtGui.QGraphicsRectItem.__init__(self, scene = scene)
        brush = QtGui.QBrush()
        
        brush.setStyle(QtCore.Qt.SolidPattern)
        brush.setColor(QtGui.QColor(140, 240, 140, 100))

        self.setBrush(brush)
        self.channels = []
        self.ready = False
        self.rx_bw = bw
        
    def setParams(self, time, duration, freq):
        self.start_time = time
        self.duration = duration
        self.freq = freq
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.startReceiver)
        self.timer.setSingleShot(True)
        diff = (self.start_time - ephem.now()) * 24.0 * 60.0 * 60.0 * 1000
        print 'Starting in',diff,'ms'
        self.timer.start(diff)
        self.ready = True

    def startReceiver(self):
        print 'Should be starting rx for', self.freq, 'for', self.duration, 'minutes'
        self.timer.stop()
        self.timer2 = QtCore.QTimer()
        self.timer2.timeout.connect(self.stopReceiver)
        self.timer2.setSingleShot(True)
        self.timer2.start(self.duration * 60.0 * 1000)

    def stopReceiver(self):
        print '******* Stopping.....', self.freq
        self.hide()
        
    def addChannel(self, name, mode, freq, params):
        print 'Adding', name
        self.channels.append(PlannerChannel(self, name, mode, freq, params))

    def update(self, fx0, scale_x, scale_y, off_x, off_y):
        if self.ready:
            y = ((self.start_time - ephem.now()) * 24.0 * 60.0) * scale_y + off_y
            h = min(min(self.duration, (self.start_time - ephem.now()) * 24 * 60 + self.duration) * scale_y, 25 * 60 * scale_y - y)
        
            # Calculate the width from the mode - one day!
            w = self.rx_bw * scale_x
            x = (self.freq - (fx0 * 1e6)) * scale_x + off_x - w/2
            self.setRect(x, max(y, off_y), w, h)
            for x in xrange(len(self.channels)):
                if ephem.now() > self.channels[x].stop_time:
                    self.channels[x].hide()
                else:
                    self.channels[x].update(fx0, scale_x, scale_y, off_x, off_y)
                            
class PlannerChannel(QtGui.QGraphicsRectItem):
    def __init__(self, parent, name, mode, freq, params):
        QtGui.QGraphicsRectItem.__init__(self, parent = parent)
        brush = QtGui.QBrush()
        
        brush.setStyle(QtCore.Qt.SolidPattern)
        brush.setColor(QtGui.QColor(240, 40, 40, 100))

        self.setBrush(brush)
        self.name = name
        self.mode = mode
        self.freq = freq
        self.start_time = params[0]
        self.stop_time = params[4]
        
    def update(self, fx0, scale_x, scale_y, off_x, off_y):
        y = ((self.start_time - ephem.now()) * 24.0 * 60.0) * scale_y + off_y
        h = min(((self.stop_time - max(self.start_time, ephem.now())) * 24.0 * 60.0) * scale_y, 25 * 60 * scale_y - y)
        
        # Calculate the width from the mode - one day!
        w = 6
        x = (self.freq - (fx0 * 1e6)) * scale_x + off_x - w/2
        self.setRect(x, max(y, off_y), w, h)
    
class Planner(QtGui.QGraphicsView):
    def __init__(self, parent = None, freq0 = 435, bw = 3):
        QtGui.QGraphicsView.__init__(self, parent)
        self.setScene(QtGui.QGraphicsScene())
        self.drawAxis()
        self.freq_labels = {}
        self.time_labels = {}
        self.freq_lines = {}
        self.time_lines = {}
        self.old_w = 0
        self.old_h = 0

        self.rx = []

        self.fx0 = int(freq0)
        self.bw = int(bw)
        self.default_rx_bw = 1536000.0 # Need a way to let user configure this - also allow for multiple RX units?
        
    def drawAxis(self):
        
        if self.parent() is not None and (self.old_w != self.parent().width() or self.old_h != self.parent().height()):
            font = QtGui.QFont()
            font.setBold(True)
            font.setPixelSize(15)
            brush = QtGui.QBrush(QtCore.Qt.black)
            fm = QtGui.QFontMetrics(font)
            pen = QtGui.QPen(QtGui.QColor(240, 40, 110, 200))
            w = self.parent().width()
            h = self.parent().height() * 6
            self.old_w = self.parent().width()
            self.old_h = self.parent().height()
            print 'WxH = ',w,h
            self.scale_x = (w * 0.8 / (self.bw * 1e6))           # pixels/Hz
            self.scale_y = (h * 0.9 / (24.0 * 60.0))  # pixels/minute
            self.orig_x = w * 0.05
            self.orig_y = 35

            for x in range(self.fx0,self.fx0+self.bw+1):
                txt = str(x)
                if txt not in self.freq_labels.keys():
                    self.freq_labels[txt] = QtGui.QGraphicsSimpleTextItem(txt, scene=self.scene())
                    self.freq_labels[txt].setFont(font)
                    self.freq_labels[txt].setBrush(brush)
                
                lab_size = (fm.width(txt), fm.height())
                self.freq_labels[txt].setPos((x - self.fx0) * 1e6 * self.scale_x - lab_size[0]/2 + self.orig_x, lab_size[1]/2)

                if txt not in self.freq_lines.keys():
                    self.freq_lines[txt] = QtGui.QGraphicsLineItem(scene=self.scene())
                    self.freq_lines[txt].setPen(pen)
                    
                self.freq_lines[txt].setLine((x - self.fx0) * 1e6 * self.scale_x + self.orig_x, self.orig_y,
                                             (x - self.fx0) * 1e6 * self.scale_x + self.orig_x, self.orig_y + 24.0 * 60.0 * self.scale_y)

            for y in range(0,25):
                txt = str(y)
                if txt not in self.time_labels.keys():
                    self.time_labels[txt] = QtGui.QGraphicsSimpleTextItem(txt, scene=self.scene())
                    self.time_labels[txt].setFont(font)
                    self.time_labels[txt].setBrush(brush)
                    
                lab_size = (fm.width(txt), fm.height())
                self.time_labels[txt].setPos(- lab_size[0]/2+10, y * 60 * self.scale_y - lab_size[1]/2 + self.orig_y)
                
                if txt not in self.time_lines.keys():
                    self.time_lines[txt] = QtGui.QGraphicsLineItem(scene=self.scene())
                    self.time_lines[txt].setPen(pen)
                    
                self.time_lines[txt].setLine(self.orig_x,                                self.orig_y + y * 60.0 * self.scale_y,
                                             self.orig_x + self.scale_x * self.bw * 1e6, self.orig_y + y * 60.0 * self.scale_y)
                
    # I think it makes sense to do everything in decimal minutes
    def update(self, satellite):
        self.drawAxis()
        for passes in xrange(len(satellite.passList)):
            tr, azr, tt, altt, ts, azs = satellite.passList[passes]
            if math.degrees(altt) > 15.0 and (tr - ephem.now()) < 1.0 and satellite.freq > (self.fx0 * 1e6) and satellite.freq < (self.fx0 + self.bw) * 1e6:
                if tr < ephem.now():
                    tr = ephem.now()

                y = ((tr - ephem.now()) * 24.0 * 60.0) * self.scale_y + self.orig_y
                h = min(((ts - tr) * 24.0 * 60.0) * self.scale_y, 25 * 60 * self.scale_y - y)
                
                # Calculate the width from the mode - one day!
                w = 16
                x = (satellite.freq - (self.fx0 * 1e6)) * self.scale_x + self.orig_x - w/2

                satellite.passListPlan[passes].setRect(x, max(y, self.orig_y), w, h)
                satellite.passListPlan[passes].setParams((tr, azr, tt, altt, ts, azs))

                if satellite.passListPlan[passes].scene() == None:
                    self.scene().addItem(satellite.passListPlan[passes])
                satellite.passListPlan[passes].show()

            else:
                satellite.passListPlan[passes].hide()
        for passes in xrange(len(satellite.passListPlan) - len(satellite.passList)):
            #print 'hiding'
            satellite.passListPlan[passes+len(satellite.passList)].hide()

        nw = datetime.datetime.now()
        for x in xrange(len(self.time_labels)):
            self.time_labels[str(x)].setToolTip(nw.strftime('%H:%M:%S'))
            nw += datetime.timedelta(hours=1)


        for x in xrange(len(self.rx)):
            self.rx[x].update(self.fx0, self.scale_x, self.scale_y, self.orig_x, self.orig_y)
            
    def mousePressEvent(self, evt):
        pos = evt.pos()
        self.rx.append(PlannerReceiver(scene=self.scene(), bw = self.default_rx_bw))
        self.rx[-1].setRect(pos.x() - (self.default_rx_bw * self.scale_x / 2.0),
                            pos.y() + self.verticalScrollBar().value(),
                            self.default_rx_bw * self.scale_x,                   1)
        self.rx[-1].show()
        
    def mouseReleaseEvent(self, evt):
        rect = self.rx[-1].rect()
        pos = evt.pos()
        self.rx[-1].setRect(rect.x(), rect.y(), rect.width(), pos.y()-rect.y()+ self.verticalScrollBar().value())
        rect = self.rx[-1].rect()

        print 'Start time', str(ephem.date(ephem.now() + ((rect.y() - self.orig_y) / self.scale_y) * ephem.minute))
        print 'Duration', rect.height() / self.scale_y
        print 'Centre Frequency', (rect.x() + rect.width()/2 - self.orig_x) / self.scale_x + (self.fx0 * 1e6)

        self.rx[-1].setParams(ephem.date(ephem.now() + ((rect.y() - self.orig_y) / self.scale_y) * ephem.minute),
                              rect.height() / self.scale_y,
                              (rect.x() + rect.width()/2 - self.orig_x) / self.scale_x + (self.fx0 * 1e6))
        
        for f in self.scene().items(rect):
            print f
            if isinstance(f, PlannerSat):
                print f.name, f.mode, f.freq, f.params
                self.rx[-1].addChannel(f.name, f.mode, f.freq, f.params)
        
    def mouseMoveEvent(self, evt):
        rect = self.rx[-1].rect()
        pos = evt.pos()
        self.rx[-1].setRect(rect.x(), rect.y(), rect.width(), pos.y()-rect.y()+ self.verticalScrollBar().value())
