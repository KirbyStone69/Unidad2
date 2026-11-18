"""Demo gráfica de N reinas basada en 1.png y 2.png.

Para N=8 se conserva el vector del libro como primer individuo inicial.
La búsqueda, el cruce OX y la mutación guiada opcional son añadidos
didácticos: las imágenes no publican estos operadores.
Cada posición es una columna; su valor es la fila, contando desde arriba.
La búsqueda genética automática es una demo añadida e independiente de a.pdf.
"""
import random
from collections import Counter

PADRE_LIBRO = [8, 3, 7, 4, 2, 5, 1, 6]
COLORES = ('#ffe2ae', '#dcd2ff')


def validar(cadena):
    if not cadena or sorted(cadena) != list(range(1, len(cadena)+1)):
        raise ValueError('La cadena debe contener los números de 1 a N sin repetir.')


def cruce_orden(padre1, padre2, inicio, fin):
    """OX: copiar [inicio:fin] y completar circularmente con el otro padre."""
    validar(padre1)
    validar(padre2)
    n = len(padre1)
    if len(padre2) != n:
        raise ValueError('Los padres deben tener el mismo tamaño.')
    if not 0 <= inicio < fin <= n:
        raise ValueError('Los cortes deben cumplir 0 <= inicio < fin <= N.')

    def hijo(primero, segundo):
        genes = [None] * n
        genes[inicio:fin] = primero[inicio:fin]
        orden = segundo[fin:] + segundo[:fin]
        segmento = set(primero[inicio:fin])
        restantes = [gen for gen in orden if gen not in segmento]
        posiciones = list(range(fin, n)) + list(range(inicio))
        for posicion, gen in zip(posiciones, restantes):
            genes[posicion] = gen
        return genes

    return hijo(padre1, padre2), hijo(padre2, padre1)


def casillas(cadena):
    """Coordenadas (columna, fila), ambas desde cero para dibujar."""
    validar(cadena)
    return [(columna, fila-1) for columna, fila in enumerate(cadena)]


def conflictos(cadena):
    """Pares de reinas que se atacan en diagonal (filas/columnas son únicas)."""
    validar(cadena)
    n = len(cadena)
    return [(i, j) for i in range(n) for j in range(i+1, n)
            if abs(cadena[i]-cadena[j]) == j-i]


def mutar(cadena, rng, probabilidad=0.5, guiada=False):
    """Intercambiar dos posiciones sin repetir ni perder filas."""
    hijo = cadena.copy()
    if len(hijo) > 1 and rng.random() < probabilidad:
        if guiada:
            return intercambio_guiado(hijo, rng)
        a, b = rng.sample(range(len(hijo)), 2)
        hijo[a], hijo[b] = hijo[b], hijo[a]
    return hijo


def contar_conflictos(cadena):
    """Mismo número de pares, contando diagonales en O(N)."""
    diagonales = Counter(i-fila for i, fila in enumerate(cadena))
    opuestas = Counter(i+fila for i, fila in enumerate(cadena))
    return sum(cantidad*(cantidad-1)//2 for cantidad in diagonales.values()) + sum(
        cantidad*(cantidad-1)//2 for cantidad in opuestas.values())


def intercambio_guiado(cadena, rng):
    """Mutación añadida opcional: elegir reina atacada y su mejor intercambio.

    Evalúa el cambio de pares mediante las diagonales afectadas; no construye
    una solución externa ni cambia la representación por permutaciones.
    """
    d = Counter(i-f for i, f in enumerate(cadena))
    u = Counter(i+f for i, f in enumerate(cadena))
    atacadas = [i for i, f in enumerate(cadena) if d[i-f] > 1 or u[i+f] > 1]
    if not atacadas:
        return cadena.copy()
    a = rng.choice(atacadas)
    mejor, candidatos = float('inf'), []
    for b in range(len(cadena)):
        if a == b:
            continue
        cambio = 0
        for cuentas, signo in ((d, -1), (u, 1)):
            delta = Counter()
            delta[a+signo*cadena[a]] -= 1
            delta[b+signo*cadena[b]] -= 1
            delta[a+signo*cadena[b]] += 1
            delta[b+signo*cadena[a]] += 1
            cambio += sum(v*(2*cuentas[k]+v-1)//2 for k, v in delta.items())
        if cambio < mejor:
            mejor, candidatos = cambio, [b]
        elif cambio == mejor:
            candidatos.append(b)
    b = rng.choice(candidatos)
    hijo = cadena.copy()
    hijo[a], hijo[b] = hijo[b], hijo[a]
    return hijo


class BusquedaReinas:
    """Población de 64, torneo de 3, OX, mutación 0.5 y dos élites.

    Para N>8, la mutación guiada opcional está activada por defecto.
    """
    def __init__(self, rng=None, n=8, guiada=None):
        if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n in (2, 3):
            raise ValueError("Usa N=1 o N≥4: para 2 y 3 no existe solución.")
        self.n = n
        self.guiada = n > 8 if guiada is None else guiada
        self.rng = rng if rng is not None else random.Random()
        primero = PADRE_LIBRO.copy() if n == 8 else self.rng.sample(range(1, n+1), n)
        self.poblacion = [primero] + [self.rng.sample(range(1, n+1), n) for _ in range(63)]
        self.generacion = 0
        self.solucion = None
        p1, p2 = self.poblacion[:2]
        a, b = sorted(self.rng.sample(range(self.n+1), 2))
        h1, h2 = cruce_orden(p1, p2, a, b)
        self.escena = (p1, p2, h1, h2, a, b)
        self._comprobar()

    def _comprobar(self):
        for cadena in self.escena[:4]:
            if contar_conflictos(cadena) == 0:
                self.solucion = cadena.copy()
                break

    def paso(self, continuar=False):
        if self.solucion is not None and not continuar:
            return
        self.solucion = None
        aptitud = contar_conflictos
        ordenada = sorted(self.poblacion, key=aptitud)
        nuevos = [cadena.copy() for cadena in ordenada[:2]]
        mejor = float('inf')
        for pareja in range(31):
            # Un ganador ya presente también debe aparecer en los tableros.
            p1 = ordenada[0] if pareja == 0 else min(self.rng.sample(self.poblacion, 3), key=aptitud)
            p2 = min(self.rng.sample(self.poblacion, 3), key=aptitud)
            a, b = sorted(self.rng.sample(range(self.n+1), 2))
            h1, h2 = cruce_orden(p1, p2, a, b)
            h1, h2 = mutar(h1, self.rng, guiada=self.guiada), mutar(h2, self.rng, guiada=self.guiada)
            nuevos.extend((h1, h2))
            puntuacion = min(map(aptitud, (p1, p2, h1, h2)))
            if puntuacion < mejor:
                mejor = puntuacion
                self.escena = (p1, p2, h1, h2, a, b)
        self.poblacion = nuevos
        self.generacion += 1
        self._comprobar()


# PyQt6 solo dibuja la interfaz; las operaciones genéticas siguen siendo manuales.
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QScrollArea, QScrollBar, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget,
)


class SecuenciaReinas(QWidget):
    """Fila de genes coloreados, sin crear un widget por número."""
    def __init__(self):
        super().__init__()
        self.cadena = []
        self.colores = []
        self.inicio = self.fin = 0
        self.paso = 30
        self.setFixedHeight(29)

    def actualizar(self, cadena, colores, inicio, fin):
        self.cadena, self.colores = cadena, colores
        self.inicio, self.fin = inicio, fin
        self.paso = max(28, len(str(len(cadena)))*8+12)
        self.setFixedWidth(len(cadena)*self.paso)
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont('DejaVu Sans Mono', 9))
        primero = max(0, evento.rect().left()//self.paso)
        ultimo = min(len(self.cadena), evento.rect().right()//self.paso+1)
        for i in range(primero, ultimo):
            rect = QRectF(i*self.paso+2, 2, self.paso-4, self.height()-5)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(self.colores[i]))
            p.drawRoundedRect(rect, 5, 5)
            p.setPen(QColor('#23334a'))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self.cadena[i]))
            if self.inicio <= i < self.fin:
                p.setPen(QPen(QColor('#4c72d9'), 2))
                p.drawLine(rect.bottomLeft(), rect.bottomRight())


class TableroReinas(QWidget):
    """Un solo tablero cuadrado que ocupa el espacio disponible, sin zoom manual."""
    detalle = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cadena = []
        self.atacadas = set()
        self.cache = None
        self.clave_cache = None
        self.casilla_hover = None
        self.setMouseTracking(True)
        self.setMinimumSize(130, 130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar(self, cadena):
        self.cadena = cadena.copy()
        d = Counter(i-f for i, f in enumerate(cadena))
        u = Counter(i+f for i, f in enumerate(cadena))
        self.atacadas = {i for i, f in enumerate(cadena) if d[i-f] > 1 or u[i+f] > 1}
        self.update()

    def rect_tablero(self):
        lado = max(1, int(min(self.width(), self.height())-44))
        return QRectF((self.width()-lado)/2, (self.height()-lado)/2, lado, lado)

    def paintEvent(self, evento):
        if not self.cadena:
            return
        p = QPainter(self)
        rect, n = self.rect_tablero(), len(self.cadena)
        lado = rect.width()/n
        clave = (n, int(rect.width()))
        if clave != self.clave_cache:
            self.cache = QPixmap(clave[1], clave[1])
            self.cache.fill(QColor('#edf2f7'))
            fondo = QPainter(self.cache)
            for fila in range(n):
                for col in range((fila+1)%2, n, 2):
                    fondo.fillRect(QRectF(col*lado, fila*lado, lado, lado), QColor('#b9c9da'))
            fondo.end()
            self.clave_cache = clave
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#dfe7ef'))
        p.drawRoundedRect(rect.adjusted(-3, -1, 3, 5), 9, 9)
        borde = QPainterPath()
        borde.addRoundedRect(rect, 6, 6)
        p.save()
        p.setClipPath(borde)
        p.drawPixmap(int(rect.left()), int(rect.top()), self.cache)
        if self.casilla_hover is not None:
            col, fila = self.casilla_hover
            p.fillRect(QRectF(rect.left()+col*lado, rect.top()+fila*lado, lado, lado), QColor(65, 110, 220, 65))
        for col, fila in enumerate(self.cadena):
            x, y = rect.left()+(col+.5)*lado, rect.top()+(fila-.5)*lado
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#dc6575' if col in self.atacadas else '#147d73'))
            if lado < 14:
                radio = max(.65, lado*.33)
                p.drawEllipse(QRectF(x-radio, y-radio, radio*2, radio*2))
            else:
                p.save()
                p.translate(x, y)
                p.scale(lado*.72, lado*.72)
                corona = QPainterPath()
                corona.moveTo(-.38, .25)
                for a, b in ((-.45, -.25), (-.18, -.08), (0, -.42), (.18, -.08), (.45, -.25), (.38, .25)):
                    corona.lineTo(a, b)
                corona.closeSubpath()
                p.drawPath(corona)
                p.drawRoundedRect(QRectF(-.4, .3, .8, .13), .04, .04)
                for a, b in ((-.45, -.3), (0, -.46), (.45, -.3)):
                    p.drawEllipse(QRectF(a-.065, b-.065, .13, .13))
                p.restore()
        p.restore()
        p.setPen(QColor('#72859a'))
        p.setFont(QFont('DejaVu Sans', 8))
        salto = 1 if n <= 16 else max(1, n//10)
        for i in range(n):
            if i == 0 or i == n-1 or (i+1)%salto == 0:
                if lado >= 8 or i in (0, n-1):
                    p.drawText(QRectF(rect.left()+i*lado-8, rect.top()-20, lado+16, 16), Qt.AlignmentFlag.AlignCenter, str(i+1))
                    p.drawText(QRectF(rect.left()-24, rect.top()+i*lado-4, 20, lado+8), Qt.AlignmentFlag.AlignCenter, str(i+1))

    def mouseMoveEvent(self, evento):
        rect = self.rect_tablero()
        pos = evento.position()
        if self.cadena and rect.contains(pos):
            n = len(self.cadena)
            col = min(n-1, int((pos.x()-rect.left())*n/rect.width()))
            fila = min(n-1, int((pos.y()-rect.top())*n/rect.height()))
            self.casilla_hover = (col, fila)
            self.detalle.emit(f'Columna {col+1} · fila {fila+1} | Reina de esta columna: fila {self.cadena[col]}')
        else:
            self.casilla_hover = None
        self.update()

    def leaveEvent(self, evento):
        self.casilla_hover = None
        self.detalle.emit('Cada posición es una columna; su número indica la fila desde arriba.')
        self.update()


ESTILO_REINAS = """
QMainWindow, QWidget#raiz { background: #101b2d; }
QWidget { color: #e9eef7; font-family: 'DejaVu Sans'; font-size: 12px; }
QLabel { background: transparent; }
QLabel#titulo { font-size: 25px; font-weight: 700; }
QLabel#subtitulo { color: #91a4be; font-size: 11px; }
QFrame#controles, QFrame#estadistica { background: #19283e; border: 1px solid #293a53; border-radius: 10px; }
QLabel#dato { font-size: 20px; font-weight: 700; color: #a4e5d4; }
QLabel#etiqueta { font-size: 10px; color: #91a4be; }
QFrame#panel { background: #f8fafc; border: 1px solid #e1e8f0; border-radius: 12px; }
QFrame#panel QLabel { color: #30425b; }
QLabel#seccion { font-size: 13px; font-weight: 700; }
QLabel#leyenda { color: #6f8198; font-size: 10px; }
QLabel#estado { color: #a4e5d4; background: #203e46; padding: 7px 12px; border-radius: 8px; font-weight: 600; }
QLabel#error { color: #ffaeb7; }
QSpinBox { background: #101b2d; border: 1px solid #405574; border-radius: 6px; padding: 7px; min-width: 64px; }
QSpinBox:focus { border-color: #7abfb5; }
QPushButton { background: #294361; border: 0; padding: 9px 15px; border-radius: 7px; font-weight: 600; }
QPushButton:hover { background: #365778; }
QPushButton#principal { color: #0f302f; background: #8fe1cd; }
QPushButton#principal:hover { background: #b4f0e1; }
QPushButton:disabled { color: #7e91aa; background: #23334a; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #7c92b0; border-radius: 3px; background: #101b2d; }
QCheckBox::indicator:checked { background: #8fe1cd; border: 2px solid #e1fff5; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:horizontal { background: #e7edf4; height: 9px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #9eafc3; min-width: 30px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
"""


class VentanaReinas(QMainWindow):
    def __init__(self, n=100):
        super().__init__()
        self.busqueda = BusquedaReinas(n=n)
        self.setWindowTitle('N reinas · laboratorio genético')
        self.setMinimumSize(700, 420)
        self.resize(1100, 880)
        self.setStyleSheet(ESTILO_REINAS)
        raiz = QWidget()
        raiz.setObjectName('raiz')
        self.setCentralWidget(raiz)
        layout = QVBoxLayout(raiz)
        self.distribucion = layout
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)
        cabecera = QHBoxLayout()
        titulos = QVBoxLayout()
        titulo = QLabel('N reinas')
        titulo.setObjectName('titulo')
        self.titulo = titulo
        subtitulo = QLabel('Selección, cruce y mutación. Una solución, paso a paso.')
        subtitulo.setObjectName('subtitulo')
        self.subtitulo = subtitulo
        titulos.addWidget(titulo)
        titulos.addWidget(subtitulo)
        cabecera.addLayout(titulos)
        cabecera.addStretch()
        self.estado = QLabel('BUSCANDO')
        self.estado.setObjectName('estado')
        cabecera.addWidget(self.estado)
        layout.addLayout(cabecera)
        controles = QFrame()
        controles.setObjectName('controles')
        fila = QHBoxLayout(controles)
        self.fila_controles = fila
        fila.setContentsMargins(12, 9, 12, 9)
        fila.addWidget(QLabel('Tamaño N × N'))
        self.tamano = QSpinBox()
        self.tamano.setRange(1, 1000)
        self.tamano.setValue(n)
        self.tamano.setToolTip('N reinas en N filas y N columnas. N=1 o N≥4.')
        fila.addWidget(self.tamano)
        iniciar = QPushButton('Iniciar / reiniciar')
        iniciar.setObjectName('principal')
        iniciar.clicked.connect(self.reiniciar)
        fila.addWidget(iniciar)
        self.pausa = QPushButton('Pausar')
        self.pausa.setMinimumWidth(100)
        self.pausa.clicked.connect(self.alternar_pausa)
        fila.addWidget(self.pausa)
        fila.addStretch()
        self.guiada = QCheckBox('Mutación guiada')
        self.guiada.setChecked(n > 8)
        self.guiada.setToolTip('Se aplica al iniciar. Busca el mejor intercambio de filas para una reina atacada.')
        fila.addWidget(self.guiada)
        layout.addWidget(controles)
        self.error = QLabel('')
        self.error.setObjectName('error')
        self.error.hide()
        layout.addWidget(self.error)
        estadisticas = QHBoxLayout()
        self.datos = []
        self.tarjetas = []
        for texto in ('GENERACIÓN', 'PARES EN CONFLICTO', 'CONFLICTOS DE LAS DOS ÉLITES'):
            card = QFrame()
            card.setObjectName('estadistica')
            interior = QVBoxLayout(card)
            interior.setContentsMargins(12, 7, 12, 7)
            etiqueta = QLabel(texto)
            etiqueta.setObjectName('etiqueta')
            valor = QLabel('0')
            valor.setObjectName('dato')
            interior.addWidget(etiqueta)
            interior.addWidget(valor)
            self.datos.append(valor)
            estadisticas.addWidget(card, 1)
            self.tarjetas.append(card)
        layout.addLayout(estadisticas)
        self.resumen = QLabel('')
        self.resumen.setStyleSheet('color: #a4e5d4; font-weight: 600;')
        self.resumen.hide()
        layout.addWidget(self.resumen)
        panel = QFrame()
        panel.setObjectName('panel')
        genes = QVBoxLayout(panel)
        self.distribucion_genes = genes
        genes.setContentsMargins(12, 9, 12, 9)
        genes.setSpacing(3)
        encabezado = QHBoxLayout()
        seccion = QLabel('SECUENCIAS GENÉTICAS')
        seccion.setObjectName('seccion')
        encabezado.addWidget(seccion)
        encabezado.addStretch()
        leyenda = QLabel('Naranja / azul: origen  ·  Verde: mutación  ·  Subrayado: cruce')
        leyenda.setObjectName('leyenda')
        self.leyenda = leyenda
        encabezado.addWidget(leyenda)
        genes.addLayout(encabezado)
        self.secuencias, self.areas, self.errores = [], [], []
        self.desplazamiento = QScrollBar(Qt.Orientation.Horizontal)
        for nombre in ('Padre 1', 'Padre 2', 'Hijo 1', 'Hijo 2'):
            fila = QHBoxLayout()
            etiqueta = QLabel(nombre)
            etiqueta.setFixedWidth(58)
            fila.addWidget(etiqueta)
            area = QScrollArea()
            area.setFixedHeight(29)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            secuencia = SecuenciaReinas()
            area.setWidget(secuencia)
            area.horizontalScrollBar().rangeChanged.connect(self.sincronizar_rango)
            self.desplazamiento.valueChanged.connect(area.horizontalScrollBar().setValue)
            fila.addWidget(area, 1)
            errores = QLabel('')
            errores.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            errores.setFixedWidth(85)
            fila.addWidget(errores)
            genes.addLayout(fila)
            self.secuencias.append(secuencia)
            self.areas.append(area)
            self.errores.append(errores)
        genes.addWidget(self.desplazamiento)
        layout.addWidget(panel)
        panel_tablero = QFrame()
        panel_tablero.setObjectName('panel')
        inferior = QVBoxLayout(panel_tablero)
        inferior.setContentsMargins(12, 9, 12, 7)
        encabezado_tablero = QHBoxLayout()
        self.info_tablero = QLabel('MEJOR TABLERO ACTUAL')
        self.info_tablero.setObjectName('seccion')
        encabezado_tablero.addWidget(self.info_tablero)
        encabezado_tablero.addStretch()
        self.dimension = QLabel(f'{n} × {n}  ·  {n} reinas')
        self.dimension.setObjectName('leyenda')
        encabezado_tablero.addWidget(self.dimension)
        inferior.addLayout(encabezado_tablero)
        self.tablero = TableroReinas()
        inferior.addWidget(self.tablero, 1)
        self.detalle = QLabel('Cada posición es una columna; su número indica la fila desde arriba.')
        self.detalle.setObjectName('leyenda')
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inferior.addWidget(self.detalle)
        self.tablero.detalle.connect(self.detalle.setText)
        layout.addWidget(panel_tablero, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.avanzar)
        self.mostrar()
        self.compacto = None
        self.ajustar_densidad()
        if self.busqueda.solucion is None:
            self.timer.start()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        if hasattr(self, 'compacto'):
            self.ajustar_densidad()

    def ajustar_densidad(self):
        compacto = self.height() < 680
        if self.compacto == compacto:
            return
        self.compacto = compacto
        self.subtitulo.setVisible(not compacto)
        self.leyenda.setVisible(not compacto)
        self.resumen.setVisible(compacto)
        for tarjeta in self.tarjetas:
            tarjeta.setVisible(not compacto)
        self.titulo.setStyleSheet('font-size: 20px; font-weight: 700;' if compacto else '')
        margenes = (12, 8, 12, 8) if compacto else (18, 14, 18, 14)
        self.distribucion.setContentsMargins(*margenes)
        self.distribucion.setSpacing(5 if compacto else 10)
        if compacto:
            self.fila_controles.setContentsMargins(8, 4, 8, 4)
            self.distribucion_genes.setContentsMargins(9, 5, 9, 5)
        else:
            self.fila_controles.setContentsMargins(12, 9, 12, 9)
            self.distribucion_genes.setContentsMargins(12, 9, 12, 9)
        self.distribucion_genes.setSpacing(1 if compacto else 3)
        for area, secuencia in zip(self.areas, self.secuencias):
            area.setFixedHeight(22 if compacto else 29)
            secuencia.setFixedHeight(22 if compacto else 29)

    def sincronizar_rango(self, *args):
        maximo = max((area.horizontalScrollBar().maximum() for area in self.areas), default=0)
        self.desplazamiento.setRange(0, maximo)

    def reiniciar(self):
        try:
            nueva = BusquedaReinas(n=self.tamano.value(), guiada=self.guiada.isChecked())
        except ValueError as error:
            self.error.setText(str(error))
            self.error.show()
            return
        self.timer.stop()
        self.error.hide()
        self.busqueda = nueva
        self.desplazamiento.setValue(0)
        self.pausa.setText('Pausar')
        self.mostrar()
        if nueva.solucion is None:
            self.timer.start()

    def alternar_pausa(self):
        if self.busqueda.solucion is not None:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.pausa.setText('Continuar')
            self.estado.setText('EN PAUSA')
        else:
            self.timer.start()
            self.pausa.setText('Pausar')
            self.estado.setText('BUSCANDO')

    def avanzar(self):
        if self.busqueda.solucion is not None:
            self.timer.stop()
            return
        self.busqueda.paso()
        self.mostrar()

    def mostrar(self):
        b = self.busqueda
        cadenas, (inicio, fin) = b.escena[:4], b.escena[4:]
        antes = cruce_orden(*cadenas[:2], inicio, fin)
        for i, cadena in enumerate(cadenas):
            colores = []
            for j, gen in enumerate(cadena):
                origen = i % 2 if i < 2 or inicio <= j < fin else 1-i % 2
                color = ('#f4d4ac', '#cbdcf8')[origen]
                if i >= 2 and gen != antes[i-2][j]:
                    color = '#b8e6d3'
                colores.append(color)
            self.secuencias[i].actualizar(cadena, colores, inicio, fin)
            self.errores[i].setText(f'{contar_conflictos(cadena)} conflictos')
        elites = sorted(b.poblacion, key=contar_conflictos)[:2]
        mejor = b.solucion if b.solucion is not None else min([*elites, *cadenas], key=contar_conflictos)
        self.tablero.actualizar(mejor)
        self.datos[0].setText(str(b.generacion))
        self.datos[1].setText(str(contar_conflictos(mejor)))
        self.datos[2].setText(' / '.join(str(contar_conflictos(e)) for e in elites))
        self.resumen.setText(f'Generación {b.generacion}   ·   {contar_conflictos(mejor)} conflictos   ·   Élite: {self.datos[2].text()}')
        self.dimension.setText(f'{b.n} × {b.n}  ·  {b.n} reinas')
        terminado = b.solucion is not None
        self.pausa.setEnabled(not terminado)
        self.estado.setText('SOLUCIÓN ENCONTRADA' if terminado else 'BUSCANDO')
        self.info_tablero.setText('TABLERO GANADOR' if terminado else 'MEJOR TABLERO ACTUAL')
        if terminado:
            self.timer.stop()
        self.sincronizar_rango()

    def closeEvent(self, evento):
        self.timer.stop()
        evento.accept()


def main():
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ventana = VentanaReinas()
    pantalla = app.primaryScreen().availableGeometry()
    ventana.resize(min(1100, pantalla.width()), min(880, pantalla.height()))
    ventana.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
