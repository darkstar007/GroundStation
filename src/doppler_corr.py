#!/usr/bin/env python

import ephem
import numpy
import struct

obs = ephem.Observer()

obs.long = '-0.10982'
obs.lat = '52.44332'

l1='PHONESATS'
l2='1 99990U          13113.70833333  .01795425  00000-0  10551-2 0 00005'
l3='2 99990 051.6241 300.5810 0014076 348.5145 326.4915 16.14303457000309'

m = ephem.readtle(l1, l2, l3)

for offset in xrange(25):
    obs.date='2013/4/23 12:00:10'
    tr, azr, tt, altt, ts, azs=obs.next_pass(m)

    data=[]
    obs.date = tr + offset * 5 * ephem.second
    while obs.date < ts:
       m.compute(obs)
       data.append(m.range)
       obs.date += ephem.second

    freq=437.425e6
    c=299792458.0
    lamb = c / freq

    sample_rate = 1.536e6

    t0=0

    file_len = 3837908056
    file_samps = file_len / 8   # cos its in complex samples

    file_time = file_samps / sample_rate

    fp = open('/data/matt/mygnuradio/doppler.'+str(offset*5)+'.dat', 'wb')
    count = 0
    while t0 <= file_time:
        samp = int(t0)
        rng = (t0 - samp) * (data[samp+1] - data[samp]) + data[samp]
        phs = 2 * numpy.pi * rng / lamb
        s = struct.pack('ff', numpy.cos(phs), numpy.sin(phs))
        fp.write(s)
        t0 += 1.0 / sample_rate
        count +=1
        if count % 1536000 == 0:
            print 'Done ', t0*100.0/file_time,'% of offset',offset*5
    fp.close()
