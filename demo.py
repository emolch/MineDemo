import sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as num
from pyrocko import pile, hamster_pile, autopick, util, pile_viewer, model, gui_util

def stacked_widget_setter(stackwidget, widget):
    
    def setit():
        stackwidget.setCurrentWidget(widget)
    
    return setit

def load_stations(fn):
    f = open(fn,'r')
    stations = []
    for line in f:

        data = line.split()
        s = model.Station(lat=float(data[1])/100000., lon=float(data[2])/100000., depth=-float(data[3]))
        s.my_x = float(data[4])
        s.my_y = float(data[5])

        stations.append(s)
    return stations


class TracesWidget(pile_viewer.PileViewer):

    def __init__(self, ntracks=6, use_opengl=False, panel_parent=None, follow=60):
        source_pile = pile.make_pile(['Demodataset.mseed'])
        p = hamster_pile.HamsterPile()
        p.set_fixation_length(20.)
        pile_viewer.PileViewer.__init__(self, p, ntracks_shown_max=ntracks,
                use_opengl=use_opengl, panel_parent=panel_parent)

        self._tlast = time.time()
        self._tmin = source_pile.tmin + self._tlast % (source_pile.tmax - source_pile.tmin)
        
        v = self.get_view()
        v.follow(float(follow))

        self._source_pile = source_pile

        self._timer = QTimer( self )
        self.connect( self._timer, SIGNAL("timeout()"), self.periodical ) 
        self._timer.setInterval(4000)
        self._timer.start()
        
        self._detectiontimer = QTimer( self )
        self.connect( self._detectiontimer, SIGNAL("timeout()"), self.stalta ) 
        self._detectiontimer.setInterval(8000)
        self._detectiontimer.start()


    def periodical(self):
        source_pile = self._source_pile
        tnow = time.time()
        
        tlen = tnow - self._tlast

        tmin = source_pile.tmin + self._tlast % (source_pile.tmax - source_pile.tmin)
        self._tmin = tmin
        tmax = tmin + tlen 

        def shiftinsert(tmin, tmax, tdelay):
            traces = source_pile.all(tmin=tmin, tmax=tmax)
            for trace in traces:
                trace.shift(tdelay)

                self.get_pile().insert_trace(trace)
      
        shiftinsert(tmin, tmax, self._tlast-tmin)
        if tmax > source_pile.tmax:
            tmin = tmin - (source_pile.tmax - source_pile.tmin)
            tmax = tmax - (source_pile.tmax - source_pile.tmin)
            shiftinsert(tmin, tmax, self._tlast-tmin)
        
        self._tlast = tnow

    def stalta(self):
        ''' 
        Based on stalta by Francesco Grigoli.
        '''

        tnow = time.time() 
        pile = self._source_pile

        tlen = tnow - self._tlast
        _tmin = pile.tmin + self._tlast % (pile.tmax - pile.tmin)
        tmin, tmax = pile.get_tmin(), pile.get_tmax()
        
        swin, ratio = 0.07, 8
        lwin = swin * ratio
        self.block_factor=8.
        tinc = min(lwin * self.block_factor, tmax-tmin)
        self.tpad_factor=7.
        tpad = lwin*self.tpad_factor
        ks = 1.0
        kl = 1.8
        kd = 0.
        level = 6.0

        _numMarkers = 0
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
                lowpass = 20
                highpass = 1
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
                    #self._source_pile.add_traces([etr])
                    pass

                for t, a in zip(tpeaks, apeaks):
                    staz=nslcs[0]
                    
                    # Add markers in a time frame tnow-11 to tnow-3 Seconds
                    if (tnow-11<=t-_tmin+self._tlast<= tnow-3):
                        
                        if (pile.get_tmin() <= t <= pile.get_tmax()):
                         
                            mark = pile_viewer.Marker(nslcs, t-_tmin+self._tlast, t-_tmin+self._tlast)
                            self.markers.append(mark)

        if len(self.markers) == 1:
            mark0 = self.markers[0]
            mark_l = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin-lwin+self._tlast, mark0.tmin+self._tlast,  kind=1)
            mark_s = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin+self._tlast, mark0.tmin+swin+self._tlast, kind=2)
            self.markers.extend([mark_l, mark_s])
        v = self.get_view()
        _numMarkers+=len(self.markers)
        
        # emit signal, when Event was detected:
        if _numMarkers>=10:
            self.emit(SIGNAL('valueChanged(int)'),_numMarkers)
        v.add_markers(self.markers)


class LocationWidget(QGraphicsView):
    '''
    Shows map with stations (triangles).
    '''
    def __init__(self):
        QGraphicsView.__init__(self)


        #create canvas for overview map and add to layout:
        scale_x=680
        scale_y=680
        
        self.loc_map = QGraphicsScene()
        self.setScene(self.loc_map)
        
        self.image_item = None
        
        self._image = QPixmap("images/ruhr%ixy.gif" % 4)
        self.image_item = self.loc_map.addPixmap(QPixmap("images/ruhr3xy.gif")) 

    def setStations(self, stations):
        self._stations = stations
    
    def findImage(self):
        event_no = int(time.time()%5)
        self._image = QPixmap("images/ruhr%ixy.gif" % event_no)

    def setImage(self):
        # TEST: add background image with location result
        if self.image_item:
            self.loc_map.removeItem(self.image_item)

        self.image_item = self.loc_map.addPixmap(self._image) 

    def addStations(self,Station_Dict,Canvas,scale_x=400,scale_y=400):
        '''
        Adds stations (triangles) to map.
        @param Station_Dict Dictionary containing information of station locations
        @param Canvas Canvas to draw on
        @param scale_x give an x-scale value according to canvas size
        @param scale_y give an y-scale value according to canvas size
        '''
        
        dash_pen = QPen(QColor("black"))
        b_brush = QBrush(QColor("black"))

        # Add station after station to map_canvas:
        for Station in Station_Dict:
            triangle = QPolygonF()
            triangle.append(QPointF(10+(float(Station['Stat_x']))*scale_x,
                                -10+(float(Station['Stat_y'])*scale_y)))
            triangle.append(QPointF(0 +(float(Station['Stat_x']))*scale_x,
                                5 +(float(Station['Stat_y'])*scale_y)))
            triangle.append(QPointF(20+(float(Station['Stat_x']))*scale_x,
                                5 +(float(Station['Stat_y'])*scale_y)))
            scene_data = []
            scene_data.append({'routine':Canvas.addPolygon,
                                    'z':1,
                                    'args':(triangle,dash_pen,b_brush)})
     
            d = scene_data.pop(0)
            item = d['routine'](*d['args'])
            item.setZValue(d['z'])                  # setZValue sets stacking order of items
            item.setToolTip(Station['Stat_name'])   # mouse moves over item -> Show Stat_name 

class FocalMechanism(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.foc_mec = QGraphicsScene()
        self.setScene(self.foc_mec)
        self.imageFocMec = QPixmap("./images/figure5_cropped_rotated.jpg")
        #foc_mec.setPixmap(imageFocMec)
        self.image_item = self.foc_mec.addPixmap(self.imageFocMec) 
        

class MineDemo(QApplication):
    
    '''
    This is a demo GUI.
    '''
    
    def __init__(self, args):
       
        QApplication.__init__(self, args)
        
        # read station's data and store to dictionary:
        self._stations = load_stations('Stations.dat')
        
        self._win = QMainWindow()
        self._win.setGeometry(50,0,800,900)
        self._win.setWindowTitle("MINE")
        self._win.show()

        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button1 = QPushButton('Detection', self._win)
        button2 = QPushButton('Location', self._win)
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

        frame = QFrame()
        layout = QGridLayout()
        frame.setLayout(layout)

        tracesWidget = TracesWidget()
        locationWidget = LocationWidget()
        focalMechanism = FocalMechanism()
        plotWidget = gui_util.PyLab()

        container = QStackedWidget()

        layout.addWidget(infotext, 0,0,1,9)
        layout.addWidget(container, 1,0,1,9)
        layout.addWidget(guititle, 3,0)
        layout.addWidget(button1, 3,1)
        layout.addWidget(button2, 3,2)
        layout.addWidget(button3, 3,3)
        layout.addWidget(button4, 3,4)
        layout.addWidget(button5, 3,5)
        layout.addWidget(button6, 3,6)
        layout.addWidget(logomine, 3,7)
        layout.addWidget(logogeotech, 3,8)
       
        for button, widget in [ 
                (button1, tracesWidget), 
                (button2, locationWidget),
                (button4, plotWidget),
                (button3, focalMechanism) ]:
                
            container.addWidget(widget)
            self.connect(button, SIGNAL('clicked()'), 
                    locationWidget.setImage)
            self.connect(button, SIGNAL('clicked()'), 
                    stacked_widget_setter(container, widget))
        
        
        self._win.setCentralWidget(frame)
        self.connect(tracesWidget, SIGNAL('valueChanged(int)'),locationWidget.findImage)
        
         
#---------------------------------------------------------------------------
args = sys.argv
minedemo = MineDemo(args)
minedemo.exec_()

