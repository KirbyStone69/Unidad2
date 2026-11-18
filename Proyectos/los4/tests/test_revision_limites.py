"""Tres regresiones concretas de la revisión de casos límite."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from math import inf
from pathlib import Path
from algoritmos.bellman_ford import ejecutar_bellman_ford
from algoritmos.tipos import Conexion
from modelos.ejemplo_floyd import cargar_ejemplo_floyd


class RevisionLimitesTests(unittest.TestCase):
    def test_ciclo_negativo_con_nodo_none_conserva_testigo(self):
        resultado = ejecutar_bellman_ford({None: (Conexion(None, 0, -1),)}, None)
        self.assertTrue(resultado.ciclo_negativo)
        self.assertEqual(resultado.ciclo, (None, None))
        self.assertEqual(sum(a.peso for a in resultado.aristas_ciclo), -1)
        self.assertEqual(resultado.distancia, -inf)
        self.assertEqual(resultado.afectados, frozenset({None}))
        self.assertEqual(resultado.pasos[-1].predecesores, {})

    def test_xlsx_danado_devuelve_error_controlado(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / 'ejemplo.xlsx'
            archivo.write_bytes(b'Este archivo no es un contenedor XLSX valido.')
            with self.assertRaisesRegex(ValueError, 'No se pudo leer el ejemplo XLSX'):
                cargar_ejemplo_floyd(archivo)

    def test_retroceder_en_floyd_limpia_consulta_y_animacion(self):
        from PyQt6.QtWidgets import QApplication
        from interfaz.ventana import VentanaGrafo
        app = QApplication.instance() or QApplication([])
        ventana = VentanaGrafo(capturar=False)
        try:
            ventana.pestanas.setCurrentIndex(next(i for i, a in enumerate(ventana.algoritmos) if a.identificador == 'warshall_floyd'))
            interfaz = ventana.interfaz_actual
            interfaz.origen.setText('10')
            interfaz.destino.setText('17')
            interfaz.buscar(debug=True)
            resultado = interfaz.reproductor.resultado
            interfaz.consultar_ruta()
            self.assertIn('Costo: 22', interfaz.consulta.text())
            self.assertTrue(interfaz.celebracion.timer.isActive())
            interfaz.reproductor.reiniciar()
            self.assertEqual(interfaz.consulta.text(), 'Consulta pendiente')
            self.assertFalse(interfaz.celebracion.timer.isActive())
            self.assertEqual(interfaz.escena.paso.ruta, ())
            self.assertEqual(interfaz.reproductor.indice, 0)
            self.assertIs(interfaz.reproductor.resultado, resultado)
        finally:
            ventana.close()
            ventana.deleteLater()
            app.processEvents()


if __name__ == '__main__':
    unittest.main()
