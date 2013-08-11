
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


import sqlite3
import datetime
import urllib2
import ephem
from UTC import UTC

class Database():
    def __init__(self):
        self.baseHTTP = "http://celestrak.com/NORAD/elements/"

        self.conn = sqlite3.connect('groundstation.db')
        self.curs = self.conn.cursor()

        try:
            self.conn.execute('CREATE TABLE modes (name text, mode int unique)')
            mode_data = [
                ('Other', -1),
                ('1k2_AFSK', 0),
                ('1k2_FSK', 1),
                ('CW', 2),
                ('4k8_GMSK', 3),
                ('9k6_GMSK', 4),
                ('9k6_FSK', 5),
                ('1k2_BPSK', 6),
                ('CW(FM)', 7),
                ('19k2_GFSK', 8),
                ('APRS', 9),
                ('0k625_GFSK', 10),
                ('APT', 11),
                ('WBFM', 12),
                ('9k6_MSK', 13),
                ]
            
            self.conn.executemany('INSERT INTO modes VALUES (?, ?)', mode_data)
            self.conn.execute('CREATE INDEX mode_idx ON modes(mode)')
            self.conn.commit()
        except Exception, e:
            print e
        
        try:
            self.conn.execute('CREATE TABLE sats (name text, cname text, id int, freq real, mode int)')
            sat_data = [
                ('OSCAR 7 (AO-7)', 'AO-7', 7530, 145.9775e6, -1),
                ('UOSAT 2 (UO-11)', 'UO-11', 14781, 145.826e6, 1),
                #('EYESAT-1 (AO-27)', 'AO-27', 22825, 436.795e6, -1),
                ('ITAMSAT (IO-26)', 'IO-26', 22826, 435.867e6, -1),
                #('RADIO ROSTO (RS-15)', 'RS-15', 23439, 29.3987e6),
                ('JAS-2 (FO-29)', 'FO-29', 24278, 435.8e6, 2),
                ('TECHSAT 1B (GO-32)', 'GO-32', 25397, 435.3250e6, 2),
                ('SEDSAT 1 (SO-33)', 'SO-33', 25509, 437.91e6, -1),
                ('ISS (ZARYA)', 'ISS', 25544, 145.825e6, 9),
                ('PCSAT (NO-44)', 'NO-44', 26931, 145.8270e6, 0),
                ('SAUDISAT 1C (SO-50)', 'SO-50', 27607, 436.795e6, -1),
                ('CUTE-1 (CO-55)', 'CO-55', 27844, 436.8375e6-1000.0, 2),
                ('CUBESAT XI-IV (CO-57)', 'XI-IV/CO-57', 27848, 436.8475e6, 0),
                ('MOZHAYETS 4 (RS-22)', 'RS-22', 27939, 435.3520e6, 2),
                ('HAMSAT (VO-52)', 'VO-52', 28650, 145.86000e6, 2),
                ('CUBESAT XI-V (CO-58)', 'XI-V/CO-58', 28895, 437.465e6, 0),
                ('CUTE-1.7+APD II (CO-65)', 'Cute-1.7/CO-65', 32785, 437.275e6, 0),
                ('DELFI-C3 (DO-64)', 'Delfi-C3', 32789, 145.8700e6-2e3, 6),
                ('YUBILEINY (RS-30)', 'RS-30', 32953, 435.215e6, 2),
                ('PRISM', 'PRISM', 33493, 437.25e6, 0),
                ('STARS', 'STARS', 33498, 437.3050e6, -1),
                ('KKS-1', 'KKS-1', 33499, 437.3850e6, -1),
                ('SWISSCUBE', 'SwissCube', 35932, 437.5050e6, 0),
                ('BEESAT', 'BEESAT', 35933, 436.0e6, 4),
                ('ITUPSAT1', 'ITUpSAT1', 35935, 437.325e6, 8),
                ('HOPE-1 (HO-68)', 'HO-68', 36122, 435.7900e6+600.0, 2),
                ('JUGNU', 'JUGNU', 37839, 437.275e6, 2),
                ('SRMSAT', 'SRMSAT', 37841, 437.4250e6, 2),
                #('RAX-2', 'RAX-2', 37853, 437.345e6),
                ('MASAT 1', 'MASAT', 38081, 437.345e6, 10),
                ('AUBIESAT-1 (AO-71)', 'AubieSat', 37854, 437.475e6+6e3, 2),
                ('M-CUBED & EXP-1 PRIME', 'MCubed', 38051, 437.485e6, 4),
                ('LUSAT (LO-19)', 'LO-19', 20442, 437.125e6, -1),
                ('NOAA 15 [B]', 'NOAA 15', 25338, 137.62e6, 11),
                ('NOAA 17 [-]', 'NOAA 17', 27453, 137.5e6, 11),
                ('NOAA 18 [B]', 'NOAA 18', 28654, 137.9125e6, 11),
                ('NOAA 19 [+]', 'NOAA 19', 33591, 137.1e6, 11),
                ('Classic FM', 'Classic FM', -1, 101.9e6, 12),
                ('Graves', 'Graves', -1, 143.050e6, -1),
                ('Aeneas', 'Aeneas', 38760, 437.6e6+6.5e3, 0),
                #('TechEdSat', 'TechEdSat', 38854, 437.465e6, -1),
                ('BeeSat-2', 'Beesat-2', 39136, 435.950e6, 3),
                #('CUBEBUG 1', 'CubeBUG', 39153, 437.432e6, 0),
                ('TurkSAT', 'TurkSAT', -1, 437.225e6, -1),
                ('NEE-01 PEGASUS', 'NEE-01', 39151, 910.0e6, -1),
                ('ESTCUBE 1', 'ESTCube-1', 39161, 437.251e6, 2),
                ('STRAND 1', 'STRaND-1', 39090, 437.568e6, 5),
                #('FITSAT-1 (NIWAKA)', 'FITSAT-1', 38853, 437.250e6, 2),
                #('SOMP', 'SOMP', 39134, 437.504, 2),
                ('PicoDragon', 'PicoDragon', -1, 437.365e6, 0),
                ('ArduSat-1', 'ArduSat-1', -1, 437.325e6, 13),
                ('ArduSat-X', 'ArduSat-X', -1, 437.345e6, 13),
                ('TechEdSat-3', 'TechEdSat-3', -1, 437.465e6, 0),
                ('ROMIT1', 'Romit1', -1, 437.505e6, 0),
            ]
            
            self.conn.executemany('INSERT INTO sats VALUES (?, ?, ?, ?, ?)', sat_data)
            self.conn.execute('CREATE INDEX name_idx ON sats(name)')
            self.conn.execute('CREATE INDEX cname_idx ON sats(cname)')
            self.conn.commit()
        except Exception, e:
            print e

        try:
            self.conn.execute('CREATE TABLE pers (name text, display integer, grtrack integer)')
            self.conn.commit()
            pers_data = [
                ('NOAA 18', 1, 0),
                ('NOAA 19', 1, 0),
                ('VO-52', 1, 0),
                ('FO-29', 1, 0),
                ('ITUpSAT1', 1, 0),
                ('ISS', 1, 1),
                ('NEE-01', 1, 0),
                ('ESTCube-1', 1, 0),
                ('SO-50', 1, 0),
                ('HO-68', 1, 0),
                ('CO-55', 1, 0),
                ('AubieSat', 1, 0),
                ('MASAT', 1, 0),
                ('Cute-1.7/CO-65', 1, 0),
                ('MCubed', 1, 0),
                ('Prism', 1, 0),
                ('Delfi-C3', 1, 0),
                ('Aeneas', 1, 0),
                ('STRaND-1', 1, 0),
            ]
            self.conn.executemany('INSERT INTO pers VALUES (?, ?, ?)', pers_data)
            self.conn.commit()
            
        except Exception, e2:
            print e2


        try:
            self.conn.execute('CREATE TABLE satgroups (name text)')
            self.conn.commit()
            self.conn.execute("INSERT INTO satgroups VALUES ('amateur.txt')")
            self.conn.execute("INSERT INTO satgroups VALUES ('noaa.txt')")
            self.conn.execute("INSERT INTO satgroups VALUES ('cubesat.txt')")
            self.conn.commit()
        except Exception, e3:
            print e3

        try:
            #self.conn.execute('DROP TABLE ephemeris')
            #self.conn.commit()
            self.conn.execute('CREATE TABLE ephemeris (fname text, line1 text, line2 text, line3 text, ts timestamp, epoch timestamp)')
            self.conn.execute('CREATE INDEX fname_idx ON ephemeris(fname)')
            self.conn.execute('CREATE INDEX line1_idx ON ephemeris(line1)')
            self.conn.execute('CREATE INDEX epoch_idx ON ephemeris(epoch)')
            self.conn.commit()
        except Exception, e4:
            print e4


    def getCName(self, name):
        self.curs.execute('SELECT cname FROM sats WHERE name=?', (name.strip(),))
        res = self.curs.fetchall()
        if len(res) == 0:
            return (str(name.strip()))
        else:
            return (str(res[0][0]))

    def getFreq(self, name):
        self.curs.execute('SELECT freq FROM sats WHERE cname=?', (name,))
        res = self.curs.fetchall()

        if len(res) == 0:
            return (101.9e6)
        else:
            return (res[0][0])
        
    def getMode(self, name):
        self.curs.execute('SELECT modes.name FROM sats,modes WHERE sats.cname=? AND sats.mode = modes.mode', (name,))
        res = self.curs.fetchall()
        if len(res) == 0:
            return ('SSB')
        else:
            return (res[0][0])

    def getTLE(self, name):
        self.curs.execute('SELECT line2, line3 FROM ephemeris,sats WHERE sats.cname=? and ephemeris.line1 = sats.name', (name,))
        res = self.curs.fetchall()
        if len(res) == 0:
            return (('', ''))
        else:
            return (res[0])

    def getSat(self, name):
        self.curs.execute('SELECT display, grtrack FROM pers WHERE name=?', (name,))
        res = self.curs.fetchall()

        if len(res) == 0:
            return (False, False)
        else:
            return (res[0][0] == 1, res[0][1] == 1)


    def setSat(self, name, disp, grnd):
        self.curs.execute('SELECT count(*) FROM pers WHERE name=?', (name,))
        res = self.curs.fetchone()

        if res[0] == 0:
            self.conn.execute('INSERT INTO pers VALUES(?, ?, ?)', (name, disp, grnd))
        else:
            self.conn.execute('UPDATE pers SET display=?, grtrack=? WHERE name =?', (disp, grnd, name))
        self.conn.commit()

        
    def getSatGroups(self):
        self.curs.execute('SELECT name FROM satgroups')
        res = self.curs.fetchall()
        print 'Res', res
        fnames = []
        for r in res:
            fnames.append(r[0])
        return fnames

    def setSatGroups(self, fnames):
        try:
            print 'set fnames', fnames
            self.curs.execute('DELETE FROM satgroups')
            self.conn.commit()
            for f in fnames:
                #print f
                self.curs.execute('INSERT INTO satgroups VALUES(?)', (f,))
            self.conn.commit()
        except Exception, e:
            print 'setSatGroups', e

    def loadEphem(self, fname):
        self.curs.execute('SELECT MIN(epoch),MIN(ts) FROM ephemeris WHERE fname=?', (fname,))
        res = self.curs.fetchall()
        utc = UTC()
        
        print 'Min epoch', res
        lines = []
        if res[0][0] != None:
            epc = datetime.datetime.strptime(res[0][0][:res[0][0].find('.')], '%Y-%m-%d %H:%M:%S')
            epc = epc.replace(tzinfo=utc)
            dt_epoch = datetime.datetime.now(utc) - epc
            print 'Delta time (epoch)',dt_epoch
        else:
            dt_epoch = None

        if res[0][1] != None:
            ftch = datetime.datetime.strptime(res[0][1][:res[0][1].find('.')], '%Y-%m-%d %H:%M:%S')
            ftch = ftch.replace(tzinfo=utc)
            dt_fetch = datetime.datetime.now(utc) - ftch
            print 'Delta time (last fetch)',dt_fetch
        else:
            dt_fetch = None

        # So go and grab a new ephemeris if we don't have one or the ephoch is close to a day old and we haven't
        #  grabbed a new one in the last 0.2 days
        # We should also add an 'event' to say when we should next try and grab a set of ephem data. Hmm... a event
        #  manager....hmmmmm
        if res[0][0] == None or (dt_epoch > datetime.timedelta(days=0.9) and (dt_fetch > datetime.timedelta(days=0.2))):
            try:
                self.curs.execute('DELETE FROM ephemeris WHERE fname=?', (fname,))
                self.conn.commit()
            except Exception, e:
                print 'Hmmmmm ',e
                pass
            print 'Downloading', fname
            data = urllib2.urlopen(self.baseHTTP+fname)
            lines += data.readlines()
            if len(lines) % 3 != 0:
                raise Exception("We didn't get a multiple of 3 lines from the website!!")

            if fname == 'cubesat.txt':
                lines += ['Aeneas\r\n', '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 01547\r\n',
                          '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.81879662026327\r\n']
                
            for x in xrange(len(lines) / 3):
                m = ephem.readtle(lines[x*3], lines[x*3+1], lines[x*3+2])
                self.curs.execute("INSERT INTO ephemeris(fname, line1, line2, line3, epoch, ts)  VALUES(?, ?, ?, ?, ?, datetime('now'))",
                                  (fname, lines[x*3], lines[x*3+1], lines[x*3+2], m._epoch.datetime()))
            self.conn.commit()
        else:
            print 'Just using existing data for ',fname

    def getEphem(self, fname):
        self.curs.execute('SELECT line1, line2, line3 FROM ephemeris WHERE fname=?', (fname,))
        res = self.curs.fetchall()

        return res
    
    def setEphemEpochTime(self, cname, etime):
        self.curs.execute('UPDATE ephemeris SET epoch=? WHERE line1=?', (etime.datetime(), cname))
        self.conn.commit()
    

    
