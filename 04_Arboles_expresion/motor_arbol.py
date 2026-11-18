"""Árboles binarios de expresión, recorridos y búsqueda de un resultado numérico."""
import math
import random
import time
import numpy as np
from datos_grafica import DatosGrafica, calcular_errores, vector_finito
from dataclasses import dataclass
from operaciones import OPERACIONES_VALIDAS

# Altura en aristas: raíz = 0. Se permiten como máximo seis filas.
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
