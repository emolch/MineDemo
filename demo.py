import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MineDemo(QApplication):

    def __init__(self, args):
        QApplication.__init__(self, args)

        self._win = QMainWindow()
        self._win.show()

        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button = QPushButton('Press me!', self._win)
        button2 = QPushButton('Press me 2!', self._win)
        self.connect(button, SIGNAL('clicked()'), self.quit)

        label = QLabel('Label', self._win)

        self.layout = QGridLayout()
        
        self.frame = QFrame(self._win)
        self.frame.setLayout(self.layout)
        
        self.layout.addWidget(label, 0,0)
        self.layout.addWidget(button, 1,0)
        self.layout.addWidget(button2, 2,0)


        self._win.setCentralWidget(self.frame)

args = sys.argv

minedemo = MineDemo(args)
minedemo.exec_()


