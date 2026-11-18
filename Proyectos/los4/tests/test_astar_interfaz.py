"""A* presenta su propia traza sobre un mapa dirigido pequeño y verificable."""
import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import networkx as nx
from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox


def grafo_de_prueba(negativo=False):
    grafo = nx.MultiDiGraph()
    for nodo in range(3):
        grafo.add_node(nodo, valor=nodo, pixel=(100 * nodo, 0))
    grafo.add_edge(0, 1, weight=-2 if negativo else 2)
    grafo.add_edge(1, 2, weight=2)
    return grafo


class AEstrellaInterfazTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Un paquete todavía ausente produce un fallo explícito de funcionalidad.
        self.assertIsNotNone(
            importlib.util.find_spec('interfaz.algoritmos.a_estrella'),
            'Falta la interfaz independiente de A*',
        )
        from interfaz.algoritmos.a_estrella import InterfazAEstrella
        from algoritmos.a_estrella import ejecutar_a_estrella
        algoritmo = SimpleNamespace(nombre='A*', acepta_negativos=False,
                                    ejecutar=ejecutar_a_estrella)
        self.interfaz = InterfazAEstrella(grafo_de_prueba(), algoritmo)
        self.addCleanup(self.limpiar_interfaz)
        self.interfaz.configuracion.origen.setText('0')
        self.interfaz.configuracion.destino.setText('2')

    def limpiar_interfaz(self):
        self.interfaz.detener()
        self.interfaz.close()
        self.interfaz.deleteLater()
        self.app.processEvents()

    def fila(self, nodo):
        tabla = self.interfaz.tabla
        return next(f for f in range(tabla.rowCount())
                    if tabla.item(f, 0).text() == str(nodo))

    def test_campos_de_texto_y_validacion_de_extremos(self):
        # Detecta coerción silenciosa de un nodo inexistente o texto vacío.
        from interfaz.algoritmos.a_estrella.configuracion import ConfiguracionAEstrella
        configuracion = ConfiguracionAEstrella()
        self.addCleanup(configuracion.deleteLater)
        self.assertIsInstance(configuracion.origen, QLineEdit)
        self.assertIsInstance(configuracion.destino, QLineEdit)
        self.assertEqual(configuracion.origen.text(), '10')
        self.assertEqual(configuracion.destino.text(), '17')
        self.interfaz.configuracion.origen.setText('999')
        with patch.object(QMessageBox, 'warning'):
            self.interfaz.buscar()
        self.assertIsNone(self.interfaz.reproductor.resultado)
        self.assertFalse(self.interfaz.play.isEnabled())
        self.interfaz.configuracion.origen.setText('0')
        self.interfaz.configuracion.destino.setText('')
        with self.assertRaisesRegex(ValueError, 'destino'):
            self.interfaz.configuracion.parametros(self.interfaz.grafo)

    def test_rechaza_negativos_incluso_en_busqueda_programatica(self):
        # Detecta un botón bloqueado que todavía permitiría ejecutar por código.
        self.interfaz.cargar_grafo(grafo_de_prueba(negativo=True))
        self.assertFalse(self.interfaz.ejecutar.isEnabled())
        self.assertFalse(self.interfaz.debug.isEnabled())
        self.interfaz.buscar()
        self.assertIsNone(self.interfaz.reproductor.resultado)
        self.assertIn('pesos', self.interfaz.compatibilidad.text().lower())

    def test_tabla_g_h_f_predecesores_y_abiertos_cerrados(self):
        # Detecta usar distancias euclidianas sin calibrar o intercambiar g con f.
        a = self.interfaz
        a.buscar()
        a.reproductor.pausar()
        resultado = a.reproductor.resultado
        indice = next(i for i, paso in enumerate(resultado.pasos)
                      if 1 in paso.abiertos and 0 in paso.visitados)
        a.reproductor.mostrar(indice)
        fila = self.fila(1)
        self.assertEqual(float(a.tabla.item(fila, 1).text()), 2)
        self.assertAlmostEqual(float(a.tabla.item(fila, 2).text()), 2, places=5)
        self.assertAlmostEqual(float(a.tabla.item(fila, 3).text()), 4, places=5)
        self.assertEqual(a.tabla.item(fila, 4).text(), '0')
        self.assertEqual(a.tabla.item(fila, 5).text(), 'Abierto')
        self.assertEqual(a.tabla.item(self.fila(0), 5).text(), 'Cerrado')
        self.assertIn(resultado.pasos[indice].descripcion, a.comparacion.text())
        self.assertGreater(resultado.escala, 0)
        self.assertLessEqual(resultado.escala, 0.02)
        self.assertIn('0.02', a.escala.text())

    def test_debug_muestra_ruta_costo_y_conserva_la_traza(self):
        # Detecta un debug que omita el último evento o borre la navegación.
        a = self.interfaz
        a.debug.click()
        resultado = a.reproductor.resultado
        self.assertEqual(resultado.ruta, (0, 1, 2))
        self.assertEqual(resultado.distancia, 4)
        self.assertEqual(a.reproductor.indice, len(resultado.pasos) - 1)
        self.assertFalse(a.reproductor.timer.isActive())
        self.assertIn('4', a.resultado.text())
        self.assertIn('0 → 1 → 2', a.resultado.text())
        self.assertTrue(a.recorrido.timer.isActive())
        a.atras.click()
        self.assertEqual(a.reproductor.indice, len(resultado.pasos) - 2)
        self.assertFalse(a.celebracion.timer.isActive())
        a.reiniciar.click()
        self.assertEqual(a.reproductor.indice, 0)
        a.adelante.click()
        self.assertEqual(a.reproductor.indice, 1)

    def test_destino_inalcanzable_no_parpadea(self):
        # Detecta invertir arcos o celebrar un resultado que carece de ruta.
        a = self.interfaz
        a.configuracion.origen.setText('2')
        a.configuracion.destino.setText('0')
        a.debug.click()
        self.assertFalse(a.reproductor.resultado.encontrado)
        self.assertIn('inalcanzable', a.resultado.text().lower())
        self.assertFalse(a.celebracion.timer.isActive())

    def test_heuristica_cero_recalcula_los_valores(self):
        # Detecta ignorar el selector o mantener heurísticas de una búsqueda vieja.
        a = self.interfaz
        a.buscar()
        a.configuracion.heuristica.setCurrentIndex(1)
        self.assertIsNone(a.reproductor.resultado)
        self.assertFalse(a.reproductor.timer.isActive())
        a.debug.click()
        self.assertEqual(a.reproductor.resultado.escala, 0)
        self.assertEqual(a.reproductor.resultado.distancia, 4)
        self.assertTrue(all(a.tabla.item(f, 2).text() == '0'
                            for f in range(a.tabla.rowCount())))

    def test_editar_parametros_cancela_y_limpia_estado(self):
        # Detecta animaciones y tablas obsoletas al editar el siguiente cálculo.
        a = self.interfaz
        a.buscar()
        self.assertTrue(a.reproductor.timer.isActive())
        a.configuracion.destino.setText('1')
        self.assertFalse(a.reproductor.timer.isActive())
        self.assertIsNone(a.reproductor.resultado)
        self.assertFalse(a.play.isEnabled())
        self.assertIsNone(a.escena.paso)
        self.assertEqual(a.tabla.item(self.fila(1), 1).text(), '—')

    def test_cambiar_grafo_cancela_ruta_y_detener_pausa(self):
        # Detecta callbacks de la ruta anterior que sobrevivan al cambio de mapa.
        a = self.interfaz
        a.debug.click()
        self.assertTrue(a.recorrido.timer.isActive())
        a.cargar_grafo(grafo_de_prueba())
        self.assertFalse(a.celebracion.timer.isActive())
        self.assertIsNone(a.reproductor.resultado)
        a.buscar()
        a.detener()
        self.assertFalse(a.reproductor.timer.isActive())
        self.assertFalse(a.celebracion.timer.isActive())
        self.assertIsNotNone(a.reproductor.resultado)


if __name__ == '__main__':
    unittest.main()
