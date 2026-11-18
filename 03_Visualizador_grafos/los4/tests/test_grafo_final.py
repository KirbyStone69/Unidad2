"""Contrato del mapa final: flechas, multiplicidad, posiciones y variantes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
import networkx as nx
from grafo import crear_grafo, crear_grafo_positivo
from modelos.matrices import construir_matrices


class GrafoFinalTests(unittest.TestCase):
    def test_mapa_es_dirigido_con_30_nodos_y_63_arcos(self):
        g = crear_grafo()
        self.assertTrue(g.is_directed())
        self.assertEqual(g.number_of_nodes(), 30)
        self.assertEqual(g.number_of_edges(), 63)
        self.assertIn(666, g)
        self.assertNotIn(66, g)
        self.assertEqual(g.graph['imagen'], 'grafo_final.jpeg')
        self.assertEqual(g.graph['dimensiones'], (1600, 977))
        self.assertEqual(g.nodes[10]['pixel'], (358, 614))

    def test_sentidos_criticos_de_la_imagen(self):
        g = crear_grafo()
        self.assertTrue(g.is_directed())
        esperados = [(21,29,3), (11,21,-2), (11,24,-7), (6,7,10),
                     (1,7,20), (1,0,2), (0,15,8), (15,6,3),
                     (17,2,5), (666,12,7), (666,13,-777), (13,12,9)]
        for u,v,peso in esperados:
            self.assertTrue(g.has_edge(u,v))
            self.assertIn(peso,[d['weight'] for d in g[u][v].values()])
            self.assertFalse(g.has_edge(v,u))
        self.assertEqual(g.number_of_edges(0,15),1)
        self.assertEqual(sorted(d['weight'] for d in g[12][16].values()),[3,16])
        self.assertFalse(g.has_edge(16,12))

    def test_positivo_solo_cambia_signos_conserva_datos_y_es_independiente(self):
        a,b=crear_grafo(),crear_grafo_positivo()
        self.assertTrue(a.is_directed() and b.is_directed())
        self.assertEqual(list(a.nodes(data=True)),list(b.nodes(data=True)))
        self.assertEqual(list(a.edges(keys=True)),list(b.edges(keys=True)))
        for u,v,k,d in a.edges(keys=True,data=True):
            self.assertEqual(b[u][v][k]['weight'],abs(d['weight']))
            self.assertEqual(b[u][v][k]['valor'],abs(d['valor']))
        b[666][13][0]['weight']=0
        self.assertEqual(a[666][13][0]['weight'],-777)

    def test_matrices_dirigidas_no_inventan_arcos_inversos(self):
        g=nx.MultiDiGraph()
        g.add_edge(0,1,weight=1)
        g.add_edge(0,1,weight=3)
        g.add_edge(1,0,weight=2)
        m=construir_matrices(g)
        self.assertEqual(m.adyacencia,((0,2),(1,0)))
        self.assertEqual(m.incidencia,((-1,-1,1),(1,1,-1)))

    def test_escena_preserva_opuestos_paralelas_y_flechas(self):
        from PyQt6.QtWidgets import QApplication
        from interfaz.escena import EscenaGrafo
        app=QApplication.instance() or QApplication([])
        g=nx.MultiDiGraph()
        g.add_node(0,valor=0,pixel=(100,100))
        g.add_node(1,valor=1,pixel=(400,100))
        g.add_edge(0,1,weight=1)
        g.add_edge(0,1,weight=3)
        g.add_edge(1,0,weight=2)
        e=EscenaGrafo()
        e.cargar(g)
        self.assertEqual(len(e.aristas),3)
        self.assertNotEqual(e.identificador(0,1,0),e.identificador(1,0,0))
        self.assertTrue(all(a.flecha is not None for a in e.aristas.values()))
        self.assertNotEqual(e.aristas[e.identificador(0,1,0)].item.path(),e.aristas[e.identificador(1,0,0)].item.path())
        e.clear()


if __name__=='__main__': unittest.main()
