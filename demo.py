import sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4

import pyrocko.pile, pyrocko.pile_viewer, pyrocko.hamster_pile
import pyrocko

class MineDemo(QApplication):


    def __init__(self, args):
        QApplication.__init__(self, args)
        
        self._win = QMainWindow()
        self._win.setGeometry(50,0,800,900)
        self._win.setWindowTitle("MINE")
        self._win.show()


        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button1 = QPushButton('Detection', self._win)
        button2 = QPushButton('Location', self._win)
        self.connect(button2, SIGNAL('clicked()'), self.location)
        button3 = QPushButton('FocalMechanism', self._win)
        button4 = QPushButton('Statistics', self._win)
        button5 = QPushButton('Tomography', self._win)
        button6 = QPushButton('Quit', self._win)
        self.connect(button6, SIGNAL('clicked()'), self.quit)
        
        infotext = QLabel('Long text giving information on the chosen application .................', self._win)
        infotext.setStyleSheet("font: 18pt") 
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
        self.layout.addWidget(guititle, 3,0)
        self.layout.addWidget(button1, 3,1)
        self.layout.addWidget(button2, 3,2)
        self.layout.addWidget(button3, 3,3)
        self.layout.addWidget(button4, 3,4)
        self.layout.addWidget(button5, 3,5)
        self.layout.addWidget(button6, 3,6)
        self.layout.addWidget(logomine, 3,7)
        self.layout.addWidget(logogeotech, 3,8)

        self._win.setCentralWidget(self.frame)

    def start_pile_viewer(self, ntracks=5, use_opengl=False, panel_parent=None, follow=120):
        self._source_pile = pyrocko.pile.make_pile(['demodata.mseed'])
        self._tlast = time.time()
         
        p = pyrocko.hamster_pile.HamsterPile()
        p.set_fixation_length(20.)
        
        self._pile_viewer = pyrocko.pile_viewer.PileViewer(p, ntracks_shown_max=ntracks,
                use_opengl=use_opengl, panel_parent=panel_parent)
        
        v = self._pile_viewer.get_view()
        v.follow(float(follow))
        ev = pyrocko.model.Event(time=time.time())
        v.add_marker(pyrocko.gui_util.EventMarker(ev))

        self._timer = QTimer( self )
        self.connect( self._timer, SIGNAL("timeout()"), self.periodical ) 
        self._timer.setInterval(4000)
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
    
    def event_alert(self,t_detection):
        event_ID = QLabel(t_detection, self._win)
        
        event_ID.setStyleSheet("background-color: rgb(255,0,0)")
        
        self.layout.addWidget(event_ID,2,4,1,1)

    def location(self):
         
        hideExceptForWidget(self)
        

        x_shift = 20
        y_shift = 20
        # create objects for drawing
        dash_pen = QPen(QColor("black"))
        b_brush = QBrush(QColor("black"))
        r_brush = QBrush(QColor("red"))
        triangle1 = QPolygonF()
        triangle1.append(QPointF(10,-10))
        triangle1.append(QPointF(0,5))
        triangle1.append(QPointF(20,5))

        triangle = QPolygonF()
        triangle.append(QPointF(10+x_shift,-10+y_shift))
        triangle.append(QPointF(0+x_shift,5+y_shift))
        triangle.append(QPointF(20+x_shift,5+y_shift))

        #create canvas for overview map and add to layout:
        map_canvas = QGraphicsView()
        self.layout.addWidget(map_canvas,1,0)

        self.loc_map = QGraphicsScene()
        map_canvas.setScene(self.loc_map)

        # Data do be drawed:
        self.scene_data2 = []
        self.scene_data = []
        self.scene_data.append({'routine':self.loc_map.addPolygon,
                                'z':1,
                                'args':(triangle,dash_pen,b_brush)})
        self.scene_data2.append({'routine':self.loc_map.addPolygon,
                                'z':2,
                                'args':(triangle1,dash_pen,r_brush)})
        # draw Data:
        d = self.scene_data.pop(0)
        item = d['routine'](*d['args'])
        item.setZValue(d['z'])      # setZValue sets stacking order of items

        d = self.scene_data2.pop(0)
        item = d['routine'](*d['args'])
        item.setZValue(d['z'])      # setZValue sets stacking order of items

        
    def Detection(self):
        self._pile_viewer.show()

def hideExceptForWidget(self,widget=None):
    '''
    Hide each widget in upper grid, except for the widget given as parameter
    '''
    # Hide trace viewer
    self._pile_viewer.hide()

args = sys.argv
minedemo = MineDemo(args)
minedemo.event_alert('latest Event: '+'234')
minedemo.exec_()

