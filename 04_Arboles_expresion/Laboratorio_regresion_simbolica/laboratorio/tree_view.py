import math
from PyQt6.QtCore import Qt, QPointF, QVariantAnimation, QSequentialAnimationGroup, QEasingCurve
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QPainterPath, QFont
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsSimpleTextItem

GREEN='#39FF88'; TEXT='#E4FBEA'

class TreeView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QColor('#07130D'))
        self.setFrameShape(self.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.nodes={}; self.edges={}; self.positions={}; self.tree=None; self.animation=None
        self.speed=1.; self.zoom=1.; self._revision=0; self._fitting=False
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.tree: self.fit_tree()

    def wheelEvent(self,event):
        factor=1.15 if event.angleDelta().y()>0 else 1/1.15
        if .12<self.zoom*factor<6:
            self.scale(factor,factor); self.zoom*=factor
        event.accept()

    def fit_tree(self):
        if self._fitting or not self.nodes: return
        self._fitting=True
        try:
            self.fitInView(self.scene().itemsBoundingRect().adjusted(-55,-55,55,55),Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom=self.transform().m11()
        finally: self._fitting=False

    def stop(self):
        self._revision+=1
        animation=self.animation; self.animation=None
        if animation: animation.stop(); animation.deleteLater()
        for path,item in self.nodes.items():
            item.setPos(self.positions[path]); item.setScale(1.)
            item.setPen(QPen(QColor(GREEN),1.8))
        for path,edge in self.edges.items():
            edge.setPen(QPen(QColor('#268954'),2))
            edge.setPath(self.curve(self.positions[path[:-1]],self.positions[path]))

    def clear_tree(self):
        self.stop(); self.tree=None
        self.nodes={}; self.edges={}; self.positions={}
        self.scene().clear(); self.scene().setSceneRect(0,0,1,1)

    def closeEvent(self,event):
        self.stop(); super().closeEvent(event)

    def show_tree(self,tree,animate=False):
        self.clear_tree(); self.tree=tree
        cursor=[0]
        def layout(n,path=(),depth=0):
            if n.children:
                xs=[layout(c,path+(i,),depth+1) for i,c in enumerate(n.children)]; x=sum(xs)/len(xs)
            else: x=cursor[0]*78; cursor[0]+=1
            self.positions[path]=QPointF(x,depth*100)
            return x
        layout(tree)
        for path,pos in self.positions.items():
            if path:
                edge=self.scene().addPath(self.curve(self.positions[path[:-1]],pos),QPen(QColor('#268954'),2))
                self.edges[path]=edge
        for path,pos in self.positions.items():
            node=QGraphicsEllipseItem(-24,-24,48,48)
            node.setBrush(QBrush(QColor('#10241A'))); node.setPen(QPen(QColor(GREEN),1.8))
            node.setPos(pos); node.setZValue(2); node.setToolTip(str(tree.at(path)))
            label=QGraphicsSimpleTextItem(tree.at(path).label,node)
            label.setFont(QFont('Sans Serif',11,QFont.Weight.DemiBold)); label.setBrush(QColor(TEXT))
            if label.boundingRect().width()>40:
                label.setScale(40/label.boundingRect().width())
            label.setPos(-label.boundingRect().width()*label.scale()/2,-label.boundingRect().height()*label.scale()/2)
            self.scene().addItem(node); self.nodes[path]=node
        self.scene().setSceneRect(self.scene().itemsBoundingRect().adjusted(-65,-65,65,65))
        self.fit_tree()
        if animate:
            group=QSequentialAnimationGroup(self)
            for depth in range(tree.height+1):
                self.add_pulse(group,[p for p in self.nodes if len(p)==depth],GREEN,180)
            self.animation=group; group.start()

    @staticmethod
    def curve(a,b):
        p=QPainterPath(a); middle=(a.y()+b.y())/2
        p.cubicTo(QPointF(a.x(),middle),QPointF(b.x(),middle),b)
        return p

    def add_pulse(self,group,paths,color,duration=700,movement=False):
        anim=QVariantAnimation(group); anim.setDuration(max(1,int(duration/self.speed)))
        anim.setStartValue(0.); anim.setEndValue(1.); anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        revision=self._revision
        def frame(value):
            if revision!=self._revision: return
            glow=math.sin(value*math.pi)
            for path in paths:
                if path not in self.nodes: continue
                item=self.nodes[path]; item.setPen(QPen(QColor(color),2+4*glow)); item.setScale(1+.16*glow)
                if movement: item.setPos(self.positions[path]+QPointF(75*glow,-20*glow))
                if path in self.edges:
                    self.edges[path].setPen(QPen(QColor(color),2+glow))
            if movement:
                for path,edge in self.edges.items(): edge.setPath(self.curve(self.nodes[path[:-1]].pos(),self.nodes[path].pos()))
        anim.valueChanged.connect(frame); group.addAnimation(anim)

    def educational(self,before,after,path,color,callback,affected_paths=None):
        self.show_tree(before)
        group=QSequentialAnimationGroup(self)
        affected=affected_paths if affected_paths is not None else [p for p in self.nodes if p[:len(path)]==path]
        self.add_pulse(group,affected,color,1400,True)
        revision=self._revision
        def replaced():
            if revision!=self._revision: return
            self.animation=None
            self.show_tree(after)
            incoming=QSequentialAnimationGroup(self)
            self.add_pulse(incoming,[p for p in (affected_paths if affected_paths is not None else self.nodes) if p in self.nodes and (affected_paths is not None or p[:len(path)]==path)],GREEN,1100,True)
            incoming_revision=self._revision
            def complete():
                if incoming_revision!=self._revision: return
                self.animation=None; incoming.deleteLater(); callback()
            incoming.finished.connect(complete)
            self.animation=incoming; incoming.start()
            group.deleteLater()
        group.finished.connect(replaced); self.animation=group; group.start()

    def evaluate_animation(self):
        if not self.tree: return
        self.stop(); group=QSequentialAnimationGroup(self)
        for depth in range(self.tree.height,-1,-1):
            self.add_pulse(group,[p for p in self.nodes if len(p)==depth],'#00FF99',400)
        self.animation=group; group.start()

    def toggle_animation(self):
        if not self.animation: return
        if self.animation.state()==self.animation.State.Paused: self.animation.resume()
        elif self.animation.state()==self.animation.State.Running: self.animation.pause()
