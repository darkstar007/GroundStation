
import ephem

l1 = 'Aeneas'
l2 = '1 90038U 0        13149.44262065 +.00007265 +00000-0 +65364-3 0 0154'
l3 = '2 90038 064.6700 329.7178 0203072 217.8255 140.8445 14.8187966202632'

for x in range(10):
    for y in range(10):
        try:
            f = ephem.readtle(l1, l2+str(x), l3+str(y))
            print 'woohoo',x,y
        except Exception,e:
            print e, x, y


