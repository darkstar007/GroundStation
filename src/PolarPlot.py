#
# Copyright 2012,2013 Matthew Nottingham
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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtOpenGL
import numpy as np
import math

class PolarPlot(QtGui.QGraphicsView):
    def __init__(self, parent = None):
        QtGui.QGraphicsView.__init__(self, parent)
        self.setScene(QtGui.QGraphicsScene())
        self.elev_angles = [0, 30, 60]
        self.azi_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        self.elev = []
        for x in xrange(len(self.elev_angles)):
            self.elev.append(QtGui.QGraphicsEllipseItem())
            self.scene().addItem(self.elev[x])

        self.azi = []
        for x in xrange(len(self.azi_angles)):
            self.azi.append(QtGui.QGraphicsLineItem())
            self.scene().addItem(self.azi[x])

        self.labels = []
        self.label_info = [('N', 0), ('E', 90), ('S', 180), ('W', 270)]
        for x in xrange(len(self.label_info)):
            self.labels.append(QtGui.QGraphicsTextItem(self.label_info[x][0]))
            self.scene().addItem(self.labels[x])
        
        self.sats = {}
        self.gfx_radius = -1
        self.data = None
        
    def resizeEvent(self, evt):
        QtGui.QGraphicsView.resizeEvent(self, evt)

        self.centre_x = self.width() / 2
        self.centre_y = self.height() / 2
        self.gfx_radius = 0.85 * min(self.width(), self.height()) / 2

        for x in xrange(len(self.elev_angles)):
            fact = (90.0 - self.elev_angles[x]) / 90.0
            self.elev[x].setRect(self.centre_x - self.gfx_radius*fact,
                                 self.centre_y - self.gfx_radius*fact,
                                 self.gfx_radius*fact*2, self.gfx_radius*fact*2)
        for a in xrange(len(self.azi_angles)):
            self.azi[a].setLine(self.centre_x, self.centre_y,
                                self.gfx_radius * math.sin(math.radians(self.azi_angles[a])) + self.centre_x,
                                -self.gfx_radius * math.cos(math.radians(self.azi_angles[a])) + self.centre_y)

        for x in xrange(len(self.labels)):
            rect = self.labels[x].boundingRect()
            #print rect
            self.labels[x].setPos(  1.05 * self.gfx_radius * math.sin(math.radians(self.label_info[x][1])) + self.centre_x - rect.width()/2.0,
                                   -1.05 * self.gfx_radius * math.cos(math.radians(self.label_info[x][1])) + self.centre_y - rect.height()/2.0)

            
        self.plotSat()
        if self.data != None:
            self.plotTracks()
            self.plotLabels()
            
    def calcPos(self, elev, azi):
        x =  (1.0 - (elev / (math.pi / 2.0))) * self.gfx_radius * math.sin(azi) + self.centre_x
        y = -(1.0 - (elev / (math.pi / 2.0))) * self.gfx_radius * math.cos(azi) + self.centre_y

        return (x, y)
    
    def plotTracks(self):
        for st in xrange(len(self.data)-1):
            x1, y1 = self.calcPos(self.data[st][1], self.data[st][2])
            x2, y2 = self.calcPos(self.data[st+1][1], self.data[st+1][2])

            self.ln[st].setLine(x1, y1, x2, y2)
            
    def plotLabels(self):
        for st in xrange(len(self.dlabels)):
            x1, y1 = self.calcPos(self.dlabels[st][1], self.dlabels[st][2])

            self.label_obj[st].setPos(x1, y1)

    def plotSat(self):
        for s in self.sats:
            if self.sats[s]['elev'] >= 0.0 and self.gfx_radius > 0:
                x, y = self.calcPos(self.sats[s]['elev'], self.sats[s]['azi'])
            else:
                x = -999
                y = -999
            if x > 0 and y > 0:
                self.sats[s]['widget'].setPos(x, y)
                self.sats[s]['widget'].show()
            else:
                self.sats[s]['widget'].hide()
    
    def updateSat(self, sat):
        if sat.name not in self.sats.keys():
            self.sats[sat.name] = {}
            self.sats[sat.name]['widget'] = QtGui.QGraphicsTextItem(sat.name)
            self.scene().addItem(self.sats[sat.name]['widget'])
        self.sats[sat.name]['elev'] = sat.alt*1.0
        self.sats[sat.name]['azi'] = sat.az*1.0
        self.plotSat()
        
    def addPass(self, data, labels):
        self.data = data[:]
        self.dlabels = labels[:]
        self.ln = []
        self.label_obj = []
        pen = QtGui.QPen(QtGui.QColor(128, 0, 128))
        pen.setWidth(2)
        for st in xrange(len(self.data)-1):
            self.ln.append(QtGui.QGraphicsLineItem())
            self.ln[st].setPen(pen)
            self.scene().addItem(self.ln[st])
            
        for st in xrange(len(self.dlabels)):
            self.label_obj.append(QtGui.QGraphicsTextItem(self.dlabels[st][0]))
            self.scene().addItem(self.label_obj[st])
        
