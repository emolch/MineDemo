import sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import pyrocko.pile, pyrocko.pile_viewer, pyrocko.hamster_pile

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
       
        self.start_pile_viewer()
        self._pile_viewer.setParent(self._win)
        
        self.layout.addWidget(infotext, 0,0,1,9)
        self.layout.addWidget(self._pile_viewer, 1,0,1,9)
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

    def start_pile_viewer(self, ntracks=5, use_opengl=False, panel_parent=None, follow=120):
        self._source_pile = pyrocko.pile.make_pile(['demodata.mseed'])
        self._tlast = time.time()
        
        p = pyrocko.hamster_pile.HamsterPile()
        p.set_fixation_length(20.)
        
        self._pile_viewer = pyrocko.pile_viewer.PileViewer(p, ntracks_shown_max=ntracks,
                use_opengl=use_opengl, panel_parent=panel_parent)
        
        self._pile_viewer.get_view().follow(float(follow))
        
        self._timer = QTimer( self )
        self.connect( self._timer, SIGNAL("timeout()"), self.periodical ) 
        self._timer.setInterval(3000)
        self._timer.start()

    def periodical(self):
        pile = self._source_pile
        tnow = time.time()
        tlen = tnow - self._tlast

        tmin = pile.tmin + self._tlast % (pile.tmax - pile.tmin)
        tmax = tmin + tlen 

        def shiftinsert(tmin, tmax, tdelay):
            traces = pile.all(tmin=tmin, tmax=tmax)
            for trace in traces:
                trace.shift(tdelay)
                self._pile_viewer.get_pile().insert_trace(trace)
      
        shiftinsert(tmin, tmax, self._tlast-tmin)
        if tmax > pile.tmax:
            tmin = tmin - (pile.tmax - pile.tmin)
            tmax = tmax - (pile.tmax - pile.tmin)
            shiftinsert(tmin, tmax, self._tlast-tmin)
        
        self._tlast = tnow

args = sys.argv
minedemo = MineDemo(args)
minedemo.exec_()

