"""Búsqueda simbólica autónoma con PyQt6.

Ejecutar gr.py primero para crear gr.csv; después ejecutar este script.
Carga gr.csv junto a este archivo e inicia la búsqueda con elitismo.
Dependencias externas: numpy, matplotlib y PyQt6.
"""
import csv
import math
import operator
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import QElapsedTimer, QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import (
    QApplication, QDoubleSpinBox, QGraphicsObject, QGraphicsScene, QGraphicsView,
    QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget,
)


def vector_finito(valores):
    vector = np.array(valores, dtype=float, copy=True)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise ValueError('Se requiere una lista no vacía de números finitos.')
    return vector


@dataclass(frozen=True)
class DatosGrafica:
    x: object
    y: object
    nombre: str = 'Datos x,y'

    def __post_init__(self):
        x, y = vector_finito(self.x), vector_finito(self.y)
        if x.shape != y.shape:
            raise ValueError('x e y deben tener la misma cantidad de puntos.')
        x.setflags(write=False)
        y.setflags(write=False)
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)


def cargar_csv(ruta):
    x, y = [], []
    with Path(ruta).open(encoding='utf-8-sig', newline='') as archivo:
        muestra = archivo.read(4096)
        archivo.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=',;\t')
        except csv.Error:
            dialecto = csv.excel
        lector = csv.DictReader(archivo, dialect=dialecto)
        if lector.fieldnames is None:
            raise ValueError('El CSV está vacío. Se requieren columnas x,y.')
        nombres = {nombre.strip().lower(): nombre for nombre in lector.fieldnames}
        if 'x' not in nombres or 'y' not in nombres:
            raise ValueError('El CSV debe tener encabezados x,y.')
        for fila in lector:
            try:
                vx, vy = float(fila[nombres['x']]), float(fila[nombres['y']])
                if not np.isfinite(vx) or not np.isfinite(vy):
                    raise ValueError('Dato no finito')
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f'Valores x,y inválidos en la fila {lector.line_num}.') from error
            x.append(vx)
            y.append(vy)
    return DatosGrafica(x, y, Path(ruta).name)


def calcular_errores(esperado, predicho):
    y, pred = vector_finito(esperado), vector_finito(predicho)
    if y.shape != pred.shape:
        raise ValueError('Las predicciones deben corresponder a todos los datos.')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            sse = float(np.sum(np.square(pred - y)))
            energia = float(np.sum(np.square(y)))
            mse = sse / y.size
            nmse = sse / energia if energia != 0 else None
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('El error excede el rango numérico.') from error
    if not np.isfinite(mse) or (nmse is not None and not np.isfinite(nmse)):
        raise ValueError('El error no es finito.')
    return mse, nmse


@dataclass(frozen=True)
class Operacion:
    nombre: str
    operandos: int
    funcion: Callable[..., float]
    funcion_vectorial: Callable | None = None

    def aplicar(self, *valores):
        if len(valores) != self.operandos:
            raise ValueError(f'{self.nombre} requiere {self.operandos} operandos.')
        if not all(math.isfinite(valor) for valor in valores):
            raise ValueError('Los operandos deben ser números reales finitos.')
        try:
            resultado = self.funcion(*valores)
            if isinstance(resultado, complex) or not math.isfinite(resultado):
                raise ValueError('Resultado fuera de los números reales finitos.')
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            raise ValueError(f'{self.nombre}: operación sin resultado real finito ({error}).') from error
        return resultado


    def aplicar_vector(self, *valores):
        if len(valores) != self.operandos:
            raise ValueError(f'{self.nombre} requiere {self.operandos} operandos.')
        if not all(np.all(np.isfinite(valor)) for valor in valores):
            raise ValueError('Los operandos deben ser finitos.')
        try:
            with np.errstate(divide='raise', invalid='raise', over='raise'):
                resultado = self.funcion_vectorial(*valores)
            if not np.all(np.isfinite(resultado)):
                raise ValueError('Resultado no finito.')
        except (FloatingPointError, OverflowError, ZeroDivisionError) as error:
            raise ValueError(f'{self.nombre}: dominio inválido en los datos.') from error
        return resultado


def tangente(angulo):
    if abs(math.cos(angulo)) < 1e-12:
        raise ValueError('Tangente indefinida cerca de π/2 + kπ.')
    return math.tan(angulo)


def tangente_vectorial(angulo):
    if np.any(np.abs(np.cos(angulo)) < 1e-12):
        raise ValueError('Tangente indefinida cerca de π/2 + kπ.')
    return np.tan(angulo)


OPERACIONES_VALIDAS = {
    '+': Operacion('Suma', 2, operator.add, np.add),
    '−': Operacion('Resta', 2, operator.sub, np.subtract),
    '×': Operacion('Multiplicación', 2, operator.mul, np.multiply),
    '/': Operacion('División', 2, operator.truediv, np.divide),
    '%': Operacion('Módulo', 2, operator.mod, np.remainder),
    '^': Operacion('Potencia', 2, math.pow, np.float_power),
    '√': Operacion('Raíz cuadrada', 1, math.sqrt, np.sqrt),
    'ln': Operacion('Logaritmo natural', 1, math.log, np.log),
    'sin': Operacion('Seno', 1, math.sin, np.sin),
    'cos': Operacion('Coseno', 1, math.cos, np.cos),
    'tan': Operacion('Tangente', 1, tangente, tangente_vectorial),
}


ALTURA_MAXIMA = 5


TOLERANCIA = 1e-6


def validar_arbol(etiquetas, hijos, raiz=0, altura_maxima=None):
    """Comprobar altura, operaciones, aridad y que la estructura sea un árbol."""
    limite = ALTURA_MAXIMA if altura_maxima is None else altura_maxima
    if not isinstance(limite, int) or isinstance(limite, bool) or limite < 0:
        raise ValueError('La altura máxima debe ser un entero no negativo.')
    vistos = set()
    pendientes = [(raiz, 0)]
    altura = 0
    while pendientes:
        nodo, nivel = pendientes.pop()
        if nivel > limite:
            raise ValueError(f'El árbol supera la altura máxima de {limite}.')
        if nodo in vistos:
            raise ValueError('El árbol contiene ciclos o nodos con varios padres.')
        if nodo not in etiquetas:
            raise ValueError(f'Falta la etiqueta del nodo {nodo}.')
        vistos.add(nodo)
        altura = max(altura, nivel)
        etiqueta = etiquetas[nodo]
        descendientes = hijos.get(nodo, ())
        if etiqueta in OPERACIONES_VALIDAS:
            if len(descendientes) != OPERACIONES_VALIDAS[etiqueta].operandos:
                raise ValueError(f'Cantidad incorrecta de operandos en {etiqueta}.')
        else:
            if descendientes:
                raise ValueError(f'La hoja {etiqueta} no puede tener hijos.')
            if etiqueta == 'x':
                continue
            try:
                valido = math.isfinite(float(etiqueta))
            except (ValueError, TypeError):
                valido = False
            if not valido:
                raise ValueError(f'Operación o constante inválida: {etiqueta}.')
        pendientes.extend((hijo, nivel + 1) for hijo in descendientes)
    if vistos != set(etiquetas) or not set(hijos).issubset(vistos):
        raise ValueError('Hay nodos desconectados de la raíz.')
    return altura


def analizar_arbol(etiquetas, hijos, altura_maxima=None):
    """Recorrer por ID; un nodo unario usa únicamente el hijo izquierdo."""
    altura = validar_arbol(etiquetas, hijos, altura_maxima=altura_maxima)
    datos = {'altura': altura, 'tamano': len(etiquetas),
             'aridades': {n: len(hijos.get(n, ())) for n in etiquetas},
             'preorder': [], 'inorder': [], 'postorder': []}

    def visitar(nodo):
        descendientes = hijos.get(nodo, ())
        datos['preorder'].append(nodo)
        if descendientes:
            visitar(descendientes[0])
        datos['inorder'].append(nodo)
        if len(descendientes) == 2:
            visitar(descendientes[1])
        datos['postorder'].append(nodo)

    visitar(0)
    return datos


def evaluar(etiquetas, hijos, altura_maxima=None, tolerar_errores=False, x=None):
    """Evaluar el árbol numérico siguiendo exactamente el recorrido postorder."""
    datos = analizar_arbol(etiquetas, hijos, altura_maxima)
    resultados, pasos = {}, []
    for nodo in datos['postorder']:
        etiqueta = etiquetas[nodo]
        try:
            if etiqueta in OPERACIONES_VALIDAS:
                valores = [resultados[hijo] for hijo in hijos[nodo]]
                if any(valor is None for valor in valores):
                    raise ValueError('Un operando no tiene resultado real.')
                valor = OPERACIONES_VALIDAS[etiqueta].aplicar(*valores)
            else:
                if etiqueta == 'x':
                    if x is None or not math.isfinite(x):
                        raise ValueError('Se necesita un valor finito de x.')
                    valor = x
                else:
                    valor = float(etiqueta)
        except ValueError:
            if not tolerar_errores:
                raise
            valor = None
        resultados[nodo] = valor
        pasos.append((nodo, valor))
    return pasos


def predecir(etiquetas, hijos, xs):
    xs = vector_finito(xs)
    datos = analizar_arbol(etiquetas, hijos)
    resultados = {}
    for nodo in datos['postorder']:
        simbolo = etiquetas[nodo]
        if simbolo in OPERACIONES_VALIDAS:
            resultados[nodo] = OPERACIONES_VALIDAS[simbolo].aplicar_vector(
                *(resultados[hijo] for hijo in hijos[nodo]))
        else:
            resultados[nodo] = xs if simbolo == 'x' else float(simbolo)
    return np.broadcast_to(resultados[0], xs.shape).copy()


CONSTANTES = tuple(str(n) for n in range(-9, 10))


def generar_arbol(rng, altura_maxima, incluir_x=False):
    """Generar un árbol aleatorio del catálogo con constantes numéricas."""
    if not isinstance(altura_maxima, int) or not 0 <= altura_maxima <= ALTURA_MAXIMA:
        raise ValueError(f'La altura debe estar entre 0 y {ALTURA_MAXIMA}.')
    etiquetas, hijos = {}, {}
    terminales = CONSTANTES + (('x',) if incluir_x else ())

    def crear(nivel):
        nodo = len(etiquetas)
        if nivel == altura_maxima or (nivel > 0 and rng.random() < 0.4):
            etiquetas[nodo] = rng.choice(terminales)
        else:
            simbolo = rng.choice(tuple(OPERACIONES_VALIDAS))
            etiquetas[nodo] = simbolo
            hijos[nodo] = tuple(crear(nivel + 1)
                                for _ in range(OPERACIONES_VALIDAS[simbolo].operandos))
        return nodo

    crear(0)
    return etiquetas, hijos


def escribir_expresion(etiquetas, hijos, nodo=0):
    etiqueta = etiquetas[nodo]
    if nodo not in hijos:
        return etiqueta
    argumentos = [escribir_expresion(etiquetas, hijos, hijo) for hijo in hijos[nodo]]
    if len(argumentos) == 1:
        return f'{etiqueta}({argumentos[0]})'
    return f'({argumentos[0]} {etiqueta} {argumentos[1]})'


def forma_arbol(etiquetas, hijos, nodo=0):
    """Representación inmutable para copiar y comparar subárboles."""
    return (etiquetas[nodo], tuple(forma_arbol(etiquetas, hijos, hijo)
                                  for hijo in hijos.get(nodo, ())))


def desde_forma(forma):
    etiquetas, hijos = {}, {}

    def copiar(rama):
        nodo = len(etiquetas)
        etiquetas[nodo] = rama[0]
        if rama[1]:
            hijos[nodo] = tuple(copiar(hijo) for hijo in rama[1])
        return nodo

    copiar(forma)
    return etiquetas, hijos


def ramas(forma, ruta=()):
    yield ruta, forma
    for indice, hijo in enumerate(forma[1]):
        yield from ramas(hijo, ruta + (indice,))


def sustituir(forma, ruta, reemplazo):
    if not ruta:
        return reemplazo
    descendientes = list(forma[1])
    indice = ruta[0]
    descendientes[indice] = sustituir(descendientes[indice], ruta[1:], reemplazo)
    return forma[0], tuple(descendientes)


def altura_forma(forma):
    return 1 + max((altura_forma(hijo) for hijo in forma[1]), default=-1)


def mutar_arbol(etiquetas, hijos, rng, altura_maxima, incluir_x=False):
    forma = forma_arbol(etiquetas, hijos)
    ruta, rama = rng.choice(list(ramas(forma)))
    if rng.random() < 0.5:
        if rama[1]:
            simbolos = [s for s, op in OPERACIONES_VALIDAS.items()
                        if op.operandos == len(rama[1])]
            reemplazo = rng.choice(simbolos), rama[1]
        else:
            reemplazo = rng.choice(CONSTANTES + (('x',) if incluir_x else ())), ()
    else:
        nuevos = generar_arbol(rng, altura_maxima - len(ruta), incluir_x)
        reemplazo = forma_arbol(*nuevos)
    return desde_forma(sustituir(forma, ruta, reemplazo))


def cruzar_arboles(etiquetas, hijos, otras_etiquetas, otros_hijos, rng, altura_maxima):
    forma = forma_arbol(etiquetas, hijos)
    ruta, _ = rng.choice(list(ramas(forma)))
    donantes = [rama for _, rama in ramas(forma_arbol(otras_etiquetas, otros_hijos))
                if altura_forma(rama) <= altura_maxima - len(ruta)]
    return desde_forma(sustituir(forma, ruta, rng.choice(donantes)))


@dataclass
class Candidato:
    etiquetas: dict
    hijos: dict
    valor: float
    error: float
    mse: float | None = None
    nmse: float | None = None


class BusquedaExpresiones:
    """Búsqueda evolutiva por lotes; sin límite automático en modo continuo."""
    usa_x = False

    def __init__(self, objetivo, altura_maxima=None, max_intentos=None,
                 tolerancia=TOLERANCIA, semilla=None, tamano_elite=32):
        self.altura = ALTURA_MAXIMA if altura_maxima is None else altura_maxima
        if not isinstance(self.altura, int) or not 0 <= self.altura <= ALTURA_MAXIMA:
            raise ValueError(f'La altura debe estar entre 0 y {ALTURA_MAXIMA}.')
        if not math.isfinite(objetivo):
            raise ValueError('El resultado esperado debe ser finito.')
        if max_intentos is not None and (not isinstance(max_intentos, int) or max_intentos < 1):
            raise ValueError('Los intentos deben ser un entero positivo o None.')
        if not isinstance(tamano_elite, int) or tamano_elite < 1:
            raise ValueError('El tamaño de élite debe ser un entero positivo.')
        if not math.isfinite(tolerancia) or tolerancia < 0:
            raise ValueError('La tolerancia debe ser finita y no negativa.')
        self.objetivo = objetivo
        self.max_intentos, self.tolerancia = max_intentos, tolerancia
        self.rng = random.Random(semilla)
        self.intentos = 0
        self.mejor = None
        self.terminada = False
        self.simples = iter(self.expresiones_simples())
        self.elite = []
        self.tamano_elite = tamano_elite
        self.firmas_elite = set()
        self.mutaciones = 0
        self.cruces = 0

    def expresiones_simples(self):
        if self.altura == 0:
            for constante in CONSTANTES:
                yield {0: constante}, {}
            return
        # Un primer candidato válido asegura una aproximación aun con pocos intentos.
        yield {0: '+', 1: '0', 2: '0'}, {0: (1, 2)}
        for simbolo, operacion in OPERACIONES_VALIDAS.items():
            for izquierda in CONSTANTES:
                if operacion.operandos == 1:
                    yield {0: simbolo, 1: izquierda}, {0: (1,)}
                else:
                    for derecha in CONSTANTES:
                        yield {0: simbolo, 1: izquierda, 2: derecha}, {0: (1, 2)}

    @staticmethod
    def aptitud(candidato):
        return candidato.error, len(candidato.etiquetas)

    def seleccionar(self):
        participantes = self.rng.sample(self.elite, min(3, len(self.elite)))
        return min(participantes, key=self.aptitud)

    def proponer(self):
        # Combinar enumeración de expresiones simples con evolución desde el inicio.
        if self.intentos < 256 or self.intentos % 4 == 0:
            etiquetas, hijos = next(self.simples, (None, None))
            if etiquetas is not None:
                return etiquetas, hijos
        if not self.elite or self.rng.random() < 0.25:
            return generar_arbol(self.rng, self.altura, self.usa_x)
        padre = self.seleccionar()
        if self.rng.random() < 0.6:
            self.mutaciones += 1
            return mutar_arbol(padre.etiquetas, padre.hijos, self.rng, self.altura, self.usa_x)
        madre = self.seleccionar()
        self.cruces += 1
        return cruzar_arboles(padre.etiquetas, padre.hijos,
                             madre.etiquetas, madre.hijos, self.rng, self.altura)

    def conservar(self, candidato):
        firma = forma_arbol(candidato.etiquetas, candidato.hijos)
        if firma in self.firmas_elite:
            return
        self.elite.append(candidato)
        self.firmas_elite.add(firma)
        self.elite.sort(key=self.aptitud)
        if len(self.elite) > self.tamano_elite:
            descartado = self.elite.pop()
            self.firmas_elite.remove(forma_arbol(descartado.etiquetas, descartado.hijos))
        self.mejor = self.elite[0]

    def puntuar(self, etiquetas, hijos):
        valor = evaluar(etiquetas, hijos, self.altura)[-1][1]
        error = abs(valor - self.objetivo)
        return Candidato(etiquetas, hijos, valor, error)

    def avanzar(self, lote=60, presupuesto_ms=None):
        inicio = time.monotonic()
        for indice in range(lote):
            if self.terminada:
                break
            if indice and presupuesto_ms is not None and (time.monotonic() - inicio) * 1000 >= presupuesto_ms:
                break
            etiquetas, hijos = self.proponer()
            self.intentos += 1
            try:
                if self.altura > 0 and not hijos:
                    raise ValueError('Se requiere una expresión con operaciones.')
                candidato = self.puntuar(etiquetas, hijos)
                if math.isfinite(candidato.error):
                    self.conservar(candidato)
            except ValueError:
                pass
            # Acertar no termina la evolución: seguir intentando reducir el árbol.
            self.terminada = self.max_intentos is not None and self.intentos >= self.max_intentos


class BusquedaGrafica(BusquedaExpresiones):
    """Regresión simbólica: error MSE calculado sobre TODOS los puntos del CSV."""
    usa_x = True

    def __init__(self, datos, **opciones):
        self.datos = datos
        super().__init__(0, **opciones)

    def expresiones_simples(self):
        if self.altura == 0:
            yield {0: 'x'}, {}
            yield from super().expresiones_simples()
            return
        yield {0: '+', 1: 'x', 2: '0'}, {0: (1, 2)}
        yield {0: '×', 1: 'x', 2: 'x'}, {0: (1, 2)}
        for simbolo, operacion in OPERACIONES_VALIDAS.items():
            if operacion.operandos == 1:
                yield {0: simbolo, 1: 'x'}, {0: (1,)}
            else:
                for constante in CONSTANTES:
                    for a, b in [('x', constante), (constante, 'x')]:
                        yield {0: simbolo, 1: a, 2: b}, {0: (1, 2)}
        yield from super().expresiones_simples()

    def puntuar(self, etiquetas, hijos):
        pred = predecir(etiquetas, hijos, self.datos.x)
        mse, nmse = calcular_errores(self.datos.y, pred)
        return Candidato(etiquetas, hijos, float(pred[0]), mse, mse, nmse)


class GraficaCartesiana(FigureCanvasQTAgg):
    """Puntos de referencia y curva candidata en el plano cartesiano."""
    def __init__(self):
        self.figura = Figure(facecolor='#0b1220', layout='constrained')
        super().__init__(self.figura)
        self.ax = self.figura.add_subplot()
        self.dibujar(None)

    def dibujar(self, datos, candidato=None):
        ax = self.ax
        ax.clear()
        ax.set_facecolor('#101b2c')
        ax.tick_params(colors='#a9bfd6', labelsize=9)
        for borde in ax.spines.values():
            borde.set_color('#334155')
        ax.set_xlabel('x', color='#a9bfd6')
        ax.set_ylabel('y', color='#a9bfd6')
        ax.grid(color='#334155', alpha=0.4)
        ax.axhline(0, color='#64748b', linewidth=0.7)
        ax.axvline(0, color='#64748b', linewidth=0.7)
        if datos is not None:
            ax.scatter(datos.x, datos.y, color='#67d8ff', s=16,
                       label='CSV esperado', zorder=3)
            if candidato is not None:
                minimo, maximo = float(np.min(datos.x)), float(np.max(datos.x))
                if minimo == maximo:
                    minimo, maximo = minimo - 1, maximo + 1
                # Incluir todos los x observados para no omitir oscilaciones muestreadas.
                xs = np.unique(np.concatenate((datos.x, np.linspace(minimo, maximo, 300))))
                try:
                    ys = predecir(candidato.etiquetas, candidato.hijos, xs)
                except ValueError:
                    ys = []
                    for x in xs:
                        try:
                            ys.append(evaluar(candidato.etiquetas, candidato.hijos, x=float(x))[-1][1])
                        except ValueError:
                            ys.append(np.nan)
                ax.plot(xs, ys, color='#53e3b1', linewidth=1.4, label='Mejor expresión')
            ax.legend(facecolor='#172638', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=9)
        self.draw_idle()



class Nodo(QGraphicsObject):
    def __init__(self, etiqueta, aridad):
        super().__init__()
        self.etiqueta = etiqueta
        self.aridad = aridad
        self.valor = ''
        self.estado = 'pendiente'
        self.pulso = 0.0
        self.animacion = QVariantAnimation(self)
        self.animacion.setDuration(85)
        self.animacion.setStartValue(0.0)
        self.animacion.setKeyValueAt(0.4, 1.0)
        self.animacion.setEndValue(0.0)
        self.animacion.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animacion.valueChanged.connect(self.actualizar_pulso)

    def actualizar_pulso(self, valor):
        self.pulso = float(valor)
        self.update()

    def resaltar(self):
        self.animacion.stop()
        self.animacion.start()

    def boundingRect(self):
        return QRectF(-69, -69, 138, 138)

    def paint(self, painter, option, widget=None):
        colores = {'pendiente': '#425570', 'activo': '#67d8ff',
                   'listo': '#53e3b1', 'error': '#ff829b'}
        color = QColor(colores[self.estado])
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radio = 44 + 4 * self.pulso
        if self.estado != 'pendiente':
            halo = QRadialGradient(QPointF(0, 0), radio + 18)
            centro = QColor(color)
            centro.setAlpha(45 + int(45 * self.pulso))
            halo.setColorAt(0.55, centro)
            halo.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(halo)
            painter.drawEllipse(QPointF(0, 0), radio + 18, radio + 18)
        fondo = QRadialGradient(QPointF(-15, -20), 80)
        fondo.setColorAt(0, QColor('#223953'))
        fondo.setColorAt(1, QColor('#101d30'))
        painter.setBrush(fondo)
        painter.setPen(QPen(color, 2.2 if self.estado != 'pendiente' else 1.3))
        painter.drawEllipse(QPointF(0, 0), radio, radio)
        painter.setPen(QColor('#f1f5f9'))
        painter.setFont(QFont('Sans Serif', 21, QFont.Weight.DemiBold))
        painter.drawText(QRectF(-40, -31 if self.valor else -25, 80, 43),
                         Qt.AlignmentFlag.AlignCenter, self.etiqueta)
        if self.valor:
            painter.setPen(color)
            texto = 'Sin valor\nreal' if self.estado == 'error' else self.valor
            tamano = 8 if len(self.valor) > 9 else 10
            painter.setFont(QFont('Sans Serif', tamano, QFont.Weight.DemiBold))
            painter.drawText(QRectF(-40, 5, 80, 23),
                             Qt.AlignmentFlag.AlignCenter, texto)
        painter.setPen(QColor('#8ca5bf'))
        painter.setFont(QFont('Sans Serif', 7))
        painter.drawText(QRectF(-35, 26, 70, 14),
                         Qt.AlignmentFlag.AlignCenter, f'aridad {self.aridad}')


class VistaArbol(QGraphicsView):
    def __init__(self, escena):
        super().__init__(escena)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor('#0b1220'))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class VentanaArbol(QWidget):
    def __init__(self, cargar_automatico=True):
        super().__init__()
        self.setWindowTitle('Árbol binario · Búsqueda de expresiones')
        self.resize(1080, 940)
        self.setMinimumSize(540, 640)
        self.setStyleSheet('''
            QWidget { background: #0b1220; color: #e2e8f0; font-size: 14px; }
            QDoubleSpinBox { background: #172638; border: 1px solid #334155;
                border-radius: 9px; padding: 10px; min-width: 160px; }
            QPushButton { background: #38bdf8; color: #082032; border: none;
                border-radius: 9px; padding: 12px 26px; font-weight: bold; }
            QPushButton:hover { background: #7dd3fc; }
            QPushButton:pressed { background: #0ea5e9; }
            QPushButton:disabled { background: #1e293b; color: #64748b; }
            QDoubleSpinBox:disabled { color: #64748b; }
            QPlainTextEdit { background: #101b2c; border: 1px solid #26374d;
                border-radius: 10px; padding: 8px; color: #b3c6db; font-size: 12px; }
        ''')
        self.objetivo = QDoubleSpinBox()
        self.objetivo.setRange(-1000000, 1000000)
        self.objetivo.setDecimals(6)
        self.objetivo.setValue(6)
        self.objetivo.setKeyboardTracking(False)
        self.objetivo.setAccessibleName('Resultado esperado')
        self.boton_buscar = QPushButton('Buscar')
        self.boton_buscar.setMinimumWidth(120)
        self.boton_buscar.clicked.connect(self.iniciar_busqueda)
        controles = QHBoxLayout()
        controles.addStretch()
        controles.addWidget(QLabel('Resultado esperado'))
        controles.addWidget(self.objetivo)
        controles.addWidget(self.boton_buscar)
        controles.addStretch()
        self.boton_aleatorio = QPushButton('Aleatorio')
        self.boton_aleatorio.clicked.connect(self.objetivo_aleatorio)
        self.boton_csv = QPushButton('Cargar CSV')
        self.boton_csv.clicked.connect(self.seleccionar_csv)
        self.boton_valor = QPushButton('Usar resultado')
        self.boton_valor.clicked.connect(self.usar_resultado)
        self.boton_valor.setVisible(False)
        archivos = QHBoxLayout()
        archivos.addStretch()
        archivos.addWidget(self.boton_aleatorio)
        archivos.addWidget(self.boton_csv)
        archivos.addWidget(self.boton_valor)
        archivos.addStretch()
        self.fuente = QLabel('Búsqueda de un valor · Tolerancia: 0.000001')
        self.fuente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fuente.setWordWrap(True)
        self.fuente.setStyleSheet('color: #94a3b8; font-size: 12px;')
        self.expresion = QLabel('La búsqueda construirá una expresión para tu resultado.')
        self.expresion.setWordWrap(True)
        self.expresion.setTextFormat(Qt.TextFormat.PlainText)
        self.expresion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expresion.setMaximumHeight(85)
        self.expresion.setStyleSheet('color: #67d8ff; font-size: 17px;')
        self.escena = QGraphicsScene(self)
        self.vista = VistaArbol(self.escena)
        self.grafica = GraficaCartesiana()
        self.paneles = QSplitter(Qt.Orientation.Horizontal)
        self.paneles.addWidget(self.vista)
        self.paneles.addWidget(self.grafica)
        self.paneles.setSizes([600, 600])
        self.grafica.setVisible(False)
        self.estadisticas = QLabel(f'Altura máxima: {ALTURA_MAXIMA} · Búsqueda continua con elitismo')
        self.estadisticas.setWordWrap(True)
        self.estadisticas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estadisticas.setStyleSheet('color: #94a3b8; font-size: 12px;')
        self.recorridos = QPlainTextEdit()
        self.recorridos.setReadOnly(True)
        self.recorridos.setAccessibleName('Recorridos del árbol')
        self.recorridos.setPlaceholderText('Aquí aparecerán inorder, postorder y preorder.')
        self.recorridos.setMinimumHeight(130)
        self.recorridos.setMaximumHeight(170)
        self.mensaje = QLabel('Introduce un resultado y pulsa Buscar.')
        self.mensaje.setWordWrap(True)
        self.mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mensaje.setStyleSheet('color: #94a3b8; font-size: 13px;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addLayout(controles)
        layout.addLayout(archivos)
        layout.addWidget(self.fuente)
        layout.addWidget(self.expresion)
        layout.addWidget(self.paneles, 1)
        layout.addWidget(self.estadisticas)
        layout.addWidget(self.recorridos)
        layout.addWidget(self.mensaje)
        self.temporizador = QTimer(self)
        self.temporizador.setInterval(100)
        self.temporizador.timeout.connect(self.avanzar)
        self.reloj_busqueda = QTimer(self)
        self.reloj_busqueda.setInterval(10)
        self.reloj_busqueda.timeout.connect(self.procesar_busqueda)
        self.busqueda = None
        self.etiquetas, self.hijos, self.nodos, self.conexiones = {}, {}, {}, {}
        self.pasos = []
        self.indice = 0
        self.activo = None
        self.resumen_busqueda = ''
        self.candidato_mostrado = None
        self.datos = None
        self.coincidencia_animada = False
        self.reloj_visual = QElapsedTimer()
        self.reloj_visual.start()
        if cargar_automatico:
            ruta_csv = Path(__file__).resolve().with_name('gr.csv')
            if ruta_csv.is_file():
                self.abrir_csv(ruta_csv)
                if self.datos is not None:
                    self.generar()
            else:
                self.mensaje.setText('No se encontró gr.csv junto a arbol.py. Ejecuta gr.py o pulsa Cargar CSV.')

    def seleccionar_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, 'Cargar puntos x,y', '', 'Archivos CSV (*.csv);;Todos (*)')
        if ruta:
            self.abrir_csv(ruta)

    def abrir_csv(self, ruta):
        try:
            datos = cargar_csv(ruta)
        except (ValueError, OSError, UnicodeError) as error:
            self.mensaje.setText(f'No se pudo cargar el CSV: {error}')
            return
        self.limpiar_busqueda()
        self.datos = datos
        self.objetivo.setEnabled(False)
        self.boton_valor.setVisible(True)
        self.boton_aleatorio.setEnabled(False)
        self.grafica.setVisible(True)
        self.paneles.setSizes([600, 600])
        self.grafica.dibujar(datos)
        self.fuente.setText(f'{datos.nombre} · {len(datos.x)} puntos · Criterio: MSE ≤ {TOLERANCIA:g}')
        self.expresion.setText('Pulsa Buscar para ajustar una expresión a los datos x,y.')
        self.mensaje.setText('CSV cargado. El error se calculará sobre todos los puntos.')

    def limpiar_busqueda(self):
        self.reloj_busqueda.stop()
        self.temporizador.stop()
        for nodo in self.nodos.values():
            nodo.animacion.stop()
        self.escena.clear()
        self.etiquetas, self.hijos, self.nodos, self.conexiones = {}, {}, {}, {}
        self.pasos = []
        self.activo = None
        self.busqueda = None
        self.candidato_mostrado = None
        self.boton_buscar.setText('Buscar')
        self.recorridos.clear()

    def usar_resultado(self):
        self.limpiar_busqueda()
        self.datos = None
        self.grafica.setVisible(False)
        self.objetivo.setEnabled(True)
        self.boton_aleatorio.setEnabled(True)
        self.boton_valor.setVisible(False)
        self.fuente.setText('Búsqueda de un valor · Tolerancia: 0.000001')
        self.expresion.setText('Introduce un resultado y pulsa Buscar.')
        self.mensaje.setText('Modo de búsqueda de un valor.')

    def objetivo_aleatorio(self):
        if self.reloj_busqueda.isActive():
            return
        anterior = self.objetivo.value()
        nuevo = round(random.uniform(-100, 100), 3)
        while nuevo == anterior:
            nuevo = round(random.uniform(-100, 100), 3)
        self.objetivo.setValue(nuevo)
        self.mensaje.setText('Resultado aleatorio generado. Pulsa Buscar.')

    def iniciar_busqueda(self):
        if self.reloj_busqueda.isActive():
            self.cancelar_busqueda()
        else:
            self.generar()

    def cancelar_busqueda(self):
        self.reloj_busqueda.stop()
        self.boton_buscar.setText('Buscar')
        self.objetivo.setEnabled(self.datos is None)
        self.boton_aleatorio.setEnabled(self.datos is None)
        self.mostrar_mejor(forzar=True)
        self.actualizar_mensaje()

    def generar(self):
        self.temporizador.stop()
        self.reloj_busqueda.stop()
        for nodo in self.nodos.values():
            nodo.animacion.stop()
        self.busqueda = (BusquedaGrafica(self.datos, tolerancia=TOLERANCIA) if self.datos is not None
                         else BusquedaExpresiones(self.objetivo.value(), tolerancia=TOLERANCIA))
        self.coincidencia_animada = False
        self.boton_aleatorio.setEnabled(False)
        self.candidato_mostrado = None
        self.resumen_busqueda = ''
        self.boton_buscar.setText('Detener')
        self.objetivo.setEnabled(False)
        self.expresion.setText('Construyendo árboles de expresión…')
        self.mensaje.setText('Evaluando candidatos en postorder…')
        self.reloj_busqueda.start()

    def actualizar_mensaje(self):
        if self.busqueda is None:
            return
        mejor = self.busqueda.mejor
        estado = 'Buscando' if self.reloj_busqueda.isActive() else 'Detenida'
        if mejor is None:
            self.mensaje.setText(f'{estado} · Intentos: {self.busqueda.intentos}')
            return
        coincidencia = ' · Coincidencia' if mejor.error <= self.busqueda.tolerancia else ''
        if self.datos is not None:
            nmse = 'no definido' if mejor.nmse is None else f'{mejor.nmse:.8g}'
            valores = f'MSE: {mejor.mse:.8g} · NMSE: {nmse}'
        else:
            valores = (f'Esperado: {self.busqueda.objetivo:.10g} · '
                       f'Mejor resultado: {mejor.valor:.10g} · Error: {mejor.error:.6g}')
        self.resumen_busqueda = (
            f'{estado}{coincidencia} · {valores} · '
            f'Intentos: {self.busqueda.intentos} · Élite: {len(self.busqueda.elite)}')
        self.mensaje.setText(self.resumen_busqueda)

    def procesar_busqueda(self):
        self.busqueda.avanzar(presupuesto_ms=12)
        self.mostrar_mejor()
        self.actualizar_mensaje()

    def mostrar_mejor(self, forzar=False):
        if self.busqueda is None or self.busqueda.mejor is None:
            return
        mejor = self.busqueda.mejor
        if self.candidato_mostrado is mejor:
            return
        if self.temporizador.isActive() and not forzar:
            return
        coincide = mejor.error <= self.busqueda.tolerancia
        primera_coincidencia = coincide and not self.coincidencia_animada
        if not forzar and self.candidato_mostrado is not None and not primera_coincidencia and self.reloj_visual.elapsed() < 350:
            return
        self.reloj_visual.restart()
        self.cargar_arbol(mejor.etiquetas, mejor.hijos)
        self.candidato_mostrado = mejor
        texto = escribir_expresion(mejor.etiquetas, mejor.hijos)
        if self.datos is not None:
            x = float(self.datos.x[0])
            self.expresion.setText(f'f(x) = {texto}')
            self.expresion.setToolTip(f'Valores del árbol para x = {x:g} (primer punto del CSV)')
            self.estadisticas.setText(self.estadisticas.text() + f' · Valores para x = {x:g}')
            self.grafica.dibujar(self.datos, mejor)
        else:
            x = None
            self.expresion.setText(f'{texto} ≈ {mejor.valor:.10g}')
        self.pasos = evaluar(self.etiquetas, self.hijos, x=x)
        if primera_coincidencia:
            self.coincidencia_animada = True
            self.indice = 0
            self.activo = None
            self.temporizador.start()
            self.avanzar()
        else:
            # Mostrar el candidato estático sin pulsos ni espera por nodo.
            for numero, valor in self.pasos:
                self.nodos[numero].valor = f'{valor:.6g}'
                self.nodos[numero].estado = 'listo'
                self.nodos[numero].update()

    def cargar_arbol(self, etiquetas, hijos):
        validar_arbol(etiquetas, hijos)
        if hasattr(self, 'temporizador'):
            self.temporizador.stop()
        self.escena.clear()
        self.etiquetas, self.hijos = dict(etiquetas), dict(hijos)
        posiciones = {}
        hojas = []

        def situar(nodo, nivel):
            descendientes = hijos.get(nodo, ())
            if descendientes:
                coordenadas = [situar(hijo, nivel + 1) for hijo in descendientes]
                x = sum(coordenadas) / len(coordenadas)
            else:
                x = len(hojas) * 145
                hojas.append(nodo)
            posiciones[nodo] = (x, nivel * 145)
            return x

        situar(0, 0)
        self.conexiones = {}
        for padre, descendientes in hijos.items():
            for hijo in descendientes:
                px, py = posiciones[padre]
                hx, hy = posiciones[hijo]
                inicio, fin = QPointF(px, py + 45), QPointF(hx, hy - 45)
                camino = QPainterPath(inicio)
                medio = (inicio.y() + fin.y()) / 2
                camino.cubicTo(QPointF(px, medio), QPointF(hx, medio), fin)
                self.conexiones[hijo] = self.escena.addPath(camino, QPen(QColor('#293c54'), 1.7))
        self.nodos = {}
        for numero, etiqueta in etiquetas.items():
            nodo = Nodo(etiqueta, len(hijos.get(numero, ())))
            nodo.setToolTip(f'Nodo #{numero} · {etiqueta} · Aridad {nodo.aridad}')
            nodo.setPos(QPointF(*posiciones[numero]))
            self.escena.addItem(nodo)
            self.nodos[numero] = nodo
        self.escena.setSceneRect(self.escena.itemsBoundingRect().adjusted(-25, -25, 25, 25))
        self.vista.fitInView(self.escena.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if hasattr(self, 'expresion'):
            texto = escribir_expresion(etiquetas, hijos)
            self.expresion.setText(texto)
            self.expresion.setToolTip(texto)

        datos = analizar_arbol(etiquetas, hijos)
        self.estadisticas.setText(
            f'Tamaño: {datos["tamano"]} nodos · Altura: {datos["altura"]}/{ALTURA_MAXIMA} · '
            'Aridad: hojas 0, funciones 1, operaciones binarias 2')
        lineas = []
        for nombre in ('inorder', 'postorder', 'preorder'):
            recorrido = ' → '.join(f'#{n}:{etiquetas[n]}' for n in datos[nombre])
            lineas.append(f'{nombre.capitalize()}: {recorrido}')
        self.recorridos.setPlainText('\n\n'.join(lineas))


    def avanzar(self):
        if self.activo is not None:
            self.nodos[self.activo].estado = 'listo'
            self.nodos[self.activo].update()
        if self.indice >= len(self.pasos):
            self.temporizador.stop()
            return
        numero, valor = self.pasos[self.indice]
        nodo = self.nodos[numero]
        nodo.estado = 'activo'
        nodo.valor = f'{valor:.6g}'
        nodo.resaltar()
        for hijo in self.hijos.get(numero, ()):
            self.conexiones[hijo].setPen(QPen(QColor('#53e3b1'), 2.3))
        nodo.update()
        self.activo = numero
        self.indice += 1
        if numero == 0:
            nodo.estado = 'listo'
            self.temporizador.stop()
            self.actualizar_mensaje()

    def closeEvent(self, event):
        self.reloj_busqueda.stop()
        self.temporizador.stop()
        for nodo in self.nodos.values():
            nodo.animacion.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    ventana = VentanaArbol()
    ventana.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
