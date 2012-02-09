import sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4

import pyrocko.pile, pyrocko.pile_viewer, pyrocko.hamster_pile
import pyrocko

class MineDemo(QApplication):
    
    '''
    This is a demo GUI
    '''

    def __init__(self, args):
        QApplication.__init__(self, args)
        
        self._win = QMainWindow()
        self._win.setGeometry(50,0,800,900)
        self._win.setWindowTitle("MINE")
        self._win.show()

        self.connect(self, SIGNAL('lastWindowClosed()'), self.quit)
        
        button1 = QPushButton('Detection', self._win)
        self.connect(button1, SIGNAL('clicked()'), self.stalta)

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

    def start_pile_viewer(self, ntracks=5, use_opengl=False, panel_parent=None, follow=250):
        self._source_pile = pyrocko.pile.make_pile(['Demodataset.mseed'])
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


        
    def Detection(self):
        self._pile_viewer.show()

    def Location(self):
        '''
        Activated when clicking the 'Location' button.
        Shows map with stations (triangles).
        '''

        self._pile_viewer.hide()
        
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
        self.layout.addWidget(map_canvas,1,0,1,6)

        self.loc_map = QGraphicsScene()
        map_canvas.setScene(self.loc_map)

        self.loc_map.setParent(self._win)
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
    
##### STA LTA #########################################################################   
    def stalta(self):
        '''Main work routine of the snuffling.'''
        
        #self.cleanup()
        
        pile = self._source_pile
        #pile = self.get_pile()
        if self.apply_to_all:
            tmin, tmax = pile.get_tmin(), pile.get_tmax()
        else:
            tmin, tmax = self.get_viewer().get_time_range()
    
        swin, ratio = self.swin, self.ratio
        lwin = swin * ratio
        
        tinc = min(lwin * self.block_factor, tmax-tmin)
        tpad = lwin*self.tpad_factor
        
        show_level_traces = self.show_level_traces
        
        if show_level_traces and tmax-tmin > lwin * 150:
            self.error('Processing time window is longer than 150 x LTA window. Turning off display of level traces.')
            show_level_traces = False
        
        # ACHTUNG: Pfad korrigieren pjoin(getcwd()):
        markers = []
        catalogue=open('catalogue.out','w')        
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

                trace.lowpass(4, self.lowpass)
                trace.highpass(4, self.highpass)
                 
                trace.ydata = trace.ydata**2
                trace.ydata = trace.ydata.astype(num.float32)
                if etr is None:
                    etr = trace
                else:
                    etr.add(trace)

                nslcs.append(trace.nslc_id)
            
            if etr is not None: 
                autopick.recursive_stalta(swin, lwin, self.ks, self.kl, self.kd, etr)                   
                etr.shift(-swin)
                etr.set_codes(channel='STA/LTA')
                etr.meta = { 'tabu': True }
                
                etr.chop(etr.tmin + lwin, etr.tmax - lwin)

                #tpeaks, apeaks = etr.peaks(self.level, swin*2., deadtime=False)
                tpeaks, apeaks, tzeros = etr.peaks(self.level, swin*2., deadtime=True)
                if show_level_traces:
                    #etr.chop(trace.wmin, trace.wmax)
                    self.add_traces([etr])

                for t, a in zip(tpeaks, apeaks):
                    print nslcs, util.time_to_str(t)
                    staz=nslcs[0]
                    catalogue.write('sta'+str(staz[1])+' '+util.time_to_str(t)+' '+str(a)+'\n')
                    if trace.wmin <= t <= trace.wmax:
                        mark = pile_viewer.Marker(nslcs, t, t)
                        print mark, a
                        markers.append(mark)
                                           
        if len(markers) == 1:
            mark0 = markers[0]
            mark_l = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin-lwin, mark0.tmin,  kind=1)
            mark_s = pile_viewer.Marker(mark0.nslc_ids, mark0.tmin, mark0.tmin+swin, kind=2)
            #markers.extend([mark_l, mark_s])

        self.add_markers(markers)
        catalogue.close()
#-------------------------------------------------------------------------------------------
args = sys.argv
minedemo = MineDemo(args)
minedemo.event_alert('latest Event: '+'234')
minedemo.exec_()

