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

from GnuRadio2 import Demod_RX_Channel
import sys
import cjson

print sys.argv
args_orig = cjson.decode(sys.argv[1])
kwords = cjson.decode(sys.argv[2])
print args_orig, kwords

args=[]
#if sys.argv[1] == 'SSB_RX_Channel':
#    args.append('SSB')
#else:
#    args.append('FM')
    
for a in args_orig:
    if isinstance(a, str):
        args.append(a.replace('\\', ''))
    else:
        args.append(a)

for a in kwords.keys():
    if isinstance(kwords[a], str):
        kwords[a] = kwords[a].replace('\\', '')

print args,kwords

chan = Demod_RX_Channel(*args, **kwords)

chan.Run()

