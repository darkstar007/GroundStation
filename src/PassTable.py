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

class PassTable(QtGui.QTableWidget):
    def __init__(self, parent = None):
        QtGui.QTableWidget.__init__(self, parent)
        self.colLabels = ['Name', 'AOS', 'Max Elev', 'In....', 'G Track', 'Action']
        self.colLabelsVal = {}
        for x in xrange(len(self.colLabels)):
            self.colLabelsVal[self.colLabels[x]] = x
        self.setRowCount(1)
        self.setColumnCount(len(self.colLabels))
        self.setHorizontalHeaderLabels(self.colLabels)
        self.removeRow(0)
        self.sortItems(self.colLabelsVal['AOS'])
        
    def update(self, satellite):
        try:
            self.setSortingEnabled(False)
            row_start = 0
            
            for passes in xrange(len(satellite.passList)):
                tr, azr, tt, altt, ts, azs, lat, lon, alt = satellite.passList[passes]
                found = False
                if math.degrees(altt) > 15.0 and (tr - ephem.now()) < 1.0 and tr > ephem.now():
                    for row in xrange(row_start, self.rowCount()):
                        wgt = self.item(row, self.colLabelsVal['Name'])
                        if wgt is not None and wgt.text() == satellite.sat.name and not found:
                            found = True
                            row_start = row + 1
                            self.item(row, self.colLabelsVal['AOS']).setText((tr.datetime()+
                                                                              satellite.parent.dtime).strftime('%m/%d %H:%M:%S'))
                            self.item(row, self.colLabelsVal['Max Elev']).setText(format(math.degrees(altt),'.1f'))
                            self.item(row, self.colLabelsVal['In....']).setText(format((tr-ephem.now())*24.0*60.0,'.1f'))
                            if satellite.doGroundTrack:
                                self.item(row, self.colLabelsVal['G Track']).setCheckState(QtCore.Qt.Checked)
                            else:
                                self.item(row, self.colLabelsVal['G Track']).setCheckState(QtCore.Qt.Unchecked)
                            found_e, idx = satellite.inEvent(tt)
                            if found_e:
                                self.item(row, self.colLabelsVal['Action']).setCheckState(QtCore.Qt.Checked)
                            else:
                                self.item(row, self.colLabelsVal['Action']).setCheckState(QtCore.Qt.Unchecked)
                                

                    if not found:
                        row = self.rowCount()
                        row_start = row + 1
                        self.insertRow(row)
                        self.setItem(row, self.colLabelsVal['Name'], QtGui.QTableWidgetItem(satellite.sat.name))

                        self.setItem(row, self.colLabelsVal['AOS'],
                                     QtGui.QTableWidgetItem((tr.datetime()+satellite.parent.dtime).strftime('%m/%d %H:%M:%S')))

                        self.setItem(row, self.colLabelsVal['Max Elev'], QtGui.QTableWidgetItem(format(math.degrees(altt),'.1f')))
                        self.item(row, self.colLabelsVal['Max Elev']).setTextAlignment(QtCore.Qt.AlignRight+ QtCore.Qt.AlignVCenter)

                        self.setItem(row, self.colLabelsVal['In....'], QtGui.QTableWidgetItem(format((tr-ephem.now())*24.0*60.0,'.1f')))
                        self.item(row, self.colLabelsVal['In....']).setTextAlignment(QtCore.Qt.AlignRight+ QtCore.Qt.AlignVCenter)

                        ck = QtGui.QTableWidgetItem()
                        if satellite.doGroundTrack:
                            ck.setCheckState(QtCore.Qt.Checked)
                        else:
                            ck.setCheckState(QtCore.Qt.Unchecked)
                        self.setItem(row, self.colLabelsVal['G Track'], ck)
                        self.item(row, self.colLabelsVal['G Track']).setTextAlignment(QtCore.Qt.AlignRight+ QtCore.Qt.AlignVCenter)
                        
                        found_e, idx = satellite.inEvent(tt)
                        ck2 = QtGui.QTableWidgetItem()
                        if found_e:
                            ck2.setCheckState(QtCore.Qt.Checked)
                        else:
                            ck2.setCheckState(QtCore.Qt.Unchecked)
                        self.setItem(row, self.colLabelsVal['Action'], ck2)
                        self.item(row, self.colLabelsVal['Action']).setTextAlignment(QtCore.Qt.AlignRight+ QtCore.Qt.AlignVCenter)


            satellite.parent.observer.date = ephem.now()
            self.setSortingEnabled(True)
        except ValueError, e:
            pass
        except AttributeError, e:
            if tr == None:
                print 'Hmmmm', tr, azr, tt, altt, ts, azs, self.sat
            else:
                print 'This should not happen', e
