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
from PolarPlot import PolarPlot

class SatPassDialog(QtGui.QDialog):
    def __init__(self, parent=None, flags=0):
        QtGui.QDialog.__init__(self, parent = parent)

        self.setModal(False)

    def setInfo(self, lon, lat, sat, date = None):
        self.obs = ephem.Observer()
        self.obs.long = lon
        self.obs.lat = lat
        dtime = datetime.datetime.now() - ephem.now().datetime()
        if date is not None:
            tdy = datetime.date.today()
            self.obs.date = datetime.datetime.strptime(str(tdy.year)+'/'+etime_start, '%Y/%m/%d %H:%M:%S') - dtime - datetime.timedelta(mins=10.0)
        print 'SetInfo', self.obs.date
        self.sat = sat
        self.table = QtGui.QTableWidget(16, 6)
        self.table.setHorizontalHeaderLabels(['AOS', 'AOS Azi', 'Max El', 'Max El', 'LOS', 'LOS Azi'])
        self.setWindowTitle(sat.name)
        self.setLayout(QtGui.QGridLayout())
        self.table.cellDoubleClicked.connect(self.tableCellDoubleClicked)
        
        self.layout().addWidget(self.table)
        
        for p in xrange(self.table.rowCount()):
            #tr, azr, tt, altt, ts, azs = obs.next_pass(self.sat)
            res = self.obs.next_pass(self.sat)
            #print res
            for c in xrange(len(res)):
                if c % 2 == 1:
                    item = QtGui.QTableWidgetItem(format(math.degrees(res[c]), '.1f'))
                    item.setTextAlignment(QtCore.Qt.AlignRight+ QtCore.Qt.AlignVCenter)
                else:
                    item = QtGui.QTableWidgetItem((res[c].datetime()+dtime).strftime('%m/%d %H:%M:%S'))
                self.table.setItem(p, c, item)
            self.obs.date = res[4] + ephem.minute

        self.table.resizeColumnsToContents()
        self.table.show()
        print self.table.size()
        #self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding))
        self.resize(800,400)
        #self.adjustSize()
        self.show()

    def tableCellDoubleClicked(self, r, c):
        print 'TTT', r, c
        self.table.selectRow(r)
        nm_item = self.table.item(r, 0)
        yr = datetime.datetime.now().strftime('%Y')
        self.ppd = SatPlotPassDialog()
        self.ppd.setInfo(self.obs.lon, self.obs.lat, self.sat, yr+'/'+nm_item.text())

class SatAction():
    def __init__(self, parent, name, cback):
        self.cback = cback
        self.action = parent.menu.addAction(name, self.callback)
        self.name = name
        
    def callback(self):
        self.cback(self.name)

    
class SatPlotPassDialog(QtGui.QDialog):
    def __init__(self, parent=None, flags=0):
        QtGui.QDialog.__init__(self, parent = parent)

        self.setModal(False)

    def setInfo(self, lon, lat, sat, pstart = None):
        obs = ephem.Observer()
        obs.long = lon
        obs.lat = lat
        dtime = datetime.datetime.now() - ephem.now().datetime()
        if pstart != None:
            obs.date = str(pstart)
            obs.date -= ephem.minute  # Make sure we start before the AOS
            obs.date -= (dtime.days + (dtime.seconds + dtime.microseconds/1.0e6) * ephem.second)  # convert to GMT from local
            
        self.sat = sat
        self.plot = PolarPlot()
        self.setWindowTitle(sat.name)
        self.setLayout(QtGui.QGridLayout())
        
        self.layout().addWidget(self.plot)

        tr, azr, tt, altt, ts, azs = obs.next_pass(self.sat)
        data = []
        tr_time = tr.datetime()
        ltime = (datetime.datetime(tr_time.year, tr_time.month, tr_time.day, tr_time.hour, tr_time.minute, 0) +
                 datetime.timedelta(seconds=60))
        while tr < ts:
            obs.date = tr
            self.sat.compute(obs)
            print "%s | %4.1f %5.1f | %4.1f %+6.1f | %5.1f | %+6.1f" % \
                  (tr,
                   math.degrees(self.sat.alt),
                   math.degrees(self.sat.az),
                   math.degrees(self.sat.sublat),
                   math.degrees(self.sat.sublong),
                   self.sat.range/1000.,
                   self.sat.range_velocity * 435e6 / 3.0e8)
            data.append((tr, self.sat.alt*1.0, self.sat.az*1.0))
            tr = ephem.Date(tr + 20.0 * ephem.second)

        tr = ephem.Date(ltime)
        labels = []
        while tr < ts:
            obs.date = tr
            self.sat.compute(obs)
            dt = tr.datetime() + dtime
            labels.append(("%02d:%02d" % (dt.hour, dt.minute), self.sat.alt*1.0, self.sat.az*1.0))
            tr = ephem.Date(tr + 60.0 * ephem.second)
            
        self.plot.addPass(data, labels)
        self.resize(600,600)
        self.show()
