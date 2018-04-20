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
import numpy as np
import datetime
import SatPass

from SatelliteEvent import SatelliteEvent
from Planner import PlannerSat

class Satellite(QtGui.QGraphicsRectItem):
    def __init__(self, x, y, w, h, sat, marker_id, pen, brush, font, db, parent):
        QtGui.QGraphicsRectItem.__init__(self, x, y, w, h)
        self.setBrush(brush)
        self.setPen(pen)
        self.font = font
        self.marker_id = marker_id
        self.sat = sat
        self.label = QtGui.QGraphicsSimpleTextItem(self.sat.name, parent=self)
        self.label.setFont(font)
        self.label.setBrush(brush)
        fm = QtGui.QFontMetrics(self.font)
        self.lab_size = (fm.width(self.sat.name), fm.height())
        self.doFootprint = True
        self.backgroundSize = None
        self.parent = parent
        self.db = db
        self.doDisplay, self.doGroundTrack = self.db.getSat(self.sat.name)
        self.freq = self.db.getFreq(self.sat.name)
        self.mode = self.db.getMode(self.sat.name)
        if len(self.freq) != len(self.mode):
            raise Exception("We didn't get a frequency for each mode (or vis versa)")

        self.tle = self.db.getTLE(self.sat.name)

        #self.doGroundTrack = True

        self.footprintPos = None
        self.footprintItem = None
        self.groundTrackPos = None
        self.groundTrackItems = None
        
        self.eventList = []
        self.passList = []
        self.passListPlan = []
        self.passListLastUpdate = datetime.datetime.now() - datetime.timedelta(days=2)
        self.evt = None
        
        # This is the checkbox entry in the long list of sats for this sat
        self.checkBox = QtGui.QCheckBox(self.sat.name)
        self.checkBox.setChecked(self.doDisplay)
        self.checkBox.clicked.connect(self.checkBoxStateChanged)
        
    def setBackgroundSize(self, x, y):
        self.backgroundSize = (x, y)

    def updatePassList(self, obs):
        print 'Updating pass list', self.sat.name
        self.passList = []
        try:
            while (obs.date - ephem.now()) < 2.0:
                tr, azr, tt, altt, ts, azs = obs.next_pass(self.sat)
                if ts is not None:
                    if tr > tt or tr > ts:    # If sat is visible in the sky, then we get weird number out!
                        original_ts = ts
                        print self.sat.name,'tr',tr,'tt',tt,'ts',ts,'original'
                        self.parent.observer.date = obs.date - 45.0 * ephem.minute # lets rewind time by half an orbit
                        tr, azr, tt, altt, ts, azs = obs.next_pass(self.sat)
                        print self.sat.name,'tr',tr,'tt',tt,'ts',ts,'fixed'
                        if ts < (original_ts - ephem.minute):   # I'm seeing the odd really weird output
                            raise Exception("bad prediction")
                    self.passList.append((tr, azr, tt, altt, ts, azs, obs.lat, obs.lon, obs.elev))
                    obs.date = ts + 10.0 * ephem.minute
                else:
                    obs.date = obs.date + 10.0
        except Exception, e:
            print e
            
        diff = len(self.passList * len(self.freq)) - len(self.passListPlan)
        if diff > 0:
            for x in range(diff):
                self.passListPlan.append(PlannerSat(1,1,1,1,self))
                self.passListPlan[-1].hide()
                
        self.passListLastUpdate = datetime.datetime.now()
        obs.date = ephem.now()
        
    def recompute(self, obs):
        if self.doDisplay:
            if (datetime.datetime.now() - self.passListLastUpdate) > datetime.timedelta(seconds=120):
                self.updatePassList(obs)
                
            self.parent.passTable.update(self)
            for x in self.parent.planner.keys():
                self.parent.planner[x].update(self)
            
            self.sat.compute(obs)

            self.parent.polarPlot.updateSat(self.sat)

            found, idx = self.inEvent(obs.date)
            if found:
                print 'We should be doing something for', self.sat.name
                if self.evt == None:
                    self.evt = SatelliteEvent(obs, self.sat, self.freq, self.mode)
                else:
                    self.evt.update(self.sat)
            else:
                if self.evt is not None:
                    self.evt.finish()
                    self.evt = None
                
            if self.backgroundSize != None:
                x = ( self.sat.sublong + math.pi) * self.backgroundSize[0] / (2.0  *math.pi)
                y = (-self.sat.sublat + math.pi/2) * self.backgroundSize[1] / math.pi

                self.moveTo(x,y)
                self.show()
                
                if self.doFootprint:
                    self.computeFootprint()
                    self.drawFootprint()
                if self.doGroundTrack:
                    self.computeGroundTrack()
                    self.drawGroundTrack()
            else:
                print "No background size set!"
    
        else:
            self.hide()

    def computeFootprint(self):
        r0 = ephem.earth_radius
        alt = self.sat.elevation + r0

        vert = np.zeros(((360/5),3), np.float)
        r1vert = np.zeros(((360/5),3), np.float)
        r2vert = np.zeros((3,), np.float)

        x0 = r0 * r0 / alt
        phi = math.acos(x0 / r0)
        y0 = r0 * math.sin(phi)

        if (self.sat.sublat + phi) > math.pi/2 or (self.sat.sublat - phi) < -math.pi/2:
            #print self.sat, self.sat.sublat, self.sat.sublong, math.degrees(phi)
            self.footprintHighLat = True
        else:
            self.footprintHighLat = False

        #if (self.sat.sublong + phi) > math.pi or (self.sat.sublong - phi) < -math.pi:            
        #    self.footprintSplit = True
        #    print 'Spliting ',self.sat
        #else:
        #    self.footprintSplit = False

        for i in xrange(vert.shape[0]):
            vert[i,0] = x0
            vert[i,1] = y0 * math.sin(math.radians(i * 5))
            vert[i,2] = y0 * math.cos(math.radians(i * 5))
            
        # rotate about y axis by sat.sublat
        c = math.cos(self.sat.sublat)
        s = math.sin(self.sat.sublat)
        max_x = -9999999
        min_x = 9999999
        for i in xrange(vert.shape[0]):
            r1vert[i,0] = c * vert[i,0] + s * vert[i,2]
            r1vert[i,1] = vert[i, 1]
            r1vert[i,2] = -s * vert[i,0] + c * vert[i,2]

        midp=[c*x0, 0, -s*x0]
        
        # rotate about z axis by  sat.sublon
        if type(self.footprintPos) != np.ndarray and self.footprintPos == None:
            self.footprintPos = np.zeros((vert.shape[0], 2), np.float)
            
        c = math.cos(self.sat.sublong)
        s = math.sin(self.sat.sublong)
        midpt=[c * midp[0] - s * midp[1], s * midp[0] + c * midp[1], midp[2]]

        for i in xrange(vert.shape[0]):
            r2vert[0] = c * r1vert[i,0] - s * r1vert[i,1]
            r2vert[1] = s * r1vert[i,0] + c * r1vert[i,1]
            r2vert[2] = r1vert[i,2]

            phi = math.asin(r2vert[2] / r0)
            theta = math.atan2(r2vert[1], r2vert[0])
            self.footprintPos[i,0] = ( theta + math.pi) * self.backgroundSize[0] / (2.0  *math.pi)
            self.footprintPos[i,1] = ( phi + math.pi/2) * self.backgroundSize[1] / math.pi
            if  self.footprintPos[i,0] > max_x:
                max_x = self.footprintPos[i,0]
            if self.footprintPos[i,0] < min_x:
                min_x = self.footprintPos[i,0]

        phi = math.asin(midpt[2] / r0)
        theta = math.atan2(midpt[1], midpt[0])
        midptpix = [( theta + math.pi) * self.backgroundSize[0] / (2.0  *math.pi),
                    ( phi + math.pi/2) * self.backgroundSize[1] / math.pi]
        self.footprintSplit = False
        if math.fabs((min_x+max_x)/2 - midptpix[0]) > 10:
            #print 'Splitting',self.sat,midptpix, 'Min', min_x, 'Max', max_x
            self.footprintSplit = True

        
    def mousePressEvent(self, event):
        print self.marker_id," got clicked ",self.sat.name
        self.dia = SatPass.SatPassDialog()
        self.dia.setInfo(self.parent.observer.long, self.parent.observer.lat, self.sat)
        
    def moveTo(self, x, y):
        rct = self.rect()
        self.setRect(x-rct.width()/2,y-rct.height()/2, rct.width(), rct.height())
        self.label.setPos(x - self.lab_size[0]/2, y + self.lab_size[1]/2)

    def computeGroundTrack(self):
        #sat = ephem.EarthSatellite(self.sat)

        n = ephem.Date(ephem.now() - ephem.minute * 10)
        if type(self.groundTrackPos) != np.ndarray and self.groundTrackPos == None:
            self.groundTrackPos = np.zeros((250,2), np.float)
        
        for t in xrange(self.groundTrackPos.shape[0]):
            self.sat.compute(n)
            self.groundTrackPos[t,0] = ( self.sat.sublong + math.pi) * self.backgroundSize[0] / (2.0  *math.pi)
            self.groundTrackPos[t,1] = (-self.sat.sublat + math.pi/2) * self.backgroundSize[1] / math.pi
            n = ephem.Date(n + ephem.minute)
        
    def drawGroundTrack(self):
        if self.groundTrackItems == None:
            pen = QtGui.QPen(QtGui.QColor(240, 240, 10, 200))
            self.groundTrackItems = []
            for t in xrange(self.groundTrackPos.shape[0] - 1):
                self.groundTrackItems.append(QtGui.QGraphicsLineItem(parent=self))
                self.groundTrackItems[t].setPen(pen)
        

        for t in xrange(self.groundTrackPos.shape[0] - 1):
            if math.fabs(self.groundTrackPos[t,0] - self.groundTrackPos[t+1,0]) < 100:
                self.groundTrackItems[t].setLine(self.groundTrackPos[t,0], self.groundTrackPos[t,1],
                                                 self.groundTrackPos[t+1,0] ,self.groundTrackPos[t+1,1])
                self.groundTrackItems[t].show()
            else:
                self.groundTrackItems[t].hide()

    def drawFootprint(self):
        if self.footprintItem == None:
            pen = QtGui.QPen(QtGui.QColor(240, 240, 10, 200))
            brush = QtGui.QBrush()
            brush.setColor(QtGui.QColor(240, 240, 10, 100))
            brush.setStyle(QtCore.Qt.SolidPattern)
            self.footprintItem = []
            self.footprintItem.append(QtGui.QGraphicsPolygonItem(parent=self))
            self.footprintItem.append(QtGui.QGraphicsPolygonItem(parent=self))

            self.footprintItem[0].setPen(pen)
            self.footprintItem[0].setBrush(brush)

            brush.setColor(QtGui.QColor(240, 20, 230, 100))
            self.footprintItem[1].setPen(pen)
            self.footprintItem[1].setBrush(brush)

        if self.footprintHighLat:
            poly1 = QtGui.QPolygonF()
            poly2 = QtGui.QPolygonF()
            
            min_pos = {'value':9999999, 'pos':-1}
            max_pos = {'value':-9999999, 'pos':-1}

            for i in xrange(self.footprintPos.shape[0]):
                if self.footprintPos[i,0] < min_pos['value']:
                    min_pos['value'] = self.footprintPos[i,0]
                    min_pos['pos'] = i
                    
                if self.footprintPos[i,0] > max_pos['value']:
                    max_pos['value'] = self.footprintPos[i,0]
                    max_pos['pos'] = i

            for i in xrange(self.footprintPos.shape[0]):
                if i == min_pos['pos'] and self.footprintPos[0,1] < self.backgroundSize[1]/2:
                    poly1.append(QtCore.QPointF(0.0, 0.0))
                if i == max_pos['pos'] and  self.footprintPos[0,1] > self.backgroundSize[1]/2:
                    poly1.append(QtCore.QPointF(self.backgroundSize[0], self.backgroundSize[1]))

                poly1.append(QtCore.QPointF(self.footprintPos[i,0], self.footprintPos[i,1]))

                if i == min_pos['pos'] and  self.footprintPos[0,1] > self.backgroundSize[1]/2:
                    poly1.append(QtCore.QPointF(0.0, self.backgroundSize[1]))
                if i == max_pos['pos'] and  self.footprintPos[0,1] < self.backgroundSize[1]/2:
                    poly1.append(QtCore.QPointF(self.backgroundSize[0], 0))

            self.footprintItem[0].setPolygon(poly1)
            self.footprintItem[1].hide()
                    
        else:
            if self.footprintSplit:
                poly1 = QtGui.QPolygonF()
                poly2 = QtGui.QPolygonF()
                for i in xrange(self.footprintPos.shape[0]):
                    if self.footprintPos[i,0] < self.backgroundSize[0]/2:
                        poly1.append(QtCore.QPointF(self.footprintPos[i,0], self.footprintPos[i,1]))
                    else:
                        poly2.append(QtCore.QPointF(self.footprintPos[i,0], self.footprintPos[i,1]))
                self.footprintItem[0].setPolygon(poly1)
                self.footprintItem[1].setPolygon(poly2)
                self.footprintItem[1].show()
            else:
                poly = QtGui.QPolygonF()
                for i in xrange(self.footprintPos.shape[0]):
                    poly.append(QtCore.QPointF(self.footprintPos[i,0], self.footprintPos[i,1]))

                self.footprintItem[0].setPolygon(poly)
                self.footprintItem[1].hide()
            
    def setDisplay(self, disp):
        self.doDisplay = disp
        self.checkBox.setChecked(self.doDisplay)
        self.db.setSat(self.sat.name, self.doDisplay, self.doGroundTrack)
        
    def checkBoxStateChanged(self):
        self.doDisplay = self.checkBox.isChecked()
        self.db.setSat(self.sat.name, self.doDisplay, self.doGroundTrack)

    def plotNextPass(self, date):
        self.passPlot = SatPass.SatPlotPassDialog()
        self.passPlot.setInfo(self.parent.observer.long, self.parent.observer.lat, self.sat, date)

    def toggleDoGroundTrack(self):
        self.doGroundTrack = not self.doGroundTrack
        if not self.doGroundTrack:
            for t in xrange(self.groundTrackPos.shape[0] - 1):
                self.groundTrackItems[t].hide()
                
            self.groundTrackItems = None
        self.db.setSat(self.sat.name, self.doDisplay, self.doGroundTrack)

    def findEvent(self, etime):
        found = False
        idx = None
        for x in xrange(len(self.eventList)):
            if math.abs(self.eventList[x][0] - etime) < (1.0 / (24.0 * 60.0)):
                found = True
                idx = x
        return (found, idx)

    def addEvent(self, etime_start, etime_finish = None):

        if etime_finish is not None:   # and etime_start is not String:
            found, idx = findEvent(etime_start)
        
            if found:
                self.eventList[idx] = (etime_start, etime_finish)
            else:
                self.eventList.append((etime_start, etime_finish))
        else:
            #if etime_finish is String:
            tdy = datetime.date.today()
            tmp = datetime.datetime.strptime(str(tdy.year)+'/'+etime_start, '%Y/%m/%d %H:%M:%S') - self.parent.dtime

            print tmp
            for x in xrange(len(self.passList)):
                if abs(tmp - self.passList[x][0].datetime()) < datetime.timedelta(seconds=60.0):
                    self.eventList.append((self.passList[x][0], self.passList[x][4]))
                
    def inEvent(self, etime):
        found = False
        idx = None
        for x in xrange(len(self.eventList)):
            if etime >= self.eventList[x][0] and etime <= self.eventList[x][1]:
                found = True
                idx = x
        return (found, idx)
        
