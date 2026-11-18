import math
import os
import random
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import arbol


class MotorTests(unittest.TestCase):
    def test_elite_mejora_una_aproximacion_y_conserva_poblacion_unica(self):
        busqueda = arbol.BusquedaExpresiones(7.123456, semilla=25)
        busqueda.avanzar(1)
        inicial = anterior = busqueda.mejor.error
        for _ in range(80):
            busqueda.avanzar(60)
            self.assertLessEqual(busqueda.mejor.error, anterior)
            anterior = busqueda.mejor.error
        self.assertLess(busqueda.mejor.error, inicial)
        aptitudes = [(c.error, len(c.etiquetas)) for c in busqueda.elite]
        self.assertEqual(aptitudes, sorted(aptitudes))
        firmas = [arbol.escribir_expresion(c.etiquetas, c.hijos) for c in busqueda.elite]
        self.assertEqual(len(firmas), len(set(firmas)))

    def test_elitismo_continuo_no_empeora_y_no_se_detiene_al_acertar(self):
        busqueda = arbol.BusquedaExpresiones(0, semilla=11)
        busqueda.avanzar(60)
        self.assertFalse(busqueda.terminada)
        self.assertEqual(busqueda.mejor.error, 0)
        self.assertTrue(hasattr(busqueda, 'elite'), 'Falta población de élite')
        anterior = (busqueda.mejor.error, len(busqueda.mejor.etiquetas))
        for _ in range(200):
            busqueda.avanzar(60)
            actual = (busqueda.mejor.error, len(busqueda.mejor.etiquetas))
            self.assertLessEqual(actual, anterior)
            anterior = actual
        self.assertGreater(busqueda.intentos, 10000)
        self.assertFalse(busqueda.terminada)
        self.assertLessEqual(len(busqueda.elite), busqueda.tamano_elite)
        self.assertTrue(busqueda.mutaciones > 0)
        self.assertTrue(busqueda.cruces > 0)
        for candidato in busqueda.elite:
            self.assertLessEqual(arbol.validar_arbol(candidato.etiquetas, candidato.hijos), 5)

    def test_variacion_respeta_altura_y_no_modifica_padres(self):
        import arbol as motor
        self.assertTrue(hasattr(motor, 'mutar_arbol'), 'Falta mutación')
        self.assertTrue(hasattr(motor, 'cruzar_arboles'), 'Falta cruce')
        rng = random.Random(20)
        padre = ({0: '+', 1: '2', 2: '3'}, {0: (1, 2)})
        copia = (dict(padre[0]), dict(padre[1]))
        for _ in range(100):
            madre = arbol.generar_arbol(rng, 3)
            for etiquetas, hijos in (motor.mutar_arbol(*padre, rng, 3),
                                      motor.cruzar_arboles(*padre, *madre, rng, 3)):
                self.assertLessEqual(arbol.validar_arbol(etiquetas, hijos), 3)
        self.assertEqual(padre, copia)

    def test_operaciones_y_dominios(self):
        casos = [('+', (2, 3), 5), ('−', (2, 3), -1), ('×', (2, 3), 6),
                 ('/', (7, 2), 3.5), ('%', (7, 3), 1), ('^', (2, 3), 8),
                 ('√', (9,), 3), ('ln', (1,), 0), ('sin', (0,), 0),
                 ('cos', (0,), 1), ('tan', (0,), 0)]
        for simbolo, argumentos, esperado in casos:
            with self.subTest(simbolo=simbolo):
                self.assertAlmostEqual(arbol.OPERACIONES_VALIDAS[simbolo].aplicar(*argumentos), esperado)
        for simbolo, argumentos in [('/', (1, 0)), ('%', (1, 0)), ('√', (-1,)),
                                    ('ln', (0,)), ('^', (-1, 0.5)),
                                    ('tan', (math.pi/2,)), ('+', (1,))]:
            with self.subTest(simbolo=simbolo):
                with self.assertRaises(ValueError):
                    arbol.OPERACIONES_VALIDAS[simbolo].aplicar(*argumentos)

    def test_recorridos_aridad_tamano_y_evaluacion_postorder(self):
        self.assertTrue(hasattr(arbol, 'analizar_arbol'), 'Falta analizar el árbol')
        # (8 - 2) / sqrt(9): las operaciones no conmutativas comprueban el orden.
        etiquetas = {0: '/', 1: '−', 2: '8', 3: '2', 4: '√', 5: '9'}
        hijos = {0: (1, 4), 1: (2, 3), 4: (5,)}
        datos = arbol.analizar_arbol(etiquetas, hijos)
        self.assertEqual(datos['tamano'], 6)
        self.assertEqual(datos['altura'], 2)
        self.assertEqual(datos['aridades'], {0: 2, 1: 2, 2: 0, 3: 0, 4: 1, 5: 0})
        self.assertEqual(datos['preorder'], [0, 1, 2, 3, 4, 5])
        self.assertEqual(datos['inorder'], [2, 1, 3, 0, 5, 4])
        self.assertEqual(datos['postorder'], [2, 3, 1, 5, 4, 0])
        pasos = arbol.evaluar(etiquetas, hijos)
        self.assertEqual([n for n, _ in pasos], datos['postorder'])
        self.assertEqual(pasos[-1][1], 2)

    def test_limites_y_estructura_binaria(self):
        self.assertTrue(hasattr(arbol, 'analizar_arbol'), 'Falta analizar el árbol')
        etiquetas = {0: '√', 1: '√', 2: '9'}
        hijos = {0: (1,), 1: (2,)}
        self.assertEqual(arbol.validar_arbol(etiquetas, hijos, altura_maxima=2), 2)
        with self.assertRaisesRegex(ValueError, 'altura'):
            arbol.evaluar(etiquetas, hijos, altura_maxima=1)
        for etiquetas, hijos in [({0: '√'}, {0: (0,)}),
                                  ({0: '+', 1: '1'}, {0: (1,)}),
                                  ({0: 'desconocida'}, {}),
                                  ({0: '+', 1: '2'}, {0: (1, 1)}),
                                  ({0: '+', 1: '1', 2: '2', 3: '3'}, {0: (1, 2, 3)}),
                                  ({0: '1', 1: '2'}, {})]:
            with self.assertRaises(ValueError):
                arbol.validar_arbol(etiquetas, hijos)
        with self.assertRaises(ValueError):
            arbol.evaluar({0: 'x'}, {})
        self.assertEqual(arbol.evaluar({0: 'x'}, {}, x=2)[-1][1], 2)

    def test_generacion_numerica_respeta_catalogo_y_altura(self):
        rng = random.Random(123)
        operaciones = set()
        for _ in range(200):
            etiquetas, hijos = arbol.generar_arbol(rng, 3)
            self.assertLessEqual(arbol.validar_arbol(etiquetas, hijos), 3)
            self.assertNotIn('x', etiquetas.values())
            self.assertTrue(hijos)
            operaciones.update(set(etiquetas.values()) & arbol.OPERACIONES_VALIDAS.keys())
        self.assertEqual(operaciones, set(arbol.OPERACIONES_VALIDAS))

    def test_busqueda_solo_requiere_resultado(self):
        for objetivo in (6, -6, 0, 0.5):
            busqueda = arbol.BusquedaExpresiones(objetivo, max_intentos=10000, semilla=7)
            while not busqueda.terminada:
                busqueda.avanzar()
            self.assertLessEqual(busqueda.mejor.error, 1e-6)
            self.assertTrue(busqueda.mejor.hijos)
            self.assertNotIn('x', busqueda.mejor.etiquetas.values())
            self.assertAlmostEqual(arbol.evaluar(busqueda.mejor.etiquetas,
                                                 busqueda.mejor.hijos)[-1][1], objetivo)

    def test_busqueda_agota_intentos_y_valida_entrada(self):
        busqueda = arbol.BusquedaExpresiones(12345, max_intentos=1)
        busqueda.avanzar()
        self.assertTrue(busqueda.terminada)
        self.assertEqual(busqueda.intentos, 1)
        self.assertGreater(busqueda.mejor.error, 0)
        for objetivo in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                arbol.BusquedaExpresiones(objetivo)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_unica_entrada_busqueda_y_animacion(self):
        from PyQt6.QtWidgets import QAbstractSpinBox, QLineEdit
        v = arbol.VentanaArbol(cargar_automatico=False)
        self.assertEqual(len(v.findChildren(QAbstractSpinBox)), 1)
        self.assertEqual(len(v.findChildren(QLineEdit)), 1)
        v.objetivo.setValue(6)
        v.boton_buscar.click()
        for _ in range(40):
            v.procesar_busqueda()
        self.assertTrue(v.reloj_busqueda.isActive())
        v.boton_buscar.click()
        while v.temporizador.isActive():
            v.avanzar()
        self.assertEqual(v.nodos[0].valor, '6')
        self.assertEqual(len(v.nodos), len(v.etiquetas))
        self.assertIn('Tamaño', v.estadisticas.text())
        self.assertIn('Preorder', v.recorridos.toPlainText())
        self.assertIn('Inorder', v.recorridos.toPlainText())
        self.assertIn('Postorder', v.recorridos.toPlainText())
        self.assertIn('Error', v.mensaje.text())
        v.objetivo.setValue(-6)
        v.boton_buscar.click()
        for _ in range(40):
            v.procesar_busqueda()
        self.assertTrue(v.reloj_busqueda.isActive())
        v.boton_buscar.click()
        while v.temporizador.isActive():
            v.avanzar()
        self.assertEqual(v.nodos[0].valor, '-6')
        v.resize(640, 640)
        v.show()
        self.app.processEvents()
        v.close()

    def test_cancelar_y_cerrar_detienen_busqueda(self):
        v = arbol.VentanaArbol(cargar_automatico=False)
        v.objetivo.setValue(12345)
        v.boton_buscar.click()
        v.boton_buscar.click()
        self.assertFalse(v.reloj_busqueda.isActive())
        v.boton_buscar.click()
        v.close()
        self.assertFalse(v.reloj_busqueda.isActive())
        self.assertFalse(v.temporizador.isActive())


if __name__ == '__main__':
    unittest.main()
