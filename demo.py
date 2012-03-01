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

    def __init__(self, ntracks=6, use_opengl=False, panel_parent=None, follow=20):
        source_pile = pile.make_pile(['Demodataset_new.mseed'])
        p = hamster_pile.HamsterPile()
        p.set_fixation_length(20.)
        pile_viewer.PileViewer.__init__(self, p, ntracks_shown_max=ntracks,
                use_opengl=use_opengl, panel_parent=panel_parent)

        self._tlast = time.time()
        self._tlast_stalta = None
        self._tmin = source_pile.tmin + self._tlast % (source_pile.tmax - source_pile.tmin)
        
        v = self.get_view()
        v.follow(float(follow))

        self._source_pile = source_pile

        self._timer = QTimer( self )
        self.connect( self._timer, SIGNAL("timeout()"), self.periodical ) 
        self._timer.setInterval(1000)
        self._timer.start()
        
        self._detectiontimer = QTimer( self )
        self.connect( self._detectiontimer, SIGNAL("timeout()"), self.stalta ) 
        self._detectiontimer.setInterval(3000)
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
                trace.shift(tdelay+1)

                self.get_pile().insert_trace(trace)
      
        shiftinsert(tmin, tmax, self._tlast-tmin)
        if tmax > source_pile.tmax:
            tmin = tmin - (source_pile.tmax - source_pile.tmin)
            tmax = tmax - (source_pile.tmax - source_pile.tmin)
            shiftinsert(tmin, tmax, self._tlast-tmin)
        
        self._tlast = tnow
        self.get_view().update()

    def stalta(self):
        ''' 
        Based on stalta by Francesco Grigoli.
        '''

        tnow = time.time() 
        pile = self.get_view().pile
        if self._tlast_stalta is None:
            self._tlast_stalta = tnow
            return

        tmin = self._tlast_stalta
        tmax = tnow
        
        self._tlast_stalta = tnow

        swin, ratio = 0.07, 8
        lwin = swin * ratio
        
        tpad = lwin
        ks = 1.0
        kl = 1.8
        kd = 0.
        level = 6.0

        _numMarkers = 0
        
        self.markers = []
        for traces in pile.chopper_grouped(tmin=tmin, tmax=tmax, tpad=tpad, want_incomplete=True,
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

                for t, a in zip(tpeaks, apeaks):
                    staz=nslcs[0]
                    
                    mark = pile_viewer.Marker(nslcs, t,t)
                    print mark
                    self.markers.append(mark)
            print 'xx'

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
        
        self.loc_map = QGraphicsScene()
        self.setScene(self.loc_map)
        
        self.image_item = None
        
        #self._image = QPixmap("images/ruhr%ixy.jpg" % 1)

        #self.scaledImage = self._image.scaled(
        #        QSize(self.width(),self.height()),Qt.KeepAspectRatioByExpanding)
        
        #self.image_item = self.loc_map.addPixmap(QPixmap(self.scaledImage)) 
        
        self.indx = 0

    def setStations(self, stations):
        self._stations = stations
    
    def setImage(self):
        
        self.events = [1,3,4]
        
        self._image = QPixmap("images/ruhr%ixy.jpg" % self.events[self.indx%3])
        
        if self.image_item:
            self.loc_map.removeItem(self.image_item)

        self.scaledImage = self._image.scaled(
                QSize(self.width(),self.height()),Qt.KeepAspectRatioByExpanding)
        
        self.image_item = self.loc_map.addPixmap(self.scaledImage) 
        
        self.indx += 1

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

class Statistics(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.statisticsScene = QGraphicsScene()
        self.setScene(self.statisticsScene)
        self.imageStatistics = QPixmap("./images/Statistics.jpg")
        self.scaledImage = self.imageStatistics.scaled(QSize(self.width(),self.height()),Qt.KeepAspectRatioByExpanding)
        
        self.image_item = self.statisticsScene.addPixmap(self.scaledImage) 


'''
class FocalMechanism(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.foc_mec = QGraphicsScene()
        self.setScene(self.foc_mec)
        self.imageFocMec = QPixmap("./images/focalmechanisms.jpg")
        self.image_item = self.foc_mec.addPixmap(self.imageFocMec) 
'''

class FocalMechanism(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        self.localLayout = QGridLayout()
        self.setLayout(self.localLayout)
#        self.localFrame.setLayout(self.localLayout)

        self.foclabel = QLabel('')
        self.imagefocmec = QPixmap("./images/focalmechanisms.jpg")
        #scaledimage = imagefocmec.scaled(
        #        QSize(localFrame.width(),localFrame.height()),Qt.KeepAspectRatioByExpanding)
        self.scaledimage = self.imagefocmec.scaled(800,500)
        self.foclabel.setPixmap(self.scaledimage)
        
        
        self.localLayout.addWidget(self.foclabel)
#        foc_mec = QGraphicsScene()
#        view.setScene(foc_mec)
#        self.addWidget(self.foc_mec)
        #layout.addWidget(foc_mec)
   #     self.setScene(self.foc_mec)
    #    self.imageFocMec = QPixmap("./images/focalmechanisms.jpg")
      #  self.image_item = self.foc_mec.addPixmap(self.imageFocMec) 
        

class Tomographie(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        #self.tomographieScene = QGraphicsScene()
        #self.setScene(self.tomographieScene)
        self.Tomolabel = QLabel('', self)
        
        self.imageTomographie = QPixmap("./images/figure3dbis.jpg")
        self.scaledImage = self.imageTomographie.scaled(
                QSize(self.width(),self.height()),Qt.KeepAspectRatioByExpanding)
        #self.image_item = self.tomographieScene.addPixmap(self.scaledImage)
        self.Tomolabel.setPixmap(self.scaledImage)

class MineDemo(QApplication):
    
    '''
    This is a demo GUI.
    '''
    
    def __init__(self, args):
       
        QApplication.__init__(self, args)
        
        # read station's data and store to dictionary (temporarily deprecated):
        # self._stations = load_stations('Stations.dat')
        
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
        locationWidget.setImage()
        focalMechanismWidget = FocalMechanism()
        statisticsWidget = Statistics()
        tomographieWidget = Tomographie()
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
                (button3, focalMechanismWidget), 
                (button4, statisticsWidget),
                (button5, tomographieWidget) ]:        
            container.addWidget(widget)
            self.connect(button, SIGNAL('clicked()'), 
                    stacked_widget_setter(container, widget))
        
        self._win.setCentralWidget(frame)
        self.connect(tracesWidget, SIGNAL('valueChanged(int)'),locationWidget.setImage)
         
#---------------------------------------------------------------------------
args = sys.argv
minedemo = MineDemo(args)
minedemo.exec_()

