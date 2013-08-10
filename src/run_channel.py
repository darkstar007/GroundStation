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

