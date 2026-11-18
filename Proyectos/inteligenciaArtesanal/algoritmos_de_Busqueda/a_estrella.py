"""A* propio con heurística geométrica consistente y eventos de reproducción.

La escala mínima peso/longitud convierte las posiciones del dibujo a unidades
de costo. La desigualdad triangular garantiza que h no supera el costo real.
No depende de NetworkX ni de Qt.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import dist, inf, isfinite
from numbers import Real

from .tipos import Adyacencia, Arista, Conexion, NodoId, Paso, Resultado


@dataclass(frozen=True, kw_only=True)
class PasoAEstrella(Paso):
    heuristicas: dict[NodoId, float]
    valores_f: dict[NodoId, float]
    abiertos: frozenset[NodoId]


@dataclass(frozen=True)
class ResultadoAEstrella(Resultado):
    heuristicas: dict[NodoId, float]
    escala: float
    expandidos: int


def _numero_finito(valor, mensaje):
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise ValueError(mensaje)
    try:
        numero = float(valor)
    except (ValueError, OverflowError):
        raise ValueError(mensaje) from None
    if not isfinite(numero):
        raise ValueError(mensaje)
    return numero


def _preparar_heuristica(adyacencia, destino, posiciones, modo):
    if modo not in ('euclidiana', 'cero'):
        raise ValueError('La heurística debe ser euclidiana o cero.')
    coordenadas = {}
    if posiciones is not None:
        if not isinstance(posiciones, Mapping):
            raise ValueError('Las posiciones deben ser un mapa de coordenadas.')
        for nodo, posicion in posiciones.items():
            try:
                x, y = posicion
            except (TypeError, ValueError):
                raise ValueError('Cada posición debe contener dos coordenadas finitas.') from None
            coordenadas[nodo] = (
                _numero_finito(x, 'Las coordenadas deben ser numéricas y finitas.'),
                _numero_finito(y, 'Las coordenadas deben ser numéricas y finitas.'),
            )
        if not all(nodo in coordenadas for nodo in adyacencia):
            raise ValueError('Las posiciones deben incluir todos los nodos.')
    if modo == 'cero':
        return {nodo: 0.0 for nodo in adyacencia}, 0.0
    if posiciones is None:
        raise ValueError('La heurística euclidiana requiere posiciones para todos los nodos.')

    escala = inf
    for nodo, conexiones in adyacencia.items():
        for conexion in conexiones:
            longitud = dist(coordenadas[nodo], coordenadas[conexion.destino])
            if longitud > 0:
                escala = min(escala, conexion.peso / longitud)
    # Sin arcos de longitud positiva no hay una escala informativa. También
    # usamos cero si la geometría extrema desborda el rango de float.
    if not isfinite(escala) or escala == 0:
        return {nodo: 0.0 for nodo in adyacencia}, 0.0
    escala *= 1 - 1e-12  # Margen frente al redondeo de longitud y división.
    heuristicas = {nodo: escala * dist(coordenadas[nodo], coordenadas[destino])
                   for nodo in adyacencia}
    if not all(isfinite(h) for h in heuristicas.values()):
        return {nodo: 0.0 for nodo in adyacencia}, 0.0
    return heuristicas, escala


def ejecutar_a_estrella(adyacencia: Adyacencia, origen, destino,
                       posiciones=None, modo_heuristica='euclidiana') -> ResultadoAEstrella:
    """Encuentra una ruta mínima dirigida y registra g, h, f y la frontera.

    El modo cero funciona sin posiciones. Si se proporcionan posiciones, se
    validan en ambos modos. Un costo acumulado no representable se rechaza
    explícitamente para no confundirlo con un destino inalcanzable.
    """
    if origen not in adyacencia or destino not in adyacencia:
        raise ValueError('El origen y el destino deben existir en el grafo.')
    conexiones_validas = {}
    for nodo, conexiones in adyacencia.items():
        normalizadas = []
        for conexion in conexiones:
            if conexion.destino not in adyacencia:
                raise ValueError('Una conexión apunta a un nodo inexistente.')
            peso = _numero_finito(conexion.peso, 'A* requiere pesos numéricos finitos y no negativos.')
            if peso < 0:
                raise ValueError('A* requiere pesos numéricos finitos y no negativos.')
            normalizadas.append(Conexion(conexion.destino, conexion.clave, peso))
        conexiones_validas[nodo] = tuple(normalizadas)
    heuristicas, escala = _preparar_heuristica(conexiones_validas, destino, posiciones, modo_heuristica)

    distancias = {nodo: inf for nodo in adyacencia}
    distancias[origen] = 0.0
    valores_f = {nodo: inf for nodo in adyacencia}
    valores_f[origen] = heuristicas[origen]
    predecesores = {}
    aristas_previas = {}
    visitados = set()
    abiertos = {origen}
    pasos = []
    expandidos = 0
    orden = count()  # Los empates nunca comparan los identificadores de nodo.
    pendientes = [(valores_f[origen], next(orden), 0.0, origen)]

    def registrar(tipo, descripcion, actual=None, arista=None, ruta=(), aristas_ruta=()):
        pasos.append(PasoAEstrella(
            tipo, descripcion, actual, arista, distancias.copy(),
            predecesores.copy(), frozenset(visitados), ruta, aristas_ruta,
            heuristicas=heuristicas.copy(), valores_f=valores_f.copy(),
            abiertos=frozenset(abiertos),
        ))

    def resultado(encontrado, ruta=(), aristas_ruta=()):
        return ResultadoAEstrella(
            origen, destino, distancias[destino], ruta, aristas_ruta,
            tuple(pasos), encontrado, heuristicas.copy(), escala, expandidos,
        )

    registrar('inicio', f'Iniciar A* en {origen}: g = 0; h = {heuristicas[origen]:g}; '
              f'f = g + h = {valores_f[origen]:g}.', origen)
    while pendientes:
        _, _, distancia, actual = heappop(pendientes)
        if actual in visitados or distancia != distancias[actual]:
            continue
        abiertos.remove(actual)
        visitados.add(actual)
        expandidos += 1
        registrar('seleccionar', f'Seleccionar {actual}, el abierto de menor f: '
                  f'g = {distancia:g}; h = {heuristicas[actual]:g}; '
                  f'f = {valores_f[actual]:g}.', actual)
        if actual == destino:
            ruta = [destino]
            aristas_ruta = []
            while ruta[-1] != origen:
                arista = aristas_previas[ruta[-1]]
                aristas_ruta.append(arista)
                ruta.append(arista.origen)
            ruta = tuple(reversed(ruta))
            aristas_ruta = tuple(reversed(aristas_ruta))
            registrar('fin', f'Ruta {" → ".join(map(str, ruta))}. Costo total: {distancia:g}.',
                      actual, ruta=ruta, aristas_ruta=aristas_ruta)
            return resultado(True, ruta, aristas_ruta)

        for conexion in conexiones_validas[actual]:
            vecino = conexion.destino
            arista = Arista(actual, vecino, conexion.clave, conexion.peso)
            registrar('examinar', f'Examinar {actual} → {vecino}, peso {conexion.peso:g}.', actual, arista)
            candidato = distancia + conexion.peso
            if not isfinite(candidato):
                raise ValueError('La suma de costos desborda el rango numérico.')
            anterior = distancias[vecino]
            if candidato < anterior:
                valor_f = candidato + heuristicas[vecino]
                if not isfinite(valor_f):
                    raise ValueError('La suma g + h desborda el rango numérico.')
                distancias[vecino] = candidato
                valores_f[vecino] = valor_f
                predecesores[vecino] = actual
                aristas_previas[vecino] = arista
                visitados.discard(vecino)
                abiertos.add(vecino)
                heappush(pendientes, (valor_f, next(orden), candidato, vecino))
                antes = '∞' if anterior == inf else f'{anterior:g}'
                registrar('actualizar', f'{vecino}: g {antes} → {candidato:g}; '
                          f'h = {heuristicas[vecino]:g}; f = {valor_f:g}; predecesor {actual}.', actual, arista)
            else:
                registrar('descartar', f'g = {candidato:g} no mejora g = {anterior:g} de {vecino}.', actual, arista)

    registrar('sin_ruta', f'No existe una ruta de {origen} a {destino}.')
    return resultado(False)
