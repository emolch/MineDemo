import sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as num
import pyrocko.pile,  pyrocko.hamster_pile
from pyrocko import autopick, util, pile_viewer

class MineDemo(QApplication):
    
    '''
    This is a demo GUI.
    '''


    def addStations(self,Station_Dict,Canvas,scale_x=400,scale_y=400):
        '''
        Adds stations (triangles) to map.
        @param Station_Dict Dictionary containing information of station locations
        @param Canvas Canvas to draw on
        @param scale_x give an x-scale value according to canvas size
        @param scale_y give an y-scale value according to canvas size
        '''
        #!!!!!!!!!!!!!!!!!!!!!!!!!
        # position probably incorrect?
        #!!!!!!!!!!!!!!!!!!!!!!!!!
        
        dash_pen = QPen(QColor("black"))
        b_brush = QBrush(QColor("black"))

        # Add station after station to map_canvas:
        for Station in Station_Dict:
            triangle = QPolygonF()
            triangle.append(QPointF(10+(float(Station['Stat_x']))*scale_x,-10+(float(Station['Stat_y'])*scale_y)))
            triangle.append(QPointF(0 +(float(Station['Stat_x']))*scale_x, 5 +(float(Station['Stat_y'])*scale_y)))
            triangle.append(QPointF(20+(float(Station['Stat_x']))*scale_x, 5 +(float(Station['Stat_y'])*scale_y)))
            scene_data = []
            scene_data.append({'routine':Canvas.addPolygon,
                                    'z':1,
                                    'args':(triangle,dash_pen,b_brush)})
     
            d = scene_data.pop(0)
            item = d['routine'](*d['args'])
            item.setZValue(d['z'])                  # setZValue sets stacking order of items
            item.setToolTip(Station['Stat_name'])   # mouse moves over item -> Show Stat_name 

    def __init__(self, args):
        QApplication.__init__(self, args)
        
        
        # read station's data and store to dictionary:
        self.Stat_file = open('Stations.dat','r')
        self._stat_dict = []
        for line in self.Stat_file:
            Stat_data = line.split()
            Stat_dict = {'Stat_name':Stat_data[0],'Stat_lat':Stat_data[1],
                'Stat_lon':Stat_data[2],'Stat_z':Stat_data[3],'Stat_x':Stat_data[4],
                'Stat_y':Stat_data[5]}
            self._stat_dict.append(Stat_dict) 
        
        self._win = QMainWindow()
        self._win.setGeometry(50,0,800,900)
        self._win.setWindowTitle("MINE")
        self._win.show()

        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button1 = QPushButton('Detection', self._win)
        self.connect(button1, SIGNAL('clicked()'), self.Detection)

        button2 = QPushButton('Location', self._win)
        self.connect(button2, SIGNAL('clicked()'), self.Location)
        
        button3 = QPushButton('FocalMechanism', self._win)
        button4 = QPushButton('Statistics', self._win)
        button5 = QPushButton('Tomography', self._win)
        button6 = QPushButton('Quit', self._win)
        self.connect(button6, SIGNAL('clicked()'), self.quit)
        
        infotext = QLabel('Long text giving information on application',self._win)
        infotext.setStyleSheet("font: 18pt") 

        imagelogomine = QPixmap("./logomine_small.png")
        logomine = QLabel('', self._win)
        logomine.setPixmap(imagelogomine)
        imagelogogeotech = QPixmap("./Logo_GEOTECH_small.png")
        logogeotech = QLabel('', self._win)
        logogeotech.setPixmap(imagelogogeotech)
        guititle = QLabel('MINE Project GUI Demonstrator', self._win)

        ###
        self.buttonBox = QGroupBox("Applications")
        self.layout = QGridLayout()
        #self.frame = QFrame(self._win)
        #self.frame.setLayout(self.layout)
       
        self.start_pile_viewer()
        self._pile_viewer.setParent(self._win)
        
        #self.layout.addWidget(infotext, 0,0,1,9)
        #self.layout.addWidget(self._pile_viewer, 1,0,1,9)
        #self.layout.addWidget(guititle, 3,0)
        self.layout.addWidget(button1, 3,1)
        self.layout.addWidget(button2, 3,2)
        self.layout.addWidget(button3, 3,3)
        self.layout.addWidget(button4, 3,4)
        self.layout.addWidget(button5, 3,5)
        self.layout.addWidget(button6, 3,6)
        self.layout.addWidget(logomine, 3,7)
        self.layout.addWidget(logogeotech, 3,8)
        
        ###
        self.buttonBox.setLayout(self.layout)
        
        ###
        self.topLayout = QStackedLayout()
        self.topLayout.addWidget(self._pile_viewer) 
        
        ###
        self._win.setCentralWidget(self.buttonBox)
        #self._win.setCentralWidget(self.topLayout)

        self._detectiontimer = QTimer( self )
        self.connect( self._detectiontimer, SIGNAL("timeout()"), self.stalta ) 
        self._detectiontimer.setInterval(8000)
        self._detectiontimer.start()
    def start_pile_viewer(self, ntracks=6, use_opengl=False, panel_parent=None, follow=60):
        self._source_pile = pyrocko.pile.make_pile(['Demodataset.mseed'])
        self._tlast = time.time()
         
        p = pyrocko.hamster_pile.HamsterPile()
        p.set_fixation_length(20.)
        
        self._pile_viewer = pyrocko.pile_viewer.PileViewer(p, ntracks_shown_max=ntracks,
                use_opengl=use_opengl, panel_parent=panel_parent)
        
        v = self._pile_viewer.get_view()
        v.follow(float(follow))

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


        
    def Detection(self):
        self._pile_viewer.show()

    def Location(self):
        '''
        Activated when clicking the 'Location' button.
        Shows map with stations (triangles).
        '''
        self._pile_viewer.hide()
        #create canvas for overview map and add to layout:
        scale_x=680
        scale_y=680
        map_canvas = QGraphicsView()
        self.topLayout.addWidget(map_canvas)
        
        self.loc_map = QGraphicsScene()
        map_canvas.setScene(self.loc_map)
        
        # TEST: add background image with location result
        bg_loc = QPixmap("images/ruhr1xy.gif")
        self.loc_map.addPixmap(bg_loc.scaled(scale_x,scale_y)) # bg_loc.scaled() returns copy.
                                        # how to avoid that?

        self.loc_map.setParent(self._win)
        self.addStations(self._stat_dict,self.loc_map,680,680)

##### STA LTA #########################################################################   
    ''' Based on stalta by Francesco Grigoli.
    All values are preliminary. 
    TODO: Add button: "change LTASTA parameters --> snufflings' panel will open
    '''
    def stalta(self):
        '''Main work routine of the snuffling.'''
        tnow = time.time() 
        pile = self._source_pile

        tlen = tnow - self._tlast
        _tmin = pile.tmin + self._tlast % (pile.tmax - pile.tmin)
        tmin, tmax = pile.get_tmin(), pile.get_tmax()
        
        swin, ratio = 0.01, 10
        lwin = swin * ratio
        self.block_factor=8.79
        tinc = min(lwin * self.block_factor, tmax-tmin)
        self.tpad_factor=10
        tpad = lwin*self.tpad_factor
        ks = 1.0
        kl = 1.8
        kd = 0.
        level = 6.0

        show_level_traces = True
        if show_level_traces and tmax-tmin > lwin * 150:
            
            print('Processing time window is longer than 150 x LTA window. Turning off display of level traces.')
            show_level_traces = False
        
        self.markers = []
        for traces in pile.chopper_grouped(tmin=tmin, tmax=tmax, tinc=tinc, tpad=tpad, want_incomplete=False,
                gather=lambda tr: tr.nslc_id[:3]):

            etr = None
            nslcs = []
            deltat = 0.
            for trace in traces:
                if deltat == 0:
                    deltat = trace.deltat
                else:
                    if abs(deltat - trace.deltat) > 0.0001*deltat:
                        
                        logger.error('skipping trace %s.%s.%s.%s with unexpected sampling rate' % trace.nslc_id)
                        continue
                lowpass = 202
                highpass = 8
                trace.lowpass(4, lowpass)
                trace.highpass(4, highpass)
                 
                trace.ydata = trace.ydata**2
                trace.ydata = trace.ydata.astype(num.float32)
                if etr is None:
                    etr = trace
                else:
                    etr.add(trace)

                nslcs.append(trace.nslc_id)
            
            if etr is not None: 
                autopick.recursive_stalta(swin, lwin, ks, kl, kd, etr)                   
                etr.shift(-swin)
                etr.set_codes(channel='STA/LTA')
                etr.meta = { 'tabu': True }
                
                etr.chop(etr.tmin + lwin, etr.tmax - lwin)
                tpeaks, apeaks, tzeros = etr.peaks(level, swin*2., deadtime=True)
                if show_level_traces:
                    self.add_traces([etr])

                for t, a in zip(tpeaks, apeaks):
                    staz=nslcs[0]
                    
                    # Add markers in a time frame tnow-11 to tnow-3 Seconds
                    # This interval looks realistic
                    if (tnow-11<=t-_tmin+self._tlast<= tnow-3):
                        
                        if (pile.get_tmin() <= t <= pile.get_tmax()):
                         
                            mark = pile_viewer.Marker(nslcs, t-_tmin+self._tlast, t-_tmin+self._tlast)
                            self.markers.append(mark)

        if len(self.markers) == 1:
            mark0 = self.markers[0]
            mark_l = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin-lwin+self._tlast, mark0.tmin+self._tlast,  kind=1)
            mark_s = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin+self._tlast, mark0.tmin+swin+self._tlast, kind=2)
            self.markers.extend([mark_l, mark_s])
        v = self._pile_viewer.get_view()
        v.add_markers(self.markers)
         
#-------------------------------------------------------------------------------------------
args = sys.argv
minedemo = MineDemo(args)
minedemo.event_alert('latest Event: '+'234')
minedemo.exec_()

