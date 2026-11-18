import importlib
import importlib.util
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


class Reinas(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('reinas'),'Falta el script reinas.py')
        self.m=importlib.import_module('reinas')

    def test_cadena_del_libro_y_filas_desde_arriba(self):
        self.assertEqual(self.m.PADRE_LIBRO,[8,3,7,4,2,5,1,6])
        self.assertEqual(self.m.conflictos(self.m.PADRE_LIBRO),[(3,6)])
        self.assertEqual(self.m.casillas(self.m.PADRE_LIBRO)[0],(0,7))
        self.assertEqual(self.m.casillas(self.m.PADRE_LIBRO)[6],(6,0))

    def test_cruce_ox_conserva_segmentos_y_orden_circular(self):
        p1=self.m.PADRE_LIBRO[:]
        p2=list(range(1,9))
        h1,h2=self.m.cruce_orden(p1,p2,2,5)
        self.assertEqual(h1,[3,5,7,4,2,6,8,1])
        self.assertEqual(h2,[7,2,3,4,5,1,6,8])
        self.assertEqual(p1,self.m.PADRE_LIBRO)
        self.assertEqual(p2,list(range(1,9)))
        h1[0]=99
        self.assertEqual(p1,self.m.PADRE_LIBRO)

    def test_hijos_siempre_son_permutaciones(self):
        rng=random.Random(7)
        for _ in range(100):
            p1=rng.sample(range(1,9),8)
            p2=rng.sample(range(1,9),8)
            a,b=sorted(rng.sample(range(9),2))
            h1,h2=self.m.cruce_orden(p1,p2,a,b)
            for h in (h1,h2):
                self.assertEqual(sorted(h),list(range(1,9)))
            self.assertEqual(h1[a:b],p1[a:b])
            self.assertEqual(h2[a:b],p2[a:b])

    def test_conflictos_y_entradas_invalidas(self):
        self.assertEqual(len(self.m.conflictos(list(range(1,9)))),28)
        with self.assertRaises(ValueError):
            self.m.cruce_orden([1]*8,list(range(1,9)),2,5)
        with self.assertRaises(ValueError):
            self.m.cruce_orden(self.m.PADRE_LIBRO,list(range(1,9)),5,2)

    def test_busqueda_automatica_encuentra_solucion_y_se_detiene(self):
        for semilla in range(20):
            busqueda = self.m.BusquedaReinas(random.Random(semilla))
            mejor = min(len(self.m.conflictos(p)) for p in busqueda.poblacion)
            for _ in range(2000):
                busqueda.paso()
                actual = min(len(self.m.conflictos(p)) for p in busqueda.poblacion)
                self.assertLessEqual(actual, mejor)
                mejor = actual
                for cadena in busqueda.poblacion:
                    self.assertEqual(sorted(cadena), list(range(1, 9)))
                if busqueda.solucion is not None:
                    break
            self.assertIsNotNone(busqueda.solucion, f'Semilla {semilla}')
            self.assertEqual(self.m.conflictos(busqueda.solucion), [])
            self.assertIn(busqueda.solucion, busqueda.escena[:4])
            generacion = busqueda.generacion
            busqueda.paso()
            self.assertEqual(busqueda.generacion, generacion)

    def test_mutacion_intercambia_y_no_modifica_original(self):
        original = self.m.PADRE_LIBRO.copy()
        mutado = self.m.mutar(original, random.Random(4), probabilidad=1)
        self.assertEqual(original, self.m.PADRE_LIBRO)
        self.assertEqual(sorted(mutado), list(range(1, 9)))
        self.assertEqual(sum(a != b for a, b in zip(original, mutado)), 2)
        self.assertEqual(self.m.mutar(original, random.Random(4), probabilidad=0), original)

    def test_continuar_conserva_las_dos_elites_despues_de_ganar(self):
        b = self.m.BusquedaReinas(random.Random(3))
        for _ in range(2000):
            b.paso()
            if b.solucion is not None:
                break
        self.assertIsNotNone(b.solucion)
        elites = sorted(b.poblacion, key=lambda c: len(self.m.conflictos(c)))[:2]
        generacion = b.generacion
        b.paso(continuar=True)
        self.assertEqual(b.generacion, generacion + 1)
        self.assertEqual(b.poblacion[:2], elites)
        self.assertIsNot(b.poblacion[0], elites[0])

    def test_mutacion_guiada_elige_un_intercambio_minimo(self):
        for n in (8, 20, 100):
            cadena = random.Random(n).sample(range(1, n+1), n)
            class Azar:
                def choice(self, opciones):
                    return opciones[0]
            mutado = self.m.intercambio_guiado(cadena, Azar())
            atacadas = sorted({i for par in self.m.conflictos(cadena) for i in par})
            a = atacadas[0]
            costos = []
            for b in range(n):
                if a != b:
                    copia = cadena.copy()
                    copia[a], copia[b] = copia[b], copia[a]
                    costos.append(len(self.m.conflictos(copia)))
            self.assertEqual(self.m.contar_conflictos(mutado), min(costos))
            self.assertEqual(sorted(mutado), list(range(1, n+1)))

    def test_operaciones_para_tamanos_editables(self):
        for n in (1, 4, 8, 20, 100):
            rng = random.Random(n)
            p1 = rng.sample(range(1, n+1), n)
            p2 = rng.sample(range(1, n+1), n)
            h1, h2 = self.m.cruce_orden(p1, p2, 0, max(1, n//2))
            for hijo in (h1, h2, self.m.mutar(h1, rng, probabilidad=1)):
                self.assertEqual(sorted(hijo), list(range(1, n+1)))
                self.assertEqual(self.m.contar_conflictos(hijo), len(self.m.conflictos(hijo)))
            busqueda = self.m.BusquedaReinas(rng, n=n)
            self.assertEqual(len(busqueda.poblacion[0]), n)
        for n in (0, -1, 2, 3):
            with self.assertRaises(ValueError):
                self.m.BusquedaReinas(n=n)

    def test_cien_reinas_encuentra_solucion(self):
        for semilla in range(3):
            b = self.m.BusquedaReinas(random.Random(semilla), n=100)
            for _ in range(500):
                b.paso()
                if b.solucion is not None:
                    break
            self.assertIsNotNone(b.solucion)
            self.assertEqual(sorted(b.solucion), list(range(1, 101)))
            self.assertEqual(self.m.conflictos(b.solucion), [])

    @classmethod
    def qt(cls):
        import os
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PyQt6.QtWidgets import QApplication
        cls._aplicacion = QApplication.instance() or QApplication([])
        return cls._aplicacion

    def test_ventana_un_tablero_editable_y_detencion(self):
        from unittest.mock import patch
        aplicacion = self.qt()
        with patch('pathlib.Path.write_text', side_effect=AssertionError('No guardar resultados')):
            ventana = self.m.VentanaReinas(n=8)
            try:
                ventana.timer.stop()
                for _ in range(500):
                    ventana.avanzar()
                    ventana.timer.stop()
                    if ventana.busqueda.solucion is not None:
                        break
                self.assertFalse(ventana.timer.isActive())
                self.assertEqual(self.m.conflictos(ventana.busqueda.solucion), [])
                self.assertEqual(len(ventana.tablero.cadena), 8)
                self.assertEqual(len(ventana.secuencias), 4)
                ventana.tamano.setValue(100)
                ventana.reiniciar()
                self.assertEqual(ventana.busqueda.n, 100)
                self.assertEqual(len(ventana.tablero.cadena), 100)
                self.assertTrue(ventana.timer.isActive())
                ventana.tamano.setValue(1)
                ventana.reiniciar()
                self.assertFalse(ventana.timer.isActive())
                self.assertEqual(ventana.busqueda.solucion, [1])
            finally:
                ventana.close()
                aplicacion.processEvents()

    def test_tablero_se_ajusta_a_ventanas_altas_y_anchas(self):
        aplicacion = self.qt()
        tablero = self.m.TableroReinas()
        tablero.actualizar(list(range(1, 101)))
        try:
            for ancho, alto in ((720, 240), (240, 720), (600, 600)):
                tablero.resize(ancho, alto)
                tablero.show()
                aplicacion.processEvents()
                rect = tablero.rect_tablero()
                self.assertAlmostEqual(rect.width(), rect.height())
                self.assertGreater(rect.width(), 0)
                self.assertGreaterEqual(rect.left(), 0)
                self.assertGreaterEqual(rect.top(), 0)
                self.assertLessEqual(rect.right(), tablero.width())
                self.assertLessEqual(rect.bottom(), tablero.height())
                captura = tablero.grab().toImage()
                self.assertFalse(captura.isNull())
        finally:
            tablero.close()
        ventana = self.m.VentanaReinas(n=100)
        try:
            ventana.timer.stop()
            ventana.resize(720, 520)
            ventana.show()
            aplicacion.processEvents()
            self.assertTrue(ventana.compacto)
            self.assertFalse(ventana.subtitulo.isVisible())
            self.assertGreaterEqual(ventana.tablero.height(), 130)
            self.assertFalse(ventana.grab().isNull())
        finally:
            ventana.close()

    def test_pausa_y_tamano_invalido_no_pierden_poblacion(self):
        aplicacion = self.qt()
        ventana = self.m.VentanaReinas(n=100)
        try:
            original = ventana.busqueda
            ventana.alternar_pausa()
            self.assertFalse(ventana.timer.isActive())
            ventana.alternar_pausa()
            self.assertTrue(ventana.timer.isActive())
            ventana.tamano.setValue(3)
            ventana.reiniciar()
            self.assertIs(ventana.busqueda, original)
            self.assertTrue(ventana.error.text())
        finally:
            ventana.close()
            aplicacion.processEvents()


if __name__=='__main__':
    unittest.main()
