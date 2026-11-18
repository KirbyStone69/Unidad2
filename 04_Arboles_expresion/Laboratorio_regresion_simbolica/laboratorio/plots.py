"""Embedded plots: cache axes/ticks and blit only the changing curve."""
import numpy as np
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self,history=False):
        self.figure=Figure(facecolor='#10241A',layout='constrained')
        super().__init__(self.figure)
        self.ax=self.figure.add_subplot(111); self.history=history
        self.ax.set_facecolor('#10241A')
        self.ax.tick_params(colors='#8BAF99',labelsize=8)
        for spine in self.ax.spines.values(): spine.set_color('#193528')
        self.ax.grid(color='#244633',alpha=.55)
        self.ax.set_xlabel('Generación' if history else 'x',color='#8BAF99')
        self.ax.set_ylabel('MSE · entrenamiento' if history else 'y',color='#8BAF99')
        self.line,=self.ax.plot([],[],color='#B8FFD1',lw=1.7,
                              label='Mejor MSE' if history else 'Predicción',animated=self.supports_blit)
        self.scatter=None; self.xs=[]; self.ys=[]; self.target=[]; self.current=[]
        self.background=None
        self.mpl_connect('draw_event',self._drawn)
        self.mpl_connect('resize_event',lambda event:setattr(self,'background',None))
        self.timer=QTimer(self); self.timer.setInterval(30); self.timer.timeout.connect(self.transition)
        self.legend()

    def _drawn(self,event):
        if self.supports_blit:
            self.background=self.copy_from_bbox(self.figure.bbox)
            self.ax.draw_artist(self.line)

    def render_line(self):
        if self.supports_blit and self.background is not None:
            self.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.blit(self.figure.bbox)
        else: self.draw_idle()

    def legend(self):
        legend=self.ax.legend(facecolor='#10241A',edgecolor='#193528',fontsize=8,loc='upper right')
        for t in legend.get_texts(): t.set_color('#E4FBEA')
        self.background=None

    def data(self,x,y):
        if self.scatter is not None: self.scatter.remove()
        self.scatter=self.ax.scatter(x,y,s=16,c='#39FF88',alpha=.8,label='Datos reales')
        self.line.set_data([],[]); self.legend()
        xspan=max(float(np.ptp(x)),1.); yspan=max(float(np.ptp(y)),1.)
        self.ax.set_xlim(float(min(x))-.04*xspan,float(max(x))+.04*xspan)
        self.ax.set_ylim(float(min(y))-.12*yspan,float(max(y))+.12*yspan)
        self.draw()

    def prediction(self,tree,x):
        ordered=np.linspace(float(min(x)),float(max(x)),300)
        self.line.set_data(ordered,tree.evaluate(ordered))
        # Fixed data-domain axes during search avoid re-rendering every tick/label.
        self.render_line()

    def reset(self,generations=100,upper=1.):
        self.timer.stop(); self.xs=[]; self.ys=[]; self.current=[]; self.target=[]
        self.line.set_data([],[])
        self.ax.set_xlim(0,max(1,generations)); self.ax.set_ylim(0,max(upper,1e-10)*1.05)
        self.background=None; self.draw()

    def finish(self):
        self.timer.stop(); self.current=list(self.target)
        self.line.set_data(self.xs,self.current)
        if self.xs:
            self.ax.set_xlim(0,max(1,self.xs[-1])); self.ax.set_ylim(0,max(max(self.ys),1e-10)*1.05)
        self.background=None; self.draw()

    def append(self,generation,mse):
        self.xs.append(generation); self.ys.append(mse)
        self.target=list(self.ys)
        self.current=self.current[:len(self.target)]
        while len(self.current)<len(self.target): self.current.append(self.current[-1] if self.current else mse)
        self.timer.start()

    def transition(self):
        a=np.asarray(self.current); b=np.asarray(self.target)
        self.current=(a+(b-a)*.3).tolist()
        if np.allclose(self.current,b,rtol=.001,atol=1e-10):
            self.current=list(self.target); self.timer.stop()
        self.line.set_data(self.xs,self.current); self.render_line()
