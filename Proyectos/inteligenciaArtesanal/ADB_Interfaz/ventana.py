"""Contenedor general: selección de grafo y pestañas de interfaces independientes."""
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from .informes import GrabadorInforme
from exportacion.informes import RAIZ_INFORMES, crear_carpetas
from PyQt6.QtWidgets import QCheckBox, QProgressBar, QPushButton, QComboBox, QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from algoritmos.registro import ALGORITMOS
from modelos.grafos import cargar_grafos
from .registro import INTERFACES


class VentanaGrafo(QMainWindow):
    def __init__(self, algoritmos=ALGORITMOS, interfaces=None, capturar=True):
        super().__init__()
        self.setWindowTitle('Rutas · Algoritmos')
        self.resize(1440, 920)
        self.setMinimumSize(1000, 760)
        self.grafos = cargar_grafos()
        self.grafo = self.grafos['positivo']
        self._indice_anterior = 0
        self.algoritmos = tuple(algoritmos)
        fabricas = INTERFACES if interfaces is None else interfaces
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        barra = QHBoxLayout()
        titulo = QLabel('RUTAS / GRAFOS')
        titulo.setObjectName('titulo')
        barra.addWidget(titulo)
        barra.addSpacing(20)
        barra.addWidget(QLabel('Datos'))
        self.selector_grafo = QComboBox()
        self.selector_grafo.addItem('Original · con negativos', 'original')
        self.selector_grafo.addItem('Pesos positivos', 'positivo')
        self.selector_grafo.setCurrentIndex(1)
        barra.addWidget(self.selector_grafo)
        barra.addStretch()
        self.capturar = QCheckBox('Capturas + PDF por paso')
        self.capturar.setChecked(capturar)
        self.capturar.setToolTip('Captura todos los eventos. Si el PDF de esta ejecución ya existe, omite el cálculo.')
        barra.addWidget(self.capturar)
        abrir = QPushButton('Abrir informes')
        crear_carpetas()
        abrir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(RAIZ_INFORMES))))
        barra.addWidget(abrir)
        layout.addLayout(barra)
        self.pestanas = QTabWidget()
        for algoritmo in self.algoritmos:
            interfaz = fabricas[algoritmo.identificador](self.grafo, algoritmo)
            interfaz.mensaje.connect(lambda texto: self.statusBar().showMessage(texto, 5000))
            if hasattr(interfaz, 'reproductor'):
                interfaz.informe = GrabadorInforme(interfaz)
                interfaz.informe.habilitado = capturar
                interfaz.informe.cambiado.connect(
                    lambda texto, actual, total, vista=interfaz: self.progreso_informe(vista, texto, actual, total))
            self.pestanas.addTab(interfaz, algoritmo.nombre)
        layout.addWidget(self.pestanas, 1)
        inferior = QHBoxLayout()
        self.estado_informe = QLabel('Capturas y PDF listos · cuatro carpetas en informes/')
        self.barra_informe = QProgressBar()
        self.barra_informe.setMaximumWidth(240)
        self.barra_informe.setRange(0, 1)
        self.barra_informe.setValue(0)
        self.cancelar_grabacion = QPushButton('Cancelar grabación')
        self.cancelar_grabacion.clicked.connect(lambda: self.interfaz_actual.cancelar_informe())
        inferior.addWidget(self.estado_informe, 1)
        inferior.addWidget(self.barra_informe)
        inferior.addWidget(self.cancelar_grabacion)
        layout.addLayout(inferior)
        self.capturar.toggled.connect(self.cambiar_capturas)
        self.selector_grafo.currentIndexChanged.connect(self.cambiar_grafo)
        self.pestanas.currentChanged.connect(self.cambiar_interfaz)
        self.statusBar().showMessage('Rueda: zoom · Arrastrar: desplazar · Grafo dirigido · Ejemplo alcanzable: 10 → 17')

    def cambiar_capturas(self, habilitado):
        for indice in range(self.pestanas.count()):
            informe = self.pestanas.widget(indice).informe
            if informe:
                informe.cancelar()
                informe.habilitado = habilitado
        self.estado_informe.setText('Capturas activadas' if habilitado else 'Solo visualización · sin capturas')

    def progreso_informe(self, vista, texto, actual, total):
        if vista is self.interfaz_actual:
            self.estado_informe.setText(texto)
            self.estado_informe.setToolTip(str(vista.informe.ruta_pdf or ''))
            self.barra_informe.setRange(0, max(1, total))
            self.barra_informe.setValue(actual)

    @property
    def interfaz_actual(self):
        return self.pestanas.currentWidget()

    def cambiar_grafo(self, *_):
        self.grafo = self.grafos[self.selector_grafo.currentData()]
        for indice in range(self.pestanas.count()):
            self.pestanas.widget(indice).cargar_grafo(self.grafo)

    def cambiar_interfaz(self, indice):
        anterior = self.pestanas.widget(self._indice_anterior)
        if anterior is not None:
            anterior.detener()
        self._indice_anterior = indice
        self.statusBar().showMessage(f'{self.algoritmos[indice].nombre} · Rueda: zoom · Arrastrar: desplazar')
        preferido = self.algoritmos[indice].grafo_preferido
        if preferido is not None:
            self.selector_grafo.setCurrentIndex(self.selector_grafo.findData(preferido))

    def closeEvent(self, event):
        for indice in range(self.pestanas.count()):
            self.pestanas.widget(indice).detener()
        super().closeEvent(event)
