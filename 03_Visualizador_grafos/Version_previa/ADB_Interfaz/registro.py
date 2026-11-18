"""Asocia cada algoritmo a su interfaz completa, sin imponerle controles o tablas."""
from .algoritmos.a_estrella import InterfazAEstrella
from .algoritmos.dijkstra import InterfazDijkstra
from .algoritmos.bellman_ford import InterfazBellmanFord
from .algoritmos.warshall_floyd import InterfazWarshallFloyd

INTERFACES = {'a_estrella': InterfazAEstrella, 'dijkstra': InterfazDijkstra, 'bellman_ford': InterfazBellmanFord, 'warshall_floyd': InterfazWarshallFloyd}
