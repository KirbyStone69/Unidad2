"""Puente de tipos y de ejecución; no contiene operaciones genéticas.

El PDF no identifica la implementación de rand ni RAND_MAX. Se elige
RAND_MAX=32767 (configurable) y el generador estándar de Python. No se
promete que una semilla reproduzca la secuencia de una biblioteca C.
"""
import argparse
from contextlib import contextmanager
import ctypes
import ctypes.util
import math
from pathlib import Path
import random
import secrets
import shutil
import sys
import struct
import time

RAND_MAX = 32767
SEMILLA_USADA = None
_panel = None
CRUCE_ESTRICTO = False
incidencias = {}
_azar = random.Random()


def float32(value):
    """Redondeo en asignaciones/casts al tipo float de C++ (IEEE-754)."""
    try:
        return struct.unpack('=f', struct.pack('=f', value))[0]
    except OverflowError as error:
        raise ValueError('Valor fuera del rango de float32 del original') from error


# C++17 escoge las sobrecargas float: sinf no siempre equivale a redondear
# math.sin (double). Se utiliza la biblioteca matemática del propio sistema
# mediante ctypes, que pertenece a la biblioteca estándar de Python.
_matematica = None


def _funcion_float(nombre):
    global _matematica
    if _matematica is None:
        candidatos = [None, ctypes.util.find_library('m'), 'ucrtbase.dll']
        for candidato in candidatos:
            try:
                lib = ctypes.CDLL(candidato)
                if hasattr(lib, 'sinf') and hasattr(lib, 'sqrtf'):
                    _matematica = lib
                    break
            except OSError:
                continue
        if _matematica is None:
            raise RuntimeError('No se encuentra sinf/sqrtf del sistema para reproducir float de C++')
    funcion = getattr(_matematica, nombre)
    funcion.argtypes = [ctypes.c_float]
    funcion.restype = ctypes.c_float
    return funcion


def seno32(x):
    return _funcion_float('sinf')(x)


def raiz32(x):
    return _funcion_float('sqrtf')(x)


def configurar_azar(semilla=None, rand_max=32767):
    global RAND_MAX, SEMILLA_USADA, _panel
    if not 1 <= rand_max <= 2147483647:
        raise ValueError('RAND_MAX debe estar entre 1 y 2147483647')
    RAND_MAX = rand_max
    SEMILLA_USADA = secrets.randbits(64) if semilla is None else semilla
    _panel = None
    _azar.seed(SEMILLA_USADA)
    incidencias.clear()


def rand():
    return _azar.randint(0, RAND_MAX)


def punto_seguro(punto_cruce, lcrom):
    """R1: solo el valor indefinido lcrom+1 se lleva al extremo lcrom.

    La fórmula del impreso y el consumo de rand se conservan. Los puntos
    válidos no cambian. --cruce-estricto detecta el acceso ilegal en lugar
    de repararlo; no se inventa el bit que habría leído C++.
    """
    if punto_cruce == lcrom + 1:
        if CRUCE_ESTRICTO:
            raise ValueError(f'Punto de cruce {punto_cruce} fuera de longitud {lcrom} (libro 302)')
        incidencias['puntos_fuera_de_rango'] = incidencias.get('puntos_fuera_de_rango', 0) + 1
        return lcrom
    if not 0 <= punto_cruce <= lcrom:
        raise ValueError('Punto de cruce inválido')
    return punto_cruce


def longitud(x_min, x_max, TOL):
    if not all(math.isfinite(x) for x in (x_min, x_max, TOL)):
        raise ValueError('Los límites y la tolerancia deben ser finitos')
    if x_max <= x_min or TOL <= 0:
        raise ValueError('Se requiere x_min < x_max y TOL > 0')
    # Exactamente la expresión del main; no se usa log2 ni se altera TOL.
    argumento = 1 + (x_max - x_min)/TOL
    if not math.isfinite(argumento):
        raise ValueError('Rango/TOL fuera del rango numérico del original')
    lcrom = math.ceil(math.log(argumento) / math.log(2.0))
    # El int pot del original desborda al finalizar un cromosoma de 31 bits.
    if not 1 <= lcrom <= 30:
        raise ValueError('Longitud fuera de 1..30: int de 32 bits del original desbordaría')
    return lcrom


def argumentos(multivariable=False, argv=None, programa="maximizacion"):
    parser = argparse.ArgumentParser(description='Migración del apéndice B de a.pdf; véase REPORTE.md')
    tipo = str if multivariable else float
    # Añadido solicitado: ejecución sin argumentos. Las operaciones no cambian.
    if multivariable:
        limites = ('0,0', '100,100')
    elif programa == 'minimizacion':
        limites = (-250.0, 250.0)
    else:
        limites = (0.0, 32.0)
    parser.add_argument('x_min', type=tipo, nargs='?', default=limites[0])
    parser.add_argument('x_max', type=tipo, nargs='?', default=limites[1])
    parser.add_argument('TOL', type=tipo, nargs='?', default='0.0001' if multivariable else 0.0001)
    parser.add_argument('tam_pob', type=int, nargs='?', default=500)
    parser.add_argument('num_gen', type=int, nargs='?', default=1000)
    parser.add_argument('prob_cruce', type=float, nargs='?', default=0.4)
    parser.add_argument('prob_mut', type=float, nargs='?', default=0.001)
    parser.add_argument('--semilla', type=int, default=None)
    parser.add_argument('--rand-max', type=int, default=32767)
    parser.add_argument('--cruce-estricto', action='store_true')
    args = parser.parse_args(argv)
    if args.tam_pob <= 0 or args.num_gen < 0:
        parser.error('tam_pob debe ser positivo; num_gen no puede ser negativo')
    if not 0 <= args.prob_cruce <= 1 or not 0 <= args.prob_mut <= 1:
        parser.error('Las probabilidades deben estar entre 0 y 1')
    global CRUCE_ESTRICTO
    CRUCE_ESTRICTO = args.cruce_estricto
    configurar_azar(args.semilla, args.rand_max)
    return args


def informar_incidencias():
    if incidencias:
        import sys
        print('R1: puntos de cruce fuera de rango tratados como cruce al final: '
              + str(incidencias.get('puntos_fuera_de_rango', 0)), file=sys.stderr)


def guardar_resultado(nombre, args, lcrom, pos_mejor, mejor, resultado):
    """Añadido de salida: guardar datos sin alterar ninguna operación genética."""
    multi = nombre == 'multivariable'
    aptitud = mejor.aptitud if nombre == 'maximizacion' else mejor.aptitud_bruta
    fenotipo = mejor.vec_x if multi else mejor.x
    cromosomas = mejor.vec_genes if multi else [mejor.genes]
    genes = '; '.join(''.join(str(int(bit)) for bit in cromosoma)
                      for cromosoma in cromosomas)
    archivo = Path(f'datos_{nombre}.txt')
    texto = (
        f'Programa: {nombre}\n'
        f'Límite inferior: {args.x_min}\n'
        f'Límite superior: {args.x_max}\n'
        f'Tolerancia: {args.TOL}\n'
        f'Población: {args.tam_pob}\n'
        f'Generaciones: {args.num_gen}\n'
        f'Probabilidad de cruce: {args.prob_cruce}\n'
        f'Probabilidad de mutación: {args.prob_mut}\n'
        f'Semilla usada: {SEMILLA_USADA}\n'
        f'RAND_MAX: {RAND_MAX}\n'
        f'Longitud de cromosoma(s): {lcrom}\n\n'
        f'{resultado}\n'
        f'Índice del mejor individuo: {pos_mejor}\n'
        f'Aptitud con precisión completa: {aptitud}\n'
        f'Fenotipo con precisión completa: {fenotipo}\n'
        f'Genes (LSB primero): {genes}\n'
        f'Puntos de cruce corregidos: {incidencias.get("puntos_fuera_de_rango", 0)}\n'
    )
    archivo.write_text(texto, encoding='utf-8')
    print(f'Datos guardados en {archivo}')


class PanelTerminal:
    """Panel ANSI fijo: observa datos reales, sin consumir azar genético."""
    def __init__(self, nombre, args):
        self.nombre = nombre
        self.total = args.num_gen
        self.generacion = 0
        self.cruce = None
        self.mutacion = None
        self.capturo_cruce = False
        self.capturo_mutacion = False
        self.ultimo_refresco = -float('inf')
        self.filas = 16
        self.ancho = max(20, shutil.get_terminal_size((100, 24)).columns - 1)
        sys.stdout.write('\n' * self.filas)

    def mostrar(self, mejor, forzar=False):
        ahora = time.monotonic()
        if not forzar and ahora - self.ultimo_refresco < 0.1:
            return
        self.ultimo_refresco = ahora
        aptitud = mejor.aptitud if self.nombre == 'maximizacion' else mejor.aptitud_bruta
        fenotipo = mejor.vec_x if hasattr(mejor, 'vec_x') else mejor.x
        if self.cruce:
            gen, padres, hijos = self.cruce
            titulo_cruce = f'Cruce observado en generación {gen} (corte |; bits LSB primero):'
        else:
            titulo_cruce = 'Cruce: todavía no se ha observado una pareja.'
            padres = hijos = ['—', '—']
        if self.mutacion:
            gen, variable, bit, antes, despues = self.mutacion
            titulo_mutacion = f'Mutación observada: generación {gen}, variable {variable+1}, bit {bit+1}'
        else:
            titulo_mutacion = 'Mutación observada: todavía ninguna.'
            antes = despues = '—'
        lineas = [
            f'Algoritmo genético: {self.nombre}',
            f'Semilla: {SEMILLA_USADA}',
            f'Generación: {self.generacion}/{self.total}',
            f'Mejor aptitud de la población: {aptitud:.6g}',
            f'Fenotipo: {fenotipo}',
            '', titulo_cruce,
            f'Padre 1: {padres[0]}', f'Padre 2: {padres[1]}',
            f'Hijo 1:  {hijos[0]}', f'Hijo 2:  {hijos[1]}',
            '', titulo_mutacion,
            f'Antes:   {antes}', f'Después: {despues}',
            f'Puntos de cruce corregidos: {incidencias.get("puntos_fuera_de_rango", 0)}',
        ]
        # Reservar siempre el mismo bloque y reemplazar sus líneas, sin scroll.
        sys.stdout.write(f'\033[{self.filas}A')
        for linea in lineas:
            if len(linea) > self.ancho:
                linea = linea[:self.ancho-1] + '…'
            sys.stdout.write('\r\033[2K' + linea + '\n')
        sys.stdout.flush()


def iniciar_panel(nombre, args, mejor):
    global _panel
    _panel = PanelTerminal(nombre, args) if sys.stdout.isatty() else None
    if _panel:
        _panel.mostrar(mejor, forzar=True)


def nueva_generacion(generacion):
    if _panel:
        _panel.generacion = generacion
        _panel.capturo_cruce = False
        _panel.capturo_mutacion = False


def actualizar_panel(mejor):
    if _panel:
        _panel.mostrar(mejor)


def terminar_panel(mejor):
    global _panel
    if _panel:
        _panel.mostrar(mejor, forzar=True)
    _panel = None


def registrar_cruce(padre1, padre2, hijo1, hijo2, punto_cruce):
    if _panel is None or _panel.capturo_cruce:
        return
    multi = hasattr(padre1, 'vec_genes')
    puntos = punto_cruce if multi else [punto_cruce]

    def representar(individuo):
        cromosomas = individuo.vec_genes if multi else [individuo.genes]
        cadenas = []
        for genes, punto in zip(cromosomas, puntos):
            bits = ''.join(str(int(bit)) for bit in genes)
            punto = min(punto, len(bits))
            cadenas.append(bits[:punto] + '|' + bits[punto:])
        return ' ; '.join(cadenas)

    _panel.cruce = (_panel.generacion,
                    [representar(padre1), representar(padre2)],
                    [representar(hijo1), representar(hijo2)])
    _panel.capturo_cruce = True


def registrar_mutacion(individuo, variable, bit):
    if _panel is None or _panel.capturo_mutacion:
        return
    genes = individuo.vec_genes[variable] if hasattr(individuo, 'vec_genes') else individuo.genes
    despues = ''.join(str(int(gen)) for gen in genes)
    # Se llamó justo tras la inversión de ese bit: reconstruir su valor anterior.
    antes = despues[:bit] + str(int(not genes[bit])) + despues[bit+1:]
    _panel.mutacion = (_panel.generacion, variable, bit, antes, despues)
    _panel.capturo_mutacion = True


_observador_evaluacion = None


@contextmanager
def observar_evaluaciones(observador):
    """Salida opcional de cada evaluación real; se restaura incluso ante error."""
    global _observador_evaluacion
    anterior = _observador_evaluacion
    _observador_evaluacion = observador
    try:
        yield
    finally:
        _observador_evaluacion = anterior


def registrar_evaluacion(x, f):
    if _observador_evaluacion is not None:
        _observador_evaluacion(x, f)
