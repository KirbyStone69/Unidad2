"""Ocho casos enfocados: captura, caché, cancelación, A* y velocidad."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import networkx as nx
from PyQt6.QtWidgets import QApplication
from algoritmos.registro import ALGORITMOS
from interfaz.registro import INTERFACES
from interfaz.tema import ESTILO, NEON


class InformesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(ESTILO)

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.vistas = []

    def tearDown(self):
        for v in self.vistas:
            if getattr(v, 'informe', None):
                v.informe.cancelar()
            v.detener()
            v.close()
            v.deleteLater()
        self.app.processEvents()
        self.temporal.cleanup()

    def vista(self, identificador):
        algoritmo = next(a for a in ALGORITMOS if a.identificador == identificador)
        grafo = nx.MultiDiGraph()
        for n, pixel in enumerate(((80, 80), (240, 80), (400, 180))):
            grafo.add_node(n, valor=n, pixel=pixel)
        grafo.add_edge(0, 1, weight=-1 if identificador == 'bellman_ford' else 1)
        grafo.add_edge(1, 2, weight=2)
        v = INTERFACES[identificador](grafo, algoritmo)
        v.resize(1100, 800)
        v.show()
        self.vistas.append(v)
        if identificador == 'dijkstra':
            c = v.panel.configuracion
        elif identificador == 'warshall_floyd':
            c = v
        else:
            c = v.configuracion
        c.origen.setText('0')
        c.destino.setText('2')
        self.app.processEvents()
        return v

    def instalar(self, v):
        from interfaz.informes import GrabadorInforme
        v.informe = GrabadorInforme(v, Path(self.temporal.name))
        return v.informe

    def completar(self, g):
        while g.activo:
            g.avanzar()

    @patch('exportacion.informes.EscritorPDF.PAGINAS_BLOQUE', 2)
    def test_pdf_y_capturas_de_todos_los_eventos_en_cuatro_interfaces(self):
        for identificador in ('dijkstra', 'bellman_ford', 'warshall_floyd', 'a_estrella'):
            with self.subTest(algoritmo=identificador):
                v = self.vista(identificador)
                g = self.instalar(v)
                if identificador in ('bellman_ford', 'warshall_floyd'):
                    v.buscar(debug=True)
                elif identificador == 'a_estrella':
                    v.buscar(directo=True)
                else:
                    v.buscar()
                self.assertTrue(g.activo)
                resultado = v.reproductor.resultado
                self.completar(g)
                self.assertEqual(len(list(g.carpeta_capturas.glob('paso_*.jpg'))), len(resultado.pasos))
                datos = g.ruta_pdf.read_bytes()
                self.assertTrue(datos.startswith(b'%PDF'))
                self.assertTrue(datos.rstrip().endswith(b'%%EOF'))
                self.assertEqual(len(re.findall(rb'/Type\s*/Page\b', datos)), len(resultado.pasos))
                self.assertEqual(v.reproductor.indice, len(resultado.pasos) - 1)
                self.assertFalse(g.ruta_pdf.with_suffix('.bloques').exists())

    def test_cache_evita_calculo_y_parametros_diferentes_no_colisionan(self):
        v = self.vista('a_estrella'); g = self.instalar(v)
        v.buscar(directo=True); self.completar(g)
        with patch('algoritmos.a_estrella.heappop', side_effect=AssertionError('no recalcular')):
            v.buscar(directo=True)
        self.assertFalse(g.activo)
        self.assertIn('PDF existente', g.estado)
        v.configuracion.destino.setText('1')
        v.buscar(directo=True)
        self.assertTrue(g.activo)

    def test_cancelar_no_publica_pdf_incompleto(self):
        v = self.vista('dijkstra'); g = self.instalar(v)
        v.buscar(); g.avanzar(); g.cancelar()
        self.assertFalse(g.activo)
        self.assertFalse(g.ruta_pdf.exists())
        self.assertFalse(g.temporal_pdf.exists())
        v.buscar()
        self.assertTrue(g.activo)
        from pikepdf import PikepdfError
        with patch('exportacion.informes.EscritorPDF.PAGINAS_BLOQUE', 2), \
                patch('pikepdf.Job', side_effect=PikepdfError('Unión fallida')):
            self.completar(g)
        self.assertIn('Error al crear informe', g.estado)
        self.assertFalse(g.ruta_pdf.exists())
        self.assertFalse(g.ruta_pdf.with_suffix('.bloques').exists())

    def test_capturas_conservan_colores_y_particula_de_busqueda(self):
        v = self.vista('a_estrella'); g = self.instalar(v)
        v.buscar(directo=True)
        self.completar(g)
        capturas = sorted(g.carpeta_capturas.glob('paso_*.jpg'))
        self.assertNotEqual(capturas[0].read_bytes(), capturas[-1].read_bytes())
        self.assertEqual(v.escena.nodos[2].brush().color().name(), NEON)
        self.assertEqual(v.escena.paso.ruta, (0, 1, 2))

    def test_a_estrella_recorrido_final_y_cinco_parpadeos(self):
        v = self.vista('a_estrella')
        v.buscar(directo=True)
        self.assertTrue(v.recorrido.timer.isActive())
        for _ in range(100):
            v.recorrido.avanzar()
        self.assertFalse(v.recorrido.timer.isActive())
        self.assertTrue(v.celebracion.timer.isActive())
        for _ in range(10):
            v.celebracion.avanzar()
        self.assertEqual(v.celebracion.ciclos_completos, 5)
        self.assertEqual(v.escena.nodos[2].brush().color().name(), NEON)

    def test_velocidad_maxima_mas_rapida_en_cuatro_algoritmos(self):
        for identificador in ('dijkstra', 'a_estrella', 'bellman_ford', 'warshall_floyd'):
            v = self.vista(identificador)
            v.cambiar_velocidad(10)
            self.assertLessEqual(v.reproductor.duracion, 20)
            self.assertLessEqual(v.reproductor.timer.interval(), 20)

    def test_clave_distingue_pesos_direccion_y_parametros(self):
        from exportacion.informes import clave_informe
        v = self.vista('a_estrella')
        clave = clave_informe('a_estrella', v.grafo, {'origen': 0, 'destino': 2})
        self.assertNotEqual(clave, clave_informe('a_estrella', v.grafo.reverse(), {'origen': 0, 'destino': 2}))
        self.assertNotEqual(clave, clave_informe('a_estrella', v.grafo, {'origen': 1, 'destino': 2}))
        v.grafo[0][1][0]['weight'] = 3
        self.assertNotEqual(clave, clave_informe('a_estrella', v.grafo, {'origen': 0, 'destino': 2}))

    def test_cambio_parametros_cancela_grabacion_y_recorrido(self):
        v = self.vista('a_estrella'); g = self.instalar(v)
        v.buscar(directo=True)
        v.configuracion.destino.setText('1')
        self.assertFalse(g.activo)
        self.assertFalse(v.recorrido.timer.isActive())
        self.assertFalse(g.ruta_pdf.exists())
