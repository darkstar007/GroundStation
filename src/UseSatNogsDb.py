#!/usr/bin/env python

import cjson

import urllib2

freq = urllib2.urlopen('https://db.satnogs.org/api/transmitters/')
freq_data = cjson.decode(freq.read())
freq.close()

#print freq_data[0]

sats = urllib2.urlopen('https://db.satnogs.org/api/satellites/')
sats_data = cjson.decode(sats.read())
sats.close()

modes = urllib2.urlopen('https://db.satnogs.org/api/modes/')
modes_data = cjson.decode(modes.read())
modes.close()

#print sats_data[0]
print modes_data[0]

sat_cat_id = {}

for s in sats_data:
    if s['status'] == 'alive':
        sat_cat_id[str(s['norad_cat_id'])] = s['name']

for f in freq_data:
    try:
        if f['downlink_low'] > 100e6 and f['downlink_low'] < 200e6:
            print 'VHF', sat_cat_id[str(f['norad_cat_id'])], f
        if f['downlink_low'] > 2000e6:
            print 'uWave', sat_cat_id[str(f['norad_cat_id'])], f
    except KeyError:
        print 'Dead sat', f['norad_cat_id']
