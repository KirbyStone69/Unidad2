"""A* propio sobre grafos dirigidos pequeños y verificables a mano."""
import copy
import unittest
from math import inf, isfinite

from algoritmos.a_estrella import ejecutar_a_estrella
from algoritmos.tipos import Conexion, Paso, Resultado


class AEstrellaTests(unittest.TestCase):
    def setUp(self):
        self.ejecutar = ejecutar_a_estrella

    def test_ruta_optima_con_euclidiana_escalada(self):
        adyacencia = {'S': (Conexion('G', 'directa', 9), Conexion('A', 'inicio', 2)),
                      'A': (Conexion('G', 'final', 2),), 'G': ()}
        posiciones = {'S': (0, 0), 'A': (1, 0), 'G': (2, 0)}
        resultado = self.ejecutar(adyacencia, 'S', 'G', posiciones)
        self.assertIsInstance(resultado, Resultado)
        self.assertTrue(resultado.encontrado)
        self.assertEqual(resultado.ruta, ('S', 'A', 'G'))
        self.assertEqual(resultado.distancia, 4)
        self.assertEqual([a.clave for a in resultado.aristas_ruta], ['inicio', 'final'])
        self.assertAlmostEqual(resultado.escala, 2)
        self.assertLess(resultado.escala, 2)
        self.assertLessEqual(resultado.heuristicas['S'], 4)
        self.assertAlmostEqual(resultado.heuristicas['A'], 2)
        self.assertEqual(resultado.heuristicas['G'], 0)

    def test_escala_considera_arcos_de_componentes_ajenos(self):
        adyacencia = {'S': (Conexion('G', 0, 4),), 'G': (),
                      'X': (Conexion('Y', 0, 0.2),), 'Y': ()}
        posiciones = {'S': (0, 0), 'G': (2, 0), 'X': (10, 10), 'Y': (20, 10)}
        resultado = self.ejecutar(adyacencia, 'S', 'G', posiciones)
        self.assertAlmostEqual(resultado.escala, 0.02)
        self.assertAlmostEqual(resultado.heuristicas['S'], 0.04)
        for nodo, conexiones in adyacencia.items():
            for conexion in conexiones:
                self.assertLessEqual(resultado.heuristicas[nodo],
                                     conexion.peso + resultado.heuristicas[conexion.destino])

    def test_heuristica_reduce_expansiones_frente_a_cero(self):
        adyacencia = {'S': (Conexion('A', 0, 1), Conexion('B', 0, 1)),
                      'A': (Conexion('G', 0, 1),), 'B': (Conexion('X', 0, 1),),
                      'X': (Conexion('G', 0, 4),), 'G': ()}
        posiciones = {'S': (0, 0), 'A': (1, 0), 'G': (2, 0),
                      'B': (0, 1), 'X': (-1, 1)}
        informada = self.ejecutar(adyacencia, 'S', 'G', posiciones)
        cero = self.ejecutar(adyacencia, 'S', 'G', modo_heuristica='cero')
        self.assertEqual(informada.distancia, 2)
        self.assertEqual(cero.distancia, 2)
        self.assertEqual(informada.expandidos, 3)
        self.assertEqual(cero.expandidos, 4)
        self.assertEqual(cero.escala, 0)
        self.assertEqual(set(cero.heuristicas.values()), {0})

    def test_paralelas_guardan_claves_y_descartan_entradas_viejas(self):
        adyacencia = {'S': (Conexion('A', 'cara', 9), Conexion('A', 'barata', 2),
                            Conexion('B', 0, 10)),
                      'A': (Conexion('B', 'mejora', 1),), 'B': (), 'G': ()}
        resultado = self.ejecutar(adyacencia, 'S', 'G', modo_heuristica='cero')
        self.assertEqual(resultado.expandidos, 3)
        self.assertEqual(resultado.pasos[-1].distancias['B'], 3)
        ruta = self.ejecutar(adyacencia, 'S', 'B', modo_heuristica='cero')
        self.assertEqual(ruta.ruta, ('S', 'A', 'B'))
        self.assertEqual([a.clave for a in ruta.aristas_ruta], ['barata', 'mejora'])
        self.assertEqual(sum(a.peso for a in ruta.aristas_ruta), 3)

    def test_empates_y_ciclos_cero_no_comparan_identificadores(self):
        adyacencia = {0: (Conexion('A', 0, 0), Conexion((2,), 0, 0)),
                      'A': (Conexion(0, 0, 0), Conexion('G', 0, 1)),
                      (2,): (Conexion('G', 0, 1),), 'G': ()}
        resultado = self.ejecutar(adyacencia, 0, 'G', modo_heuristica='cero')
        self.assertEqual(resultado.distancia, 1)
        self.assertEqual(resultado.ruta, (0, 'A', 'G'))
        self.assertEqual(resultado.expandidos, 4)

    def test_cero_longitud_y_peso_cero_tienen_heuristica_segura(self):
        adyacencia = {'S': (Conexion('A', 0, 0),), 'A': (Conexion('G', 0, 2),), 'G': ()}
        posiciones = {'S': (0, 0), 'A': (1, 0), 'G': (2, 0)}
        resultado = self.ejecutar(adyacencia, 'S', 'G', posiciones)
        self.assertEqual(resultado.escala, 0)
        self.assertEqual(resultado.distancia, 2)
        coincidentes = {nodo: (0, 0) for nodo in adyacencia}
        resultado = self.ejecutar(adyacencia, 'S', 'G', coincidentes)
        self.assertEqual(resultado.escala, 0)
        self.assertEqual(set(resultado.heuristicas.values()), {0})

    def test_sin_ruta_respeta_direccion_y_termina_con_evento(self):
        adyacencia = {'S': (), 'G': (Conexion('S', 0, 1),)}
        resultado = self.ejecutar(adyacencia, 'S', 'G', modo_heuristica='cero')
        self.assertFalse(resultado.encontrado)
        self.assertEqual(resultado.distancia, inf)
        self.assertEqual(resultado.ruta, ())
        self.assertEqual(resultado.aristas_ruta, ())
        self.assertEqual(resultado.pasos[-1].tipo, 'sin_ruta')
        self.assertEqual(resultado.expandidos, 1)

    def test_origen_igual_destino(self):
        resultado = self.ejecutar({'S': ()}, 'S', 'S', {'S': (3, 4)})
        self.assertEqual(resultado.distancia, 0)
        self.assertEqual(resultado.ruta, ('S',))
        self.assertEqual(resultado.aristas_ruta, ())
        self.assertEqual(resultado.expandidos, 1)
        self.assertEqual(resultado.pasos[-1].tipo, 'fin')

    def test_eventos_contienen_g_h_f_y_abiertos_con_instantaneas(self):
        adyacencia = {'S': (Conexion('A', 'sa', 2), Conexion('G', 'sg', 9)),
                      'A': (Conexion('S', 'as', 2), Conexion('G', 'ag', 2)), 'G': ()}
        posiciones = {'S': (0, 0), 'A': (1, 0), 'G': (2, 0)}
        antes = copy.deepcopy((adyacencia, posiciones))
        resultado = self.ejecutar(adyacencia, 'S', 'G', posiciones)
        self.assertEqual((adyacencia, posiciones), antes)
        inicio, fin = resultado.pasos[0], resultado.pasos[-1]
        self.assertEqual(inicio.tipo, 'inicio')
        self.assertEqual(inicio.distancias, {'S': 0, 'A': inf, 'G': inf})
        self.assertEqual(inicio.predecesores, {})
        self.assertEqual(inicio.visitados, frozenset())
        self.assertEqual(inicio.abiertos, frozenset({'S'}))
        self.assertEqual(fin.ruta, resultado.ruta)
        self.assertEqual(fin.aristas_ruta, resultado.aristas_ruta)
        self.assertEqual(fin.distancias['G'], 4)
        self.assertEqual({p.tipo for p in resultado.pasos},
                         {'inicio', 'seleccionar', 'examinar', 'actualizar', 'descartar', 'fin'})
        for paso in resultado.pasos:
            self.assertIsInstance(paso, Paso)
            self.assertIsInstance(paso.abiertos, frozenset)
            self.assertFalse(paso.abiertos & paso.visitados)
            for nodo in adyacencia:
                self.assertEqual(paso.valores_f[nodo], paso.distancias[nodo] + paso.heuristicas[nodo])
            if paso.tipo == 'seleccionar':
                self.assertIn(paso.actual, paso.visitados)
                self.assertNotIn(paso.actual, paso.abiertos)
        fin.heuristicas['S'] = -100
        fin.distancias['G'] = -100
        self.assertGreater(inicio.heuristicas['S'], 0)
        self.assertEqual(inicio.distancias['G'], inf)
        self.assertGreater(resultado.heuristicas['S'], 0)

    def test_rechaza_pesos_invalidos_antes_de_terminar_en_origen(self):
        for peso in (-1, inf, -inf, float('nan'), '2', None, True, complex(1, 2)):
            with self.subTest(peso=peso), self.assertRaises(ValueError):
                self.ejecutar({'S': (), 'X': (Conexion('X', 0, peso),)},
                              'S', 'S', modo_heuristica='cero')

    def test_rechaza_nodos_inexistentes(self):
        for adyacencia, origen, destino in (({'S': ()}, 'S', 'G'),
                                             ({'S': ()}, 'G', 'S'),
                                             ({'S': (Conexion('X', 0, 1),)}, 'S', 'S')):
            with self.subTest(adyacencia=adyacencia), self.assertRaises(ValueError):
                self.ejecutar(adyacencia, origen, destino, modo_heuristica='cero')

    def test_rechaza_posiciones_incompletas_o_invalidas(self):
        adyacencia = {'S': (Conexion('G', 0, 1),), 'G': ()}
        for posiciones in (None, {}, {'S': (0, 0)}, {'S': (0, 0), 'G': (inf, 0)},
                           {'S': (0, 0), 'G': (0, float('nan'))},
                           {'S': (0, 0), 'G': (1,)}, {'S': (0, 0), 'G': ('1', 2)}):
            with self.subTest(posiciones=posiciones), self.assertRaises(ValueError):
                self.ejecutar(adyacencia, 'S', 'G', posiciones)

    def test_cero_valida_posiciones_si_se_proporcionan(self):
        with self.assertRaises(ValueError):
            self.ejecutar({'S': ()}, 'S', 'S', {'S': (inf, 0)}, modo_heuristica='cero')

    def test_rechaza_modo_desconocido(self):
        with self.assertRaises(ValueError):
            self.ejecutar({'S': ()}, 'S', 'S', modo_heuristica='manhattan')

    def test_rechaza_suma_de_costos_que_desborda(self):
        adyacencia = {'S': (Conexion('A', 0, 1e308),),
                      'A': (Conexion('G', 0, 1e308),), 'G': ()}
        with self.assertRaises(ValueError):
            self.ejecutar(adyacencia, 'S', 'G', modo_heuristica='cero')

    def test_coordenadas_finitas_extremas_no_producen_nan(self):
        adyacencia = {'S': (Conexion('G', 0, 1),), 'G': ()}
        resultado = self.ejecutar(adyacencia, 'S', 'G',
                                  {'S': (-1e308, 0), 'G': (1e308, 0)})
        self.assertEqual(resultado.distancia, 1)
        self.assertTrue(all(isfinite(h) for h in resultado.heuristicas.values()))

    def test_todos_los_pares_con_oraculo_floyd_independiente(self):
        adyacencia = {'A': (Conexion('B', 0, 8), Conexion('B', 1, 2), Conexion('C', 0, 6)),
                      'B': (Conexion('C', 0, 1), Conexion('D', 0, 5)),
                      'C': (Conexion('A', 0, 4), Conexion('D', 0, 0)),
                      'D': (), 'E': ()}
        posiciones = {'A': (0, 0), 'B': (2, 0), 'C': (3, 1), 'D': (3, 1), 'E': (7, 2)}
        distancias = {(u, v): 0 if u == v else inf for u in adyacencia for v in adyacencia}
        for u, conexiones in adyacencia.items():
            for conexion in conexiones:
                distancias[u, conexion.destino] = min(distancias[u, conexion.destino], conexion.peso)
        for k in adyacencia:
            for u in adyacencia:
                for v in adyacencia:
                    distancias[u, v] = min(distancias[u, v], distancias[u, k] + distancias[k, v])
        for modo in ('euclidiana', 'cero'):
            for origen in adyacencia:
                for destino in adyacencia:
                    with self.subTest(modo=modo, origen=origen, destino=destino):
                        resultado = self.ejecutar(adyacencia, origen, destino, posiciones, modo)
                        self.assertEqual(resultado.distancia, distancias[origen, destino])
                        if resultado.encontrado:
                            self.assertEqual(sum(a.peso for a in resultado.aristas_ruta), resultado.distancia)
                            for arista in resultado.aristas_ruta:
                                self.assertIn(Conexion(arista.destino, arista.clave, arista.peso),
                                              adyacencia[arista.origen])


if __name__ == '__main__':
    unittest.main()
