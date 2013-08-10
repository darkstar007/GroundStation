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

from GnuRadio2 import *
import sys
import cjson

print sys.argv
args = cjson.decode(sys.argv[2])
kwords = cjson.decode(sys.argv[3])
print args, kwords
for a in kwords.keys():
    if isinstance(kwords[a], str):
        kwords[a] = kwords[a].replace('\\', '')

print kwords

if sys.argv[1] == 'SSB_RX_Channel':
    chan = SSB_RX_Channel(*args, **kwords)
if sys.argv[1] == 'FM_RX_Channel':
    chan = FM_RX_Channel(*args, **kwords)

chan.Run()

