"""A*: dibujo común, tabla g/h/f y controles de reproducción propios."""
import math
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QHeaderView, QHBoxLayout, QLabel,
    QPushButton, QSlider, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QMessageBox,
)
from modelos.grafos import obtener_adyacencia, tiene_negativos
from ...base import InterfazAlgoritmo
from ...celebracion import ParpadeoRuta
from ...escena import EscenaGrafo, VistaGrafo
from ...recorrido import RecorridoRuta
from ...reproductor import Reproductor
from .configuracion import ConfiguracionAEstrella


def numero(valor):
    if math.isinf(valor):
        return '∞' if valor > 0 else '−∞'
    return f'{valor:.8g}'


class InterfazAEstrella(InterfazAlgoritmo):
    def __init__(self, grafo, algoritmo, parent=None):
        super().__init__(parent)
        self.grafo = grafo
        self.algoritmo = algoritmo
        self.escena = EscenaGrafo(self)
        self.vista = VistaGrafo(self.escena)
        self.reproductor = Reproductor(self)
        self.celebracion = ParpadeoRuta(self)
        self.recorrido = RecorridoRuta(self.escena, self)
        self.recorrido.terminado.connect(self.celebracion.iniciar)
        self.celebracion.fase_cambiada.connect(self.escena.parpadear_ruta)
        self.construir_interfaz()
        self.conectar()
        self.escena.cargar(grafo)
        self.limpiar_panel()
        self.actualizar_compatibilidad()
        self.cambiar_velocidad(self.velocidad.value())
        QTimer.singleShot(0, self.vista.ajustar)

    def construir_interfaz(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        area = QVBoxLayout()
        barra = QHBoxLayout()
        barra.addStretch()
        for texto, accion in [('Ajustar', self.vista.ajustar),
                               ('＋', lambda: self.vista.zoom(1.2)),
                               ('−', lambda: self.vista.zoom(1 / 1.2))]:
            boton = QPushButton(texto)
            boton.clicked.connect(accion)
            barra.addWidget(boton)
        self.pesos = QCheckBox('Pesos')
        self.pesos.setChecked(True)
        barra.addWidget(self.pesos)
        area.addLayout(barra)
        area.addWidget(self.vista, 1)
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(['Nodo', 'g', 'h', 'f = g + h', 'Predecesor', 'Estado'])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setMaximumHeight(235)
        area.addWidget(self.tabla)
        layout.addLayout(area, 1)

        panel = QWidget()
        panel.setFixedWidth(330)
        controles = QVBoxLayout(panel)
        controles.setContentsMargins(4, 0, 0, 0)
        titulo = QLabel('Configuración de A*')
        titulo.setObjectName('titulo')
        controles.addWidget(titulo)
        self.configuracion = ConfiguracionAEstrella()
        controles.addWidget(self.configuracion)
        self.compatibilidad = QLabel()
        self.compatibilidad.setWordWrap(True)
        controles.addWidget(self.compatibilidad)
        self.ejecutar = QPushButton('Ejecutar y animar')
        self.debug = QPushButton('Debug · resultado directo')
        controles.addWidget(self.ejecutar)
        controles.addWidget(self.debug)
        navegacion = QHBoxLayout()
        self.atras = QPushButton('←')
        self.play = QPushButton('Reproducir')
        self.adelante = QPushButton('→')
        self.reiniciar = QPushButton('↺')
        for boton, ayuda in [(self.atras, 'Paso anterior'),
                              (self.play, 'Reproducir / pausar'),
                              (self.adelante, 'Paso siguiente'),
                              (self.reiniciar, 'Reiniciar pasos')]:
            boton.setToolTip(ayuda)
            navegacion.addWidget(boton)
        controles.addLayout(navegacion)
        controles.addWidget(QLabel('Velocidad de reproducción'))
        self.velocidad = QSlider(Qt.Orientation.Horizontal)
        self.velocidad.setRange(1, 10)
        self.velocidad.setValue(7)
        controles.addWidget(self.velocidad)
        self.estado = QLabel()
        self.estado.setObjectName('estado')
        self.conjuntos = QLabel()
        self.escala = QLabel()
        self.escala.setToolTip('h(n) = α · distancia euclidiana al destino.\n'
                               'α calibra las coordenadas del mapa a sus pesos.')
        self.comparacion = QLabel()
        self.resultado = QLabel()
        for etiqueta in (self.estado, self.conjuntos, self.escala,
                          self.comparacion, self.resultado):
            etiqueta.setWordWrap(True)
            etiqueta.setTextFormat(Qt.TextFormat.PlainText)
            controles.addWidget(etiqueta)
        controles.addStretch()
        layout.addWidget(panel)

    def conectar(self):
        self.configuracion.cambiada.connect(self.invalidar)
        self.ejecutar.clicked.connect(self.buscar)
        self.debug.clicked.connect(lambda: self.buscar(directo=True))
        self.atras.clicked.connect(self.reproductor.anterior)
        self.adelante.clicked.connect(self.reproductor.siguiente)
        self.reiniciar.clicked.connect(self.reproductor.reiniciar)
        self.play.clicked.connect(self.alternar)
        self.velocidad.valueChanged.connect(self.cambiar_velocidad)
        self.pesos.toggled.connect(self.escena.mostrar_pesos)
        self.reproductor.paso_cambiado.connect(self.mostrar_paso)
        self.reproductor.progreso.connect(self.escena.animar)
        self.reproductor.reproduciendo.connect(
            lambda activo: self.play.setText('Pausar' if activo else 'Reproducir'))

    def actualizar_compatibilidad(self):
        compatible = not tiene_negativos(self.grafo)
        self.ejecutar.setEnabled(compatible)
        self.debug.setEnabled(compatible)
        self.compatibilidad.setText('Listo para A*' if compatible else
                                    'A* requiere pesos ≥ 0. Selecciona «Pesos positivos».')

    def limpiar_panel(self):
        for boton in (self.atras, self.play, self.adelante, self.reiniciar):
            boton.setEnabled(False)
        self.estado.setText('Listo para buscar')
        self.conjuntos.setText('Abiertos: — · Cerrados: —')
        self.escala.setText('Escala α: —')
        self.comparacion.setText('Comparación del paso: —')
        self.resultado.setText('Costo final: —')
        self.tabla.setRowCount(len(self.grafo))
        for fila, nodo in enumerate(self.grafo):
            for columna, valor in enumerate((str(nodo), '—', '—', '—', '—', 'Sin descubrir')):
                self.tabla.setItem(fila, columna, QTableWidgetItem(valor))

    def invalidar(self):
        self.cancelar_informe()
        self.recorrido.detener()
        self.celebracion.detener()
        self.reproductor.limpiar()
        self.escena.representar()
        self.limpiar_panel()
        self.actualizar_compatibilidad()

    def cargar_grafo(self, grafo):
        self.detener()
        self.reproductor.limpiar()
        self.grafo = grafo
        self.escena.cargar(grafo)
        self.limpiar_panel()
        self.actualizar_compatibilidad()
        self.vista.ajustar()

    def buscar(self, directo=False):
        self.invalidar()
        if tiene_negativos(self.grafo):
            return
        try:
            parametros = self.configuracion.parametros(self.grafo)
        except ValueError as error:
            QMessageBox.warning(self, 'Nodos no válidos', str(error))
            return
        if self.reutilizar_informe(parametros):
            return
        try:
            posiciones = {nodo: datos['pixel'] for nodo, datos in self.grafo.nodes(data=True)}
            resultado = self.algoritmo.ejecutar(obtener_adyacencia(self.grafo),
                                                posiciones=posiciones, **parametros)
        except ValueError as error:
            self.estado.setText(str(error))
            return
        self.play.setEnabled(True)
        self.reiniciar.setEnabled(True)
        self.reproductor.cargar(resultado)
        if self.grabar_informe(resultado):
            return
        if directo:
            self.mostrar_resultado()
        else:
            self.reproductor.iniciar()

    def mostrar_resultado(self):
        if self.reproductor.resultado is None:
            return
        self.reproductor.pausar()
        self.reproductor.mostrar(len(self.reproductor.resultado.pasos) - 1)

    def mostrar_paso(self, indice, paso):
        self.recorrido.detener()
        self.celebracion.detener()
        self.escena.representar(paso)
        resultado = self.reproductor.resultado
        actual = str(paso.actual) if paso.actual is not None else '—'
        self.estado.setText(f'Paso {indice + 1}/{len(resultado.pasos)} · Nodo actual: {actual}')
        self.conjuntos.setText(f'Abiertos: {len(paso.abiertos)} · Cerrados: {len(paso.visitados)}')
        self.escala.setText(f'Escala α: {numero(resultado.escala)}')
        self.comparacion.setText(paso.descripcion)
        self.atras.setEnabled(indice > 0)
        self.adelante.setEnabled(indice < len(resultado.pasos) - 1)
        for fila, nodo in enumerate(self.grafo):
            estado = ('Cerrado' if nodo in paso.visitados else
                      'Abierto' if nodo in paso.abiertos else 'Sin descubrir')
            valores = (numero(paso.distancias[nodo]), numero(paso.heuristicas[nodo]),
                       numero(paso.valores_f[nodo]), str(paso.predecesores.get(nodo, '—')), estado)
            for columna, valor in enumerate(valores, start=1):
                self.tabla.item(fila, columna).setText(valor)
        if indice == len(resultado.pasos) - 1:
            if resultado.encontrado:
                self.resultado.setText(f'Costo: {numero(resultado.distancia)}\n'
                                        + ' → '.join(map(str, resultado.ruta))
                                        + f'\nNodos expandidos: {resultado.expandidos}')
                if paso.tipo == 'fin' and paso.ruta:
                    self.recorrido.iniciar(paso.aristas_ruta)
            else:
                self.resultado.setText(f'Destino inalcanzable\nNodos expandidos: {resultado.expandidos}')
        else:
            self.resultado.setText('Costo final: —')

    def alternar(self):
        if self.reproductor.timer.isActive():
            self.reproductor.pausar()
        else:
            self.recorrido.detener()
            self.celebracion.detener()
            self.reproductor.iniciar()

    def cambiar_velocidad(self, valor):
        self.reproductor.timer.setInterval(16)
        self.reproductor.duracion = 20 + (10 - valor) * 190

    def detener(self):
        self.cancelar_informe()
        self.recorrido.detener()
        self.celebracion.detener()
        self.reproductor.pausar()
