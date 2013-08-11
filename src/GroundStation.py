#!/usr/bin/env python

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
# along with GroundStation; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import math

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtOpenGL
import numpy as np
import math
import ephem
import datetime
import Image
import time
from Database import Database
from PolarPlot import PolarPlot
from PassTable import PassTable
from Satellite import Satellite
from Planner import Planner

import urllib2

class GraphicsSatMarker(QtGui.QGraphicsRectItem):
    def __init__(self, x, y, w, h, name):
        QtGui.QGraphicsRectItem.__init__(self, x, y, w, h)
        self.name = name
        self.label = QtGui.QGraphicsSimpleTextItem(self.name, parent=self)

    def setBrush(self, brush):
        QtGui.QGraphicsRectItem.setBrush(self, brush)
        self.label.setBrush(brush)

    def setFont(self, font):
        self.font
        self.label.setFont(font)
        fm = QtGui.QFontMetrics(self.font)
        self.lab_size = (fm.width(self.name), fm.height())

    def moveTo(self, x, y):
        rct = self.rect()
        self.setRect(x-rct.width()/2,y-rct.height()/2, rct.width(), rct.height())
        self.label.setPos(x - self.lab_size[0]/2, y + self.lab_size[1]/2)    
    
                
class OrbitWidget(QtGui.QGraphicsScene):
    '''
    Widget for drawing orbits.
    '''

    def __init__(self, parent, passTable, polarPlot, planner):
        QtGui.QGraphicsScene.__init__(self, parent)
        #self.setMinimumSize(500, 500)
        self.satdb = Database()
        fnames = self.satdb.getSatGroups()
        print 'fnames',fnames
        self.loadEphem(fnames)
        self.lastPos = None
        self.passTable = passTable

        self.passTable.cellClicked.connect(self.passTableCellClicked)
        self.passTable.cellDoubleClicked.connect(self.passTableCellDoubleClicked)

        self.polarPlot = polarPlot
        self.dtime = datetime.datetime.now()-ephem.now().datetime()
        self.planner = planner
        
    def passTableCellClicked(self, r, c):
        print 'wwww', r, c
        self.passTable.selectRow(r)
        if c == 4 or c == 5:
            nm_item = self.passTable.item(r, 0)
            print nm_item.text()
            for marker in self.marker:
                if marker.sat.name == nm_item.text():
                    if c == 4:
                        marker.toggleDoGroundTrack()
                    if c == 5:
                        marker.addEvent(str(self.passTable.item(r, 1).text()))

            
                
    def passTableCellDoubleClicked(self, r, c):
        print 'ggg', r, c
        self.passTable.selectRow(r)
        nm_item = self.passTable.item(r, 0)
        print nm_item.text()
        for marker in self.marker:
            if marker.sat.name == nm_item.text():
                tdy = datetime.date.today()
                marker.plotNextPass(str(tdy.year)+'/'+str(self.passTable.item(r,1).text()))
                
    def loadEphem(self, fnames):
        lines = []
        # We now load up the ephemeris data 
        for fname in fnames:
            print 'Opening ', fname
            self.satdb.loadEphem(fname)
            lines += self.satdb.getEphem(fname)
        numsats = len(lines)
        
        self.eph = []

        self.background = QtGui.QPixmap("Earth.jpg")
        self.addPixmap(self.background)
        self.lab = []
        self.lab_size = []
        self.marker = []
        self.label_font = QtGui.QFont()
        self.label_font.setBold(True)
        self.label_font.setPixelSize(15)
        fm = QtGui.QFontMetrics(self.label_font)
        pen = QtGui.QPen()
        pen.setWidth(1)
        pen.setBrush(QtCore.Qt.red)
        brush = QtGui.QBrush(QtCore.Qt.red)

        names = []
        count = 0
        for s in xrange(numsats):
            if lines[s][0] not in names:
                try:
                    names.append(lines[s][0])
                    nm = self.satdb.getCName(lines[s][0])
                    m = ephem.readtle(nm, str(lines[s][1]), str(lines[s][2]))
                    self.eph.append(m)
                    #self.satdb.setEphemEpochTime(lines[s][0], m._epoch)
                    self.marker.append(Satellite(0.0, 0.0, 10, 10, m, s, pen, brush, self.label_font, self.satdb, self))
                    self.marker[count].setBackgroundSize(self.background.width(), self.background.height())
                    self.addItem(self.marker[count])
                    count += 1
                except ValueError, e:
                    print e
                    print 's = ', s
                    print lines[s*3]
                    print lines[s*3+1]
                    print lines[s*3+2]

        self.marker = sorted(self.marker, key = lambda name: name.sat.name)
        self.satdb.setSatGroups(fnames)
        
    def passCBack(self, name):
        print "you clicked ",name
        self.pPopupButton.setText(name)
        sat = None
        for s in self.eph:
            if s.name == name:
                sat = s
        
        if sat is not None:
            obs = ephem.Observer()
            obs.long = self.observer.long
            obs.lat = self.observer.lat
            for p in range(3):
                tr, azr, tt, altt, ts, azs = obs.next_pass(sat)
                print """Date/Time (UTC)       Alt/Azim     Lat/Long      Range    Doppler"""
                print """=================================================================="""
                while tr < ts:
                    obs.date = tr
                    sat.compute(obs)
                    print "%s | %4.1f %5.1f | %4.1f %+6.1f | %5.1f | %+6.1f" % \
                          (tr,
                           math.degrees(sat.alt),
                           math.degrees(sat.az),
                           math.degrees(sat.sublat),
                           math.degrees(sat.sublong),
                           sat.range/1000.,
                           sat.range_velocity * 435e6 / 3.0e8)
                    tr = ephem.Date(tr + 20.0 * ephem.second)
                print
                obs.date = tr + ephem.minute

    def setPassPanel(self):
        self.pPanel = QtGui.QGridLayout()
        self.pPanel.setObjectName("pPanel")
        self.pPopupButton = QtGui.QPushButton("Pop&up Button")
        self.menu = QtGui.QMenu(self)
        self.acts = []
        for sat in self.eph:
            self.acts.append(SatAction(self, sat.name, self.passCBack))
        self.pPopupButton.setMenu(self.menu)
        self.pPanel.addWidget(self.pPopupButton, 0, 0)
        
    def setObsPosition(self, lat, lon, alt):
        # For the plotting we (i.e. I) ignore the altitude - I'll fix this one day
        self.obsx = 1.0 * math.cos(lat*math.pi/180.0)*math.cos(lon*math.pi/180.0)
        self.obsy = 1.0 * math.cos(lat*math.pi/180.0)*math.sin(lon*math.pi/180.0)
        self.obsz = 1.0 * math.sin(lat*math.pi/180.0)
        self.observer = ephem.Observer()
        self.observer.long = str(lon)
        self.observer.lat = str(lat)
        self.observer.elevation = alt

    def moonAndSun(self, now):
        # Calc the position of the sun & the moon if you couldn't guess!
        self.moon = ephem.Moon(now)
        r = self.moon.earth_distance*ephem.meters_per_au / ephem.earth_radius
        self.moon_pos_x = r * math.cos(self.moon.a_dec) * math.cos(self.moon.a_ra)
        self.moon_pos_y = r * math.cos(self.moon.a_dec) * math.sin(self.moon.a_ra)
        self.moon_pos_z = r * math.sin(self.moon.a_dec)
        self.moon_radius = r * math.atan(self.moon.radius)
        
        self.sun = ephem.Sun(now)
        r = self.sun.earth_distance*ephem.meters_per_au / ephem.earth_radius
        self.sun_pos_x = r * math.cos(self.sun.a_dec) * math.cos(self.sun.a_ra)
        self.sun_pos_y = r * math.cos(self.sun.a_dec) * math.sin(self.sun.a_ra)
        self.sun_pos_z = r * math.sin(self.sun.a_dec)
        self.sun_radius = r * math.atan(self.sun.radius)
        
    def setTime(self, now):
        # calculate the sat positions for 'now'
        self.observer.date = now
        for s in xrange(len(self.marker)):
            self.marker[s].recompute(self.observer)

        self.passTable.resizeColumnsToContents()

        #self.moonAndSun(now)


        #deltaT = now.datetime() - datetime.datetime(2000,1,1,12,00)
        #D = deltaT.days + (deltaT.seconds + (deltaT.microseconds/1.0e6)) / (24.0 * 3600.0)
        #GMST = 18.697374558 + 24.06570982441908 * D
        #self.GMST = (GMST % 24) * 360.0 / 24.0
        #self.updateGL()

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.zoom *= 0.9
        else:
            self.zoom *= 1.1
        #self.updateGL()
    
##    def mousePressEvent(self, event):
##        self.lastPos = event.pos()

##    def mouseMoveEvent(self, event):
##        if self.lastPos != None:
##            dx = event.pos().x() - self.lastPos.x()
##            dy = event.pos().y() - self.lastPos.y()
            
##            if event.buttons() & QtCore.Qt.LeftButton:
##                self.setXRotation(self.xRot + 8 * dy)
##                self.setYRotation(self.yRot + 8 * dx)
##            elif event.buttons() & QtCore.Qt.RightButton:
##                self.setXRotation(self.xRot + 8 * dy)
##                self.setZRotation(self.zRot + 8 * dx)

##        self.lastPos = event.pos()


class OrbitWidgetApp(QtGui.QMainWindow):
    ''' Qt Application that uses the'''
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        centralWidget = QtGui.QWidget()
        centralWidget.setObjectName("centralWidget")
        self.setCentralWidget(centralWidget)
        self.setObjectName("OrbitWidgetApp")
        
        cPanel = QtGui.QGridLayout()
        cPanel.setObjectName("cPanel")
        cPanel.addWidget(QtGui.QLabel("Date/time", self), 0, 0)

        self.nowWidget = QtGui.QLabel(self)
        cPanel.addWidget(self.nowWidget, 0, 1)

        cPanel.addWidget(QtGui.QLabel("Position of interest", self),7,0)

        cPanel.addWidget(QtGui.QLabel("Lat:", self),8,0)
        self.latWidget = QtGui.QLineEdit(self)
        self.latWidget.setText("52.44332")
        self.latWidget.editingFinished.connect(self.poiChanged)
        cPanel.addWidget(self.latWidget,8,1)
        
        cPanel.addWidget(QtGui.QLabel("Lon:", self),9,0)
        self.lonWidget = QtGui.QLineEdit(self)
        self.lonWidget.setText("-0.10982")
        self.lonWidget.editingFinished.connect(self.poiChanged)
        cPanel.addWidget(self.lonWidget,9,1)

        cPanel.addWidget(QtGui.QLabel("Alt:", self),10,0)
        self.altWidget = QtGui.QLineEdit(self)
        self.altWidget.setText("0.0")
        self.altWidget.editingFinished.connect(self.poiChanged)
        cPanel.addWidget(self.altWidget,10,1)

        # Give all the stretchyness to the last row
        cPanel.setRowStretch(11,1)

        self.tab = QtGui.QTabWidget()

        tab1 = QtGui.QWidget()
        tab1.setLayout(cPanel)
        self.tab.addTab(tab1, "Controls")

        self.setSatPanel()
        tab2 = QtGui.QWidget()
        tab2.setLayout(self.sPanel)
        self.tab.addTab(tab2, "Sat Groups")

        self.createPassPanel()

        self.polarPlot = PolarPlot()
        self.planner = Planner()
        self.orbitWidget = OrbitWidget(self, self.passTable, self.polarPlot, self.planner)
        
        self.setWotSatsPanel()
        tab2a = QtGui.QWidget()
        tab2a.setLayout(self.dsPanel)
        self.tab.addTab(tab2a, "Sats")

        tab3 = QtGui.QWidget()
        tab3.setLayout(self.passPanel)
        self.tab.addTab(tab3, "Passes")

        tab4 = QtGui.QWidget()
        playout = QtGui.QHBoxLayout()
        playout.addWidget(self.planner)
        tab4.setLayout(playout)
        self.tab.addTab(tab4, "Planner")

        tab5 = QtGui.QWidget()
        skybox = QtGui.QHBoxLayout()
        skybox.addWidget(self.polarPlot)
        tab5.setLayout(skybox)
        self.tab.addTab(tab5, "Sky")
        

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.setObjectName("mainLayout")
        self.view = QtGui.QGraphicsView()
        #self.view.setViewport(QtOpenGL.QGLWidget())
        self.view.setScene(self.orbitWidget)
        
        mainLayout.addWidget(self.view)
        mainLayout.addWidget(self.tab)
        # Give the orbit widget all the stretchyness
        mainLayout.setStretchFactor(self.view, 1)
        #mainLayout.setGeometry(QtCore.QRect(0,0,1200,400))
        
        centralWidget.setLayout(mainLayout)
        centralWidget.setMinimumSize(1400,600)
        self.now = ephem.now()
        self.setMinimumSize(1600,900)
        
        # The interval is in milliseconds and is how often to update the display
        self.timerInterval = 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advanceTime)
        self.timer.start(self.timerInterval)
        self.poiChanged()
        self.advanceTime()
        
    def createPassPanel(self):
        self.passPanel = QtGui.QHBoxLayout()
        self.passPanel.setObjectName('passPanel')

        self.passTable = PassTable()
        
        self.passPanel.addWidget(self.passTable)
        
    def setWotSatsPanel(self):
        try:
            while self.dsPanel.count():
                child = self.dsPanel.takeAt(0)
                child.widget().deleteLater()

        except Exception,e:
            print 'Not made it yet', e
            self.dsPanel = QtGui.QGridLayout()
            self.dsPanel.setObjectName("dsPanel")
        
        count = 0
        row = 0
        for f in range(len(self.orbitWidget.marker)):
            self.dsPanel.addWidget(self.orbitWidget.marker[f].checkBox, row, (count % 2))
            if (count % 2) == 1:
                row += 1
            count += 1

        self.dsPanel.setRowStretch(row+1, 2)

    def setSatPanel(self):
        self.sPanel = QtGui.QGridLayout()
        self.sPanel.setObjectName("sPanel")
        self.satdb = Database()
        fnames = self.satdb.getSatGroups()

        self.HTTPfiles = [ ("weather.txt", "Weather"),
                           ("noaa.txt", "NOAA"),
                           ("geos.txt", "GOES"),
                           ("resource.txt", "Earth Resource"),
                           ("sarsat.txt", "S && R"),
                           ("dmc.txt", "Disaster Monitoring"),
                           ("tdrss.txt", "TDRSS"),
                           ("geo.txt", "Geostationary"),
                           ("intelsat.txt", "Intelsat"),
                           ("gorizont.txt", "Gorizont"),
                           ("raduga.txt", "Raduga"),
                           ("iridium.txt", "Iridium"),
                           ("molniya.txt", "Molniya"),
                           ("orbcomm.txt", "Orbcomm"),
                           ("globalstar.txt", "Globalstar"),
                           ("x-comm.txt", "Experimental"),
                           ("other-comm.txt", "Other"),
                           ("amateur.txt", "Amateur"),
                           ("gps-ops.txt", "GPS"),
                           ("glo-ops.txt", "Glonass"),
                           ("galileo.txt", "Galileo"),
                           ("sbas.txt", "SBAS"),
                           ("nnss.txt", "NNSS"),
                           ("musson.txt", "Musson"),
                           ("science.txt", "Science"),
                           ("geodetic.txt", "Geodetric"),
                           ("engineering.txt", "Engineering"),
                           ("education.txt", "Educational"),
                           ("military.txt", "Military"),
                           ("radar.txt", "Radar"),
                           ("cubesat.txt", "Cubesat"),
                           ("other.txt", "Other")]
        count = 0
        row = 0
        for f in range(len(self.HTTPfiles)):
            cb = QtGui.QCheckBox(self.HTTPfiles[f][1])
            if self.HTTPfiles[f][0] in fnames:
                cb.setChecked(True)
            self.sPanel.addWidget(cb, row, (count % 2))
            self.HTTPfiles[f] += (cb, )
            if (count % 2) == 1:
                row += 1
            count += 1
        apply = QtGui.QPushButton("Apply")
        self.sPanel.addWidget(apply, row+1, 0, 1, 2)
        apply.clicked.connect(self.changeSatellites)
        self.sPanel.setRowStretch(row+2, 2)

    def changeSatellites(self):
        fnames = ()
        for f in self.HTTPfiles:
            if f[2].isChecked():
                fnames+=( f[0], )
        self.orbitWidget.loadEphem(fnames)
        self.setWotSatsPanel()

    # will alter these to take other forms of lat/longs - one day...
    def parseLat(self, value):
        return float(value)

    def parseLon(self, value):
        return float(value)
    
    def parseAlt(self, value):
        return float(value)
    
    def poiChanged(self):
        lat = self.latWidget.text()
        lon = self.lonWidget.text()
        alt = self.altWidget.text()

        if lat != "" and lon != "" and alt != "":
            try:
                plat = self.parseLat(lat)
                plon = self.parseLon(lon)
                palt = self.parseAlt(alt)
                self.orbitWidget.setObsPosition(plat, plon, palt)
            except ValueError:
                print "oh dear"
        
    def advanceTime(self):
        self.now = ephem.Date(ephem.now())
        self.timer.setInterval(800)

        self.orbitWidget.setTime(self.now)
        self.nowWidget.setText(datetime.datetime.now().strftime("%x %X"))
        

if __name__ == '__main__':
    app = QtGui.QApplication(['GroundStation Version 0.1'])
    window = OrbitWidgetApp()
    window.show()
    app.exec_()
