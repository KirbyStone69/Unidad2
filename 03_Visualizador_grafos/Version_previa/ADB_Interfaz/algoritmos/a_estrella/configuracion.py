"""Extremos y heurística de A*, independientes de los demás algoritmos."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit, QWidget
from modelos.validacion import validar_extremos


class ConfiguracionAEstrella(QWidget):
    cambiada = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        formulario = QFormLayout(self)
        self.origen = QLineEdit('10')
        self.destino = QLineEdit('17')
        self.origen.setPlaceholderText('Número del nodo origen')
        self.destino.setPlaceholderText('Número del nodo destino')
        for campo in (self.origen, self.destino):
            campo.setClearButtonEnabled(True)
            campo.textChanged.connect(lambda _: self.cambiada.emit())
        self.heuristica = QComboBox()
        self.heuristica.addItem('Euclidiana calibrada', 'euclidiana')
        self.heuristica.addItem('Cero · h = 0', 'cero')
        self.heuristica.currentIndexChanged.connect(lambda _: self.cambiada.emit())
        formulario.addRow('Origen', self.origen)
        formulario.addRow('Destino', self.destino)
        formulario.addRow('Heurística', self.heuristica)
        nota = QLabel('g: costo acumulado · h: estimación\nf = g + h · pesos ≥ 0')
        nota.setWordWrap(True)
        formulario.addRow(nota)

    def parametros(self, grafo):
        origen, destino = validar_extremos(grafo, self.origen.text(), self.destino.text())
        return {'origen': origen, 'destino': destino,
                'modo_heuristica': self.heuristica.currentData()}
