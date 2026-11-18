"""Construcción de las dos variantes del mapa dirigido de grafo_final.jpeg."""
from pathlib import Path
import json
import networkx as nx

BASE = Path(__file__).resolve().parent
from modelos.datos_grafo import POSICIONES, ARISTAS


def crear_grafo():
    """Carga los datos en un MultiDiGraph dirigido, sin dibujarlo.

    `pixel`: (x, y) desde la esquina superior izquierda de la imagen.
    `pos`: (x, -y) en un sistema cartesiano, conservando la distribución.
    """
    grafo = nx.MultiDiGraph(imagen='grafo_final.jpeg', dimensiones=(1600, 977))
    for nodo, (x, y) in POSICIONES.items():
        grafo.add_node(nodo, valor=nodo, pos=(x, -y), pixel=(x, y))
    for origen, destino, peso in ARISTAS:
        grafo.add_edge(origen, destino, weight=peso, valor=peso)
    return grafo


def crear_grafo_positivo():
    """Copia independiente con los mismos nodos y pesos en valor absoluto."""
    grafo = crear_grafo()
    for _, _, datos in grafo.edges(data=True):
        datos['weight'] = abs(datos['weight'])
        datos['valor'] = datos['weight']
    return grafo


if __name__ == '__main__':
    G = crear_grafo()
    salida = BASE / 'grafo_datos.json'
    salida.write_text(
        json.dumps(nx.node_link_data(G), ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f'Grafo cargado: {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas.')
    print(f'Datos guardados en {salida}')
