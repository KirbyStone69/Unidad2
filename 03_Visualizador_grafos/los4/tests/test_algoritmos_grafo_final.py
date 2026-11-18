"""Contrasta todos los pares del mapa final y verifica negativos aparte."""
import unittest
from math import inf

from algoritmos.a_estrella import ejecutar_a_estrella
from algoritmos.bellman_ford import ejecutar_bellman_ford
from algoritmos.dijkstra import ejecutar_dijkstra
from algoritmos.warshall_floyd import ejecutar_warshall_floyd
from modelos.grafos import cargar_grafos, obtener_adyacencia


def oraculo_por_numero_de_arcos(adyacencia):
    """Programación dinámica síncrona: caminos de hasta N arcos.

    Compara N frente a N−1 sin presuponer que hay o no ciclos negativos;
    propaga sus mejoras para identificar cada par que carece de mínimo.
    """
    distancias, afectados = {}, set()
    for origen in adyacencia:
        anterior = {nodo: 0 if nodo == origen else inf for nodo in adyacencia}
        semillas = set()
        for cantidad in range(1, len(adyacencia) + 1):
            siguiente = anterior.copy()
            for nodo, conexiones in adyacencia.items():
                if anterior[nodo] == inf:
                    continue
                for conexion in conexiones:
                    candidato = anterior[nodo] + conexion.peso
                    if candidato < siguiente[conexion.destino]:
                        siguiente[conexion.destino] = candidato
            if cantidad == len(adyacencia):
                semillas = {nodo for nodo in adyacencia if siguiente[nodo] < anterior[nodo]}
            else:
                anterior = siguiente
        pendientes = list(semillas)
        while pendientes:
            for conexion in adyacencia[pendientes.pop()]:
                if conexion.destino not in semillas:
                    semillas.add(conexion.destino)
                    pendientes.append(conexion.destino)
        for destino in adyacencia:
            distancias[origen, destino] = -inf if destino in semillas else anterior[destino]
            if destino in semillas:
                afectados.add((origen, destino))
    return distancias, frozenset(afectados)


class AlgoritmosGrafoFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafos = cargar_grafos()
        cls.adyacencias = {nombre: obtener_adyacencia(grafo)
                          for nombre, grafo in cls.grafos.items()}
        # Una sola ejecución de Floyd para cada variante del mapa.
        cls.floyd = {nombre: ejecutar_warshall_floyd(adyacencia)
                     for nombre, adyacencia in cls.adyacencias.items()}
        cls.distancias_originales, cls.afectados_originales = oraculo_por_numero_de_arcos(
            cls.adyacencias['original'])
        cls.bellman_original = {
            origen: ejecutar_bellman_ford(cls.adyacencias['original'], origen)
            for origen in cls.adyacencias['original']
        }

    def test_a_estrella_dijkstra_y_floyd_coinciden_en_900_pares_positivos(self):
        grafo = self.grafos['positivo']
        adyacencia = self.adyacencias['positivo']
        posiciones = {nodo: datos['pixel'] for nodo, datos in grafo.nodes(data=True)}
        pares = 0
        for origen in adyacencia:
            for destino in adyacencia:
                with self.subTest(origen=origen, destino=destino):
                    a = ejecutar_a_estrella(adyacencia, origen, destino, posiciones)
                    d = ejecutar_dijkstra(adyacencia, origen, destino)
                    costo_floyd = self.floyd['positivo'].consultar(origen, destino)[0]
                    self.assertEqual(a.distancia, d.distancia)
                    self.assertEqual(a.distancia, costo_floyd)
                    self.assertEqual(a.encontrado, d.encontrado)
                    if a.encontrado:
                        self.assertEqual(a.ruta[0], origen)
                        self.assertEqual(a.ruta[-1], destino)
                        self.assertEqual(sum(arista.peso for arista in a.aristas_ruta), a.distancia)
                        for arista in a.aristas_ruta:
                            self.assertEqual(grafo[arista.origen][arista.destino][arista.clave]['weight'],
                                             arista.peso)
                    else:
                        self.assertEqual((a.ruta, a.aristas_ruta), ((), ()))
                pares += 1
        self.assertEqual(pares, 900)

    def test_bellman_y_floyd_coinciden_en_900_pares_originales(self):
        adyacencia = self.adyacencias['original']
        grafo = self.grafos['original']
        floyd = self.floyd['original']
        indices = {nodo: indice for indice, nodo in enumerate(floyd.nodos)}
        self.assertEqual(floyd.afectados, self.afectados_originales)
        pares = 0
        for origen in adyacencia:
            bellman = self.bellman_original[origen]
            afectados = frozenset(destino for u, destino in self.afectados_originales if u == origen)
            self.assertEqual(bellman.afectados, afectados)
            self.assertEqual(bellman.ciclo_negativo, bool(afectados))
            for destino in adyacencia:
                with self.subTest(origen=origen, destino=destino):
                    esperado = self.distancias_originales[origen, destino]
                    self.assertEqual(bellman.distancias[destino], esperado)
                    self.assertEqual(floyd.distancias[indices[origen]][indices[destino]], esperado)
                    if esperado == -inf:
                        with self.assertRaises(ValueError):
                            floyd.consultar(origen, destino)
                    else:
                        costo, ruta, aristas = floyd.consultar(origen, destino)
                        self.assertEqual(costo, esperado)
                        if costo == inf:
                            self.assertEqual((ruta, aristas), ((), ()))
                        else:
                            self.assertEqual((ruta[0], ruta[-1]), (origen, destino))
                            self.assertEqual(sum(arista.peso for arista in aristas), costo)
                            for arista in aristas:
                                self.assertEqual(grafo[arista.origen][arista.destino][arista.clave]['weight'],
                                                 arista.peso)
                pares += 1
        self.assertEqual(pares, 900)


if __name__ == '__main__':
    unittest.main()
