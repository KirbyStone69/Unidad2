"""Only the best expression from each generation, in a table and one shared plot."""
from dataclasses import dataclass
import numpy as np
from .expressions import Node
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QLabel,QTableWidget,
                            QTableWidgetItem,QHeaderView,QAbstractItemView,QPushButton,QApplication)
from .plots import PlotCanvas

GENERATION_COLORS=('#63DFFF','#FFDB85','#C4A5FF','#FF8BA6','#B8FFD1','#39FF88')

@dataclass(frozen=True)
class GenerationBest:
    generation: int
    tree: Node
    mse: float
    nmse: float
    r2: float


class ComparisonPlot(PlotCanvas):
    """One Cartesian canvas for data and the champion of every recorded generation."""
    def __init__(self):
        self.focus_data=True
        super().__init__()
        self.line.set_linewidth(2.5)
        self.line.set_color('#B83240')
        self.generation_lines=LineCollection([],linewidths=1.1,alpha=.5,animated=self.supports_blit)
        self.ax.add_collection(self.generation_lines)
        self._curve_cache={}

    def draw(self,*args,**kwargs):
        if not self.isVisible():
            self.background=None
            return
        super().draw(*args,**kwargs)

    def data(self,x,y):
        self._real_y=np.asarray(y,dtype=float).copy()
        self.clear_candidates()
        super().data(x,y)
        self._data_bounds=self.ax.get_ylim()

    def legend(self):
        handles=[Line2D([],[],color='#39FF88',marker='o',linestyle='',markersize=4,label='Datos reales'),
                 Line2D([],[],color='#B83240',lw=2.5,label='Mejor predicción')]
        if getattr(self,'generation_lines',None) is None or self.generation_lines.get_visible():
            handles.append(Line2D([],[],color='#63DFFF',lw=1.1,label='Mejores por generación'))
        legend=self.ax.legend(handles=handles,facecolor='#10241A',edgecolor='#193528',fontsize=7,loc='upper right')
        for text in legend.get_texts():text.set_color('#E4FBEA')
        self.background=None

    def _dynamic(self):
        # Draw the best/educational prediction last, so it stays distinguishable.
        return [getattr(self,'generation_lines',None),self.line]

    def _drawn(self,event):
        if self.supports_blit:
            self.background=self.copy_from_bbox(self.figure.bbox)
            for artist in self._dynamic():
                if artist is not None and artist.get_visible():self.ax.draw_artist(artist)

    def render_line(self):
        if self.supports_blit and self.background is not None:
            self.restore_region(self.background)
            for artist in self._dynamic():
                if artist is not None and artist.get_visible():self.ax.draw_artist(artist)
            self.blit(self.figure.bbox)
        else:self.draw_idle()

    def clear_candidates(self):
        self.generation_lines.set_segments([])
        self._curve_cache={}
        self.line.set_data([],[])
        self._auto_fit=True

    def _update_bounds(self,force=False):
        if self.focus_data:
            bounds=self._data_bounds
        else:
            values=[self._real_y]
            if len(self.line.get_ydata()):values.append(np.asarray(self.line.get_ydata()))
            if self.generation_lines.get_visible():values.extend(segment[:,1] for segment in self.generation_lines.get_segments())
            low=min(float(np.min(value)) for value in values);high=max(float(np.max(value)) for value in values)
            old_low,old_high=self.ax.get_ylim()
            if not (force or self._auto_fit):
                if old_low<=low and high<=old_high:return
                low=min(low,old_low);high=max(high,old_high)
            margin=max((high-low)*.06,.1);bounds=(low-margin,high+margin)
        self._auto_fit=False
        if not np.allclose(self.ax.get_ylim(),bounds,rtol=1e-12,atol=1e-12):
            self.ax.set_ylim(*bounds);self.background=None

    def set_layers(self,generations,focus_data):
        self.generation_lines.set_visible(generations)
        self.focus_data=focus_data
        self.legend()
        if hasattr(self,'_data_bounds'):self._update_bounds(force=True)
        self.render_line()

    def prediction(self,tree,x):
        ordered=np.linspace(float(min(x)),float(max(x)),300)
        self.line.set_data(ordered,tree.evaluate(ordered))
        self._update_bounds();self.render_line()

    def finish_comparison(self):
        self._update_bounds(force=True);self.render_line()

    def compare(self,history,x):
        if not history:return
        grid=np.linspace(float(min(x)),float(max(x)),96)
        segments=[]
        for record in history:
            # Unchanged champions across generations share cached geometry.
            if record.tree not in self._curve_cache:
                self._curve_cache[record.tree]=np.column_stack((grid,record.tree.evaluate(grid)))
            segments.append(self._curve_cache[record.tree])
        self.generation_lines.set_segments(segments)
        self.generation_lines.set_colors([GENERATION_COLORS[r.generation%len(GENERATION_COLORS)] for r in history])
        self.prediction(history[-1].tree,x)


class PopulationPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.summary=QLabel('Sin generaciones · inicia una búsqueda');self.summary.setObjectName('subtitle')
        self.summary.setWordWrap(True);layout.addWidget(self.summary)
        self.table=QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(['Generación','MSE','NMSE','Nodos','Mejor expresión'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeMode.Stretch)
        for i,width in enumerate([90,85,85,50]):self.table.setColumnWidth(i,width)
        self.table.setMinimumWidth(260)
        self.table.setToolTip('Una mejor propuesta por generación. La generación 0 es la población inicial. Errores de entrenamiento.')
        layout.addWidget(self.table)
        self.copy_button=QPushButton('Copiar expresión seleccionada')
        self.copy_button.setToolTip('Copia la fórmula NumPy con precisión completa y protecciones numéricas')
        self.copy_button.clicked.connect(self.copy_selected);layout.addWidget(self.copy_button)
        self.table.currentCellChanged.connect(lambda *args:self.copy_button.setEnabled(self.table.currentRow()>=0))
        self.reset()

    def reset(self):
        self.snapshot=None;self.history={};self._dirty=set()
        self._row_generations=[];self._displayed={}
        self.table.setRowCount(0);self.copy_button.setEnabled(False)
        self.summary.setText('Sin generaciones · inicia una búsqueda')

    @property
    def records(self):
        return tuple(self.history[g] for g in sorted(self.history))

    def record(self,snapshot):
        record=GenerationBest(snapshot.generation,snapshot.tree,snapshot.mse,snapshot.nmse,snapshot.r2)
        self.snapshot=snapshot
        if self.history.get(record.generation)!=record:
            self.history[record.generation]=record;self._dirty.add(record.generation)

    def copy_selected(self):
        row=self.table.currentRow()
        if not 0<=row<len(self._row_generations):return
        record=self._displayed[self._row_generations[row]]
        QApplication.clipboard().setText('y = '+record.tree.to_python())

    def set_snapshot(self,snapshot):
        self.record(snapshot)
        self.summary.setText(f'Generación actual {snapshot.generation} · {len(self.history)} propuestas · 0: población inicial · errores de entrenamiento')
        self._render_table()

    def _render_table(self):
        if not self._dirty:return
        order=sorted(self.history)
        bar=self.table.verticalScrollBar();scroll=bar.value();follow=scroll==bar.maximum()
        selected=self.table.currentRow()
        selected_generation=self._row_generations[selected] if 0<=selected<len(self._row_generations) else None
        reordered=order[:len(self._row_generations)]!=self._row_generations
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(order))
            for row,generation in enumerate(order):
                if not reordered and generation not in self._dirty:continue
                record=self.history[generation]
                values=(str(generation),f'{record.mse:.5g}',f'{record.nmse:.5g}',str(record.tree.size),str(record.tree))
                for column,value in enumerate(values):
                    item=QTableWidgetItem(value);item.setToolTip(value)
                    if column==0:item.setForeground(QColor(GENERATION_COLORS[generation%len(GENERATION_COLORS)]))
                    self.table.setItem(row,column,item)
                self._displayed[generation]=record
            self._row_generations=order
            if reordered and selected_generation in order:self.table.setCurrentCell(order.index(selected_generation),4)
            self.table.scrollToBottom() if follow else bar.setValue(scroll)
        finally:self.table.setUpdatesEnabled(True)
        self.copy_button.setEnabled(self.table.currentRow()>=0)
        self._dirty.clear()
