"""Partícula que recorre las aristas ganadoras antes del parpadeo final."""
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class RecorridoRuta(QObject):
    terminado = pyqtSignal()

    def __init__(self, escena, parent=None):
        super().__init__(parent)
        self.escena = escena
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.avanzar)
        self.aristas = ()
        self.fotograma = 0

    def iniciar(self, aristas):
        self.detener()
        self.aristas = tuple(aristas)
        self.fotograma = 0
        if not self.aristas:
            self.terminado.emit()
            return
        self.timer.start()
        self.avanzar()

    def avanzar(self):
        if not self.timer.isActive():
            return
        indice, fase = divmod(self.fotograma, 12)
        if indice >= len(self.aristas):
            self.detener()
            self.terminado.emit()
            return
        arco = self.aristas[indice]
        grafica = self.escena.aristas[self.escena.identificador(arco.origen, arco.destino, arco.clave)]
        progreso = 0.1 + 0.8 * fase / 11
        if grafica.origen != arco.origen:
            progreso = 1 - progreso
        self.escena.particula.setPos(grafica.item.path().pointAtPercent(progreso))
        self.escena.particula.setVisible(True)
        self.fotograma += 1

    def detener(self):
        self.timer.stop()
        if self.escena.particula is not None:
            self.escena.particula.setVisible(False)
