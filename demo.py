import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MineDemo(QApplication):

    def __init__(self, args):
        QApplication.__init__(self, args)

        self._win = QMainWindow()
        self._win.show()

        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button1 = QPushButton('Detection', self._win)
        button2 = QPushButton('Location', self._win)
        button3 = QPushButton('FocalMechanism', self._win)
        button4 = QPushButton('Statistics', self._win)
        button5 = QPushButton('Tomography', self._win)
        button6 = QPushButton('Quit', self._win)
        self.connect(button6, SIGNAL('clicked()'), self.quit)
        
	infotext = QLabel('Long text giving information on the chosen application .................', self._win)
        label = QLabel('Second Label', self._win)
	imagelogomine = QPixmap("./logomine_small.png")
        logomine = QLabel('', self._win)
	logomine.setPixmap(imagelogomine)
	imagelogogeotech = QPixmap("./Logo_GEOTECH_small.png")
        logogeotech = QLabel('', self._win)
        logogeotech.setPixmap(imagelogogeotech)
	guititle = QLabel('MINE Project GUI Demonstrator', self._win)
        
        
	self.layout = QGridLayout()
        
        self.frame = QFrame(self._win)
        self.frame.setLayout(self.layout)
        
        self.layout.addWidget(infotext, 0,0,0,8)
        self.layout.addWidget(label, 1,0,1,7)
        self.layout.addWidget(guititle, 2,0)
        self.layout.addWidget(button1, 2,1)
        self.layout.addWidget(button2, 2,2)
        self.layout.addWidget(button3, 2,3)
        self.layout.addWidget(button4, 2,4)
        self.layout.addWidget(button5, 2,5)
        self.layout.addWidget(button6, 2,6)
        self.layout.addWidget(logomine, 2,7)
        self.layout.addWidget(logogeotech, 2,8)


        self._win.setCentralWidget(self.frame)

args = sys.argv

minedemo = MineDemo(args)
minedemo.exec_()

