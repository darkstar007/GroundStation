
from PyQt4 import QtGui
from PyQt4 import QtCore

have_pyrtlsdr = False
try:
    import rtlsdr
    have_pyrtlsdr = True
    import ctypes
except:
    print 'oh dear, no rtlsdr python library'

    
class Receiver(QtGui.QWidget):
    def __init__(self, idx, sdrtype):
        QtGui.QWidget.__init__(self)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        if sdrtype == 'RTLSDR':
            a=ctypes.create_string_buffer(300)
            b=ctypes.create_string_buffer(300)
            c=ctypes.create_string_buffer(300)

            aa=ctypes.cast(a, ctypes.POINTER(ctypes.c_ubyte))
            bb=ctypes.cast(b, ctypes.POINTER(ctypes.c_ubyte))
            cc=ctypes.cast(c, ctypes.POINTER(ctypes.c_ubyte))
            
            rtlsdr.librtlsdr.rtlsdr_get_device_usb_strings(0,aa,bb,cc)
            
            self.manufact = ctypes.string_at(aa)
            self.product = ctypes.string_at(bb)
            self.serial = ctypes.string_at(cc)
            self.sample_rate = 2.048e6

            grid.addWidget(QtGui.QLabel("Manufacturer"), 0, 0)
            grid.addWidget(QtGui.QLabel(self.manufact), 0, 1)
            grid.addWidget(QtGui.QLabel("Product"), 1, 0)
            grid.addWidget(QtGui.QLabel(self.product), 1, 1)
            grid.addWidget(QtGui.QLabel("Serial"), 2, 0)
            grid.addWidget(QtGui.QLabel(self.serial), 2, 1)
            grid.addWidget(QtGui.QLabel("Sample Rate"), 3, 0)
            grid.addWidget(QtGui.QLabel(str(self.sample_rate)), 3, 1)

            
        elif sdrtype == 'USRP':
            pass
        elif sdrtype == 'HackRF':
            pass
        else:
            raise Exception('Unknown sdrtype ('+str(sdrtype)+') passed to Receiver()')

        
class ReceiverPanel(QtGui.QGridLayout):
    def __init__(self):
        QtGui.QGridLayout.__init__(self)
        self.setObjectName('ReceiverPanel')
        self.find_all_receivers()
        row = 0
        for r in self.recs:
            self.addWidget(r, row, 0)
            row += 1
        
    def find_all_receivers(self):
        self.recs = []
        if have_pyrtlsdr:
            for x in xrange(rtlsdr.librtlsdr.rtlsdr_get_device_count()):
                self.recs.append(Receiver(x, 'RTLSDR'))
            
