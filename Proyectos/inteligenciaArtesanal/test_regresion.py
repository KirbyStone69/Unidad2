import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import arbol
import arbol as motor


class RegresionTests(unittest.TestCase):
    def test_regresion_evoluciona_una_recta_compuesta(self):
        self.assertTrue(hasattr(motor, 'BusquedaGrafica'), 'Falta regresión')
        busqueda = motor.BusquedaGrafica(
            motor.DatosGrafica([-2, -1, 0, 1, 2], [-3, -1, 1, 3, 5]), semilla=7)
        busqueda.avanzar(1)
        inicial = busqueda.mejor.mse
        busqueda.avanzar(3000)
        self.assertLess(busqueda.mejor.mse, inicial)
        self.assertEqual(busqueda.mejor.mse, 0)
        self.assertTrue(busqueda.mutaciones > 0)
        self.assertTrue(busqueda.cruces > 0)

    def test_operaciones_vectoriales_coinciden_con_calculo_escalar(self):
        casos = {'+': (2, 3), '−': (2, 3), '×': (2, 3), '/': (7, 2),
                 '%': (-7, 3), '^': (-2, 3), '√': (9,), 'ln': (2,),
                 'sin': (0.5,), 'cos': (0.5,), 'tan': (0.5,)}
        for simbolo, valores in casos.items():
            op = motor.OPERACIONES_VALIDAS[simbolo]
            self.assertTrue(hasattr(op, 'aplicar_vector'), 'Falta evaluación vectorial')
            self.assertAlmostEqual(float(op.aplicar_vector(*valores)), op.aplicar(*valores))

    def test_mse_nmse_y_denominador_cero(self):
        self.assertTrue(hasattr(motor, 'calcular_errores'), 'Faltan métricas')
        mse, nmse = motor.calcular_errores([1, 2, 3], [2, 2, 1])
        self.assertAlmostEqual(mse, 5/3)
        self.assertAlmostEqual(nmse, 5/14)
        self.assertEqual(motor.calcular_errores([0, 0], [1, -1]), (1, None))
        for esperado, predicho in [([], []), ([1], [1, 2]), ([1], [float('inf')])]:
            with self.assertRaises(ValueError):
                motor.calcular_errores(esperado, predicho)

    def test_carga_csv_y_errores(self):
        self.assertTrue(hasattr(arbol, 'cargar_csv'), 'Falta cargar CSV')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'puntos.csv'
            p.write_text('x,y\n-1,1\n0,0\n2,4\n')
            datos = arbol.cargar_csv(p)
            self.assertEqual(list(datos.x), [-1, 0, 2])
            self.assertEqual(list(datos.y), [1, 0, 4])
            for contenido in ['a,b\n1,2\n', 'x,y\n', 'x,y\n1,nan\n', 'x,y\n1,texto\n']:
                p.write_text(contenido)
                with self.assertRaises(ValueError):
                    arbol.cargar_csv(p)

    def test_busqueda_ajusta_todos_los_puntos_y_rechaza_dominios(self):
        self.assertTrue(hasattr(motor, 'BusquedaGrafica'), 'Falta regresión')
        datos = motor.DatosGrafica([-2, -1, 0, 1, 2], [4, 1, 0, 1, 4])
        busqueda = motor.BusquedaGrafica(datos, semilla=7)
        for _ in range(20):
            busqueda.avanzar()
        self.assertEqual(busqueda.mejor.mse, 0)
        self.assertEqual(busqueda.mejor.nmse, 0)
        self.assertIn('x', busqueda.mejor.etiquetas.values())
        self.assertFalse(busqueda.terminada)
        pred = motor.predecir(busqueda.mejor.etiquetas, busqueda.mejor.hijos, datos.x)
        self.assertEqual(list(pred), [4, 1, 0, 1, 4])
        with self.assertRaises(ValueError):
            motor.predecir({0: '√', 1: 'x'}, {0: (1,)}, datos.x)


class GuiRegresionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_no_anima_aproximaciones_y_aleatorio(self):
        v = arbol.VentanaArbol(cargar_automatico=False)
        v.objetivo.setValue(12345.6789)
        v.generar()
        v.procesar_busqueda()
        self.assertFalse(v.temporizador.isActive())
        v.cancelar_busqueda()
        self.assertFalse(v.temporizador.isActive())
        self.assertTrue(hasattr(v, 'boton_aleatorio'), 'Falta botón aleatorio')
        v.objetivo.setValue(1000000)
        v.boton_aleatorio.click()
        self.assertNotEqual(v.objetivo.value(), 1000000)
        self.assertTrue(v.objetivo.isEnabled())
        v.close()

    def test_csv_grafica_y_animacion_rapida_al_encontrar(self):
        self.assertTrue(hasattr(arbol.VentanaArbol, 'abrir_csv'), 'Falta CSV en GUI')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'datos.csv'
            p.write_text('x,y\n-2,4\n-1,1\n0,0\n1,1\n2,4\n')
            v = arbol.VentanaArbol(cargar_automatico=False)
            v.abrir_csv(p)
            self.assertEqual(len(v.datos.x), 5)
            self.assertFalse(v.objetivo.isEnabled())
            v.generar()
            for _ in range(20):
                v.procesar_busqueda()
            self.assertEqual(v.busqueda.mejor.mse, 0)
            self.assertTrue(v.reloj_busqueda.isActive())
            self.assertEqual(v.temporizador.interval(), 100)
            self.assertIn('MSE', v.mensaje.text())
            self.assertIn('NMSE', v.mensaje.text())
            self.assertGreaterEqual(len(v.grafica.ax.lines), 1)
            v.cancelar_busqueda()
            while v.temporizador.isActive():
                v.avanzar()
            v.close()


if __name__ == '__main__':
    unittest.main()
