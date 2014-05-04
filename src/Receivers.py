
from PyQt4 import QtGui
from PyQt4 import QtCore

have_pyrtlsdr = False
try:
    import rtlsdr
    have_pyrtlsdr = True
    import ctypes
except:
    print 'oh dear, no rtlsdr python library'

    
class Receiver(QtGui.QFrame):
    def __init__(self, idx, sdrtype, db):
        QtGui.QWidget.__init__(self)
        grid = QtGui.QGridLayout()
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.setLineWidth(2)
        self.db = db
        
        self.setLayout(grid)
        if sdrtype == 'RTLSDR':
            a=ctypes.create_string_buffer(300)
            b=ctypes.create_string_buffer(300)
            c=ctypes.create_string_buffer(300)

            aa=ctypes.cast(a, ctypes.POINTER(ctypes.c_ubyte))
            bb=ctypes.cast(b, ctypes.POINTER(ctypes.c_ubyte))
            cc=ctypes.cast(c, ctypes.POINTER(ctypes.c_ubyte))
            
            rtlsdr.librtlsdr.rtlsdr_get_device_usb_strings(idx, aa, bb, cc)
            
            self.manufact = ctypes.string_at(aa)
            self.product = ctypes.string_at(bb)
            self.serial = ctypes.string_at(cc)
            defs = db.getReceiver(self.serial)
            if defs is not None:
                self.sample_rate = defs['sample_rate']
                self.default = (defs['defau'] == 1)
                self.correction = defs['correction']
            else:
                self.sample_rate = 2.048e6
                self.default = False
                self.correction = 0.0

            if self.default:
                self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

            grid.addWidget(QtGui.QLabel("Manufacturer"), 0, 0)
            grid.addWidget(QtGui.QLabel(self.manufact), 0, 1)
            grid.addWidget(QtGui.QLabel("Product"), 1, 0)
            grid.addWidget(QtGui.QLabel(self.product), 1, 1)
            grid.addWidget(QtGui.QLabel("Serial"), 2, 0)
            grid.addWidget(QtGui.QLabel(self.serial), 2, 1)
            
            grid.addWidget(QtGui.QLabel("Sample Rate"), 3, 0)
            self.sample_rate_entry = QtGui.QLineEdit(str(self.sample_rate))
            grid.addWidget(self.sample_rate_entry, 3, 1)
            self.sample_rate_entry.editingFinished.connect(self.entry_changed)

            grid.addWidget(QtGui.QLabel("Correction (ppm)"), 4, 0)
            self.correction_entry = QtGui.QLineEdit(str(self.correction))
            grid.addWidget(self.correction_entry, 4, 1)
            self.correction_entry.editingFinished.connect(self.entry_changed)

            
        elif sdrtype == 'USRP':
            pass
        elif sdrtype == 'HackRF':
            pass
        else:
            raise Exception('Unknown sdrtype ('+str(sdrtype)+') passed to Receiver()')

    def entry_changed(self):
        self.sample_rate = float(self.sample_rate_entry.text())
        self.correction = float(self.correction_entry.text())
        self.db.addReceiver(self)
        
class ReceiverPanel(QtGui.QGridLayout):
    def __init__(self, db):
        QtGui.QGridLayout.__init__(self)
        self.setObjectName('ReceiverPanel')
        self.find_all_receivers(db)

        row = 0
        for r in self.recs:
            self.addWidget(r, row, 0)
            row += 1
        self.setRowStretch(row,1)
        
    def find_all_receivers(self, db):
        self.recs = []
        if have_pyrtlsdr:
            for x in xrange(rtlsdr.librtlsdr.rtlsdr_get_device_count()):
                self.recs.append(Receiver(x, 'RTLSDR', db))
