import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLBACKEND', 'Agg')
import compatibilidad as cpp
import maximizacion
import minimizacion


@contextlib.contextmanager
def ejecucion_temporal():
    anterior = Path.cwd()
    with tempfile.TemporaryDirectory() as carpeta:
        try:
            os.chdir(carpeta)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                yield
        finally:
            os.chdir(anterior)


class EvaluacionesReales(unittest.TestCase):
    def test_observador_captura_cada_adaptacion_sin_cambiar_resultado_ni_azar(self):
        for algoritmo, limites in ((maximizacion, ['0', '32']),
                                   (minimizacion, ['-250', '250'])):
            with self.subTest(algoritmo=algoritmo.__name__), ejecucion_temporal():
                args = limites + ['0.0001', '50', '3', '0.4', '0.01', '--semilla', '7']
                esperadas, recibidas = [], []
                original = algoritmo.adaptacion

                def capturar(individuo, *parametros):
                    valor = original(individuo, *parametros)
                    esperadas.append((individuo.x, valor))
                    return valor

                with patch.object(algoritmo, 'adaptacion', capturar):
                    observado = algoritmo.main(args, observar_evaluacion=lambda x, f: recibidas.append((x, f)))
                azar_observado = [cpp.rand() for _ in range(10)]
                normal = algoritmo.main(args)
                azar_normal = [cpp.rand() for _ in range(10)]
                self.assertTrue(recibidas)
                self.assertEqual(recibidas, esperadas)
                self.assertEqual(observado, normal)
                self.assertEqual(azar_observado, azar_normal)

    def test_observador_se_restaura_tras_error(self):
        recibidas = []

        def fallar(x, f):
            raise RuntimeError('error del observador')

        with cpp.observar_evaluaciones(lambda x, f: recibidas.append((x, f))):
            with self.assertRaisesRegex(RuntimeError, 'error del observador'):
                with cpp.observar_evaluaciones(fallar):
                    cpp.registrar_evaluacion(1.0, 2.0)
            cpp.registrar_evaluacion(3.0, 4.0)
        cpp.registrar_evaluacion(5.0, 6.0)
        self.assertEqual(recibidas, [(3.0, 4.0)])

    def test_main_limpia_observador_cuando_callback_falla(self):
        llamadas = []

        def fallar(x, f):
            llamadas.append((x, f))
            raise RuntimeError('error de evaluación')

        for algoritmo, limites in ((maximizacion, ['0', '32']),
                                   (minimizacion, ['-250', '250'])):
            with self.subTest(algoritmo=algoritmo.__name__), ejecucion_temporal():
                args = limites + ['0.0001', '50', '0', '0.4', '0.001', '--semilla', '7']
                with self.assertRaisesRegex(RuntimeError, 'error de evaluación'):
                    algoritmo.main(args, observar_evaluacion=fallar)
                antes = len(llamadas)
                cpp.registrar_evaluacion(2.0, 3.0)
                algoritmo.main(args)
                self.assertEqual(len(llamadas), antes)


@unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('matplotlib'),
                     'Gráfica opcional: requiere numpy y matplotlib')
class GraficaCalidad(unittest.TestCase):
    def setUp(self):
        import grafica
        import matplotlib.pyplot as plt
        self.grafica = grafica
        self.plt = plt
        self.visual = grafica.GraficaEnVivo(SimpleNamespace(x_min=0, x_max=32, num_gen=1))

    def tearDown(self):
        self.plt.close('all')

    def test_guardar_incluye_datos_pendientes_con_precision_completa(self):
        import numpy as np
        muestras = [(0.12345678901234567, 0.9876543210987654), (2.345678901234567, 8.765432109876543)]
        for x, f in muestras:
            self.visual.registrar_evaluacion(x, f)
        mejor = maximizacion.TIndividuo(genes=[True], x=muestras[1][0], aptitud=muestras[1][1])
        with ejecucion_temporal():
            self.visual.guardar(mejor)
            guardadas = np.loadtxt('datos_grafica.txt', ndmin=2)
            self.assertEqual(set(map(tuple, guardadas)), set(muestras))

    def test_limite_visual_no_descarta_datos_del_archivo(self):
        import numpy as np
        total = self.grafica.LIMITE_PUNTOS + 17
        for i in range(total):
            self.visual.registrar_evaluacion(i / total * 32, float(i))
        mejor = maximizacion.TIndividuo(genes=[True], x=31.0, aptitud=7.0)
        self.visual.actualizar(1, 'Evaluación', [mejor], 0, forzar=True)
        puntos = self.visual.evaluados.get_offsets()
        self.assertLessEqual(len(puntos), self.grafica.LIMITE_PUNTOS)
        self.assertTrue(set(map(tuple, puntos)).issubset(set(self.visual.muestras.items())))
        self.assertGreater(len(self.visual.muestras), self.grafica.LIMITE_PUNTOS)
        with ejecucion_temporal():
            self.visual.guardar(mejor)
            guardadas = np.loadtxt('datos_grafica.txt', ndmin=2)
            self.assertEqual(set(map(tuple, guardadas)), set(self.visual.muestras.items()))

    def test_figura_cerrada_no_refresca_numero_reutilizado(self):
        from matplotlib.backend_bases import CloseEvent
        numero = self.visual.figura.number
        CloseEvent('close_event', self.visual.figura.canvas)._process()
        self.plt.close(self.visual.figura)
        nueva = self.plt.figure(numero)
        self.visual.interactiva = True
        mejor = maximizacion.TIndividuo(genes=[True], x=2, aptitud=3)
        with patch.object(self.visual.figura.canvas, 'flush_events') as flush, \
             patch.object(self.visual.figura.canvas, 'draw_idle') as draw:
            self.visual.actualizar(1, 'Evaluación', [mejor], 0, forzar=True)
        self.assertTrue(self.visual._cerrada)
        self.assertEqual(flush.call_count, 0)
        self.assertEqual(draw.call_count, 0)
        self.assertTrue(self.plt.fignum_exists(nueva.number))

    def test_limites_y_solo_se_expanden_con_valores_negativos(self):
        visual = self.grafica.GraficaEnVivo(SimpleNamespace(x_min=0, x_max=32, num_gen=1), minimizar=True)
        uno = minimizacion.TIndividuo(genes=[True], x=1, aptitud_bruta=-1000)
        dos = minimizacion.TIndividuo(genes=[False], x=2, aptitud_bruta=-970)
        visual.actualizar(0, 'Inicialización', [uno], 0, forzar=True)
        inferior, superior = visual.curva.get_ylim()
        visual.actualizar(1, 'Mutación', [dos], 0, forzar=True)
        nuevo_inferior, nuevo_superior = visual.curva.get_ylim()
        self.assertLessEqual(nuevo_inferior, inferior)
        self.assertGreaterEqual(nuevo_superior, superior)

    def test_agg_no_es_interactivo(self):
        self.assertIsNone(self.visual.figura.canvas.required_interactive_framework)
        self.assertFalse(self.visual.interactiva)

    def test_cero_generaciones_en_ambos_modos(self):
        for bandera, limites, sufijo in (('-maxi', ['0', '32'], ''),
                                         ('-mini', ['-250', '250'], '_minimizacion')):
            with self.subTest(bandera=bandera), ejecucion_temporal(), patch.object(self.plt, 'show'):
                visual = self.grafica.main([bandera] + limites + ['0.0001', '50', '0', '0.4', '0.001', '--semilla', '7'])
                self.assertEqual(len(visual.historial), 1)
                self.assertEqual(visual.historial[0][1:3], (0, 'Inicialización'))
                self.assertEqual(len(visual.figura.axes), 1)
                self.assertTrue(Path('datos_grafica' + sufijo + '.txt').exists())
                self.assertTrue(visual.muestras)


    def test_refresco_se_mide_desde_fin_y_no_encadena_dibujos_lentos(self):
        visual = self.visual
        visual.interactiva = True
        visual.inicio = 0.0
        individuo = maximizacion.TIndividuo(genes=[True], x=2, aptitud=3)
        with patch.object(visual, '_dibujar') as dibujar, patch.object(visual.figura.canvas, 'flush_events'), \
             patch('grafica.time.perf_counter', side_effect=[1.0, 1.0, 1.2, 1.21, 2.01, 2.01, 2.21]):
            visual.actualizar(0, 'Inicialización', [individuo], 0)
            self.assertAlmostEqual(visual.ultimo_refresco, 1.2)
            self.assertGreaterEqual(visual._intervalo, 0.79)
            visual.actualizar(1, 'Mutación', [individuo], 0)
            self.assertEqual(dibujar.call_count, 1)
            visual.actualizar(1, 'Evaluación', [individuo], 0)
            self.assertEqual(dibujar.call_count, 2)
        self.assertEqual(len(visual.historial), 3)

    def test_reuso_de_numero_sin_evento_cierre_no_toca_canvas_viejo(self):
        visual = self.visual
        numero = visual.figura.number
        self.plt.close(visual.figura)
        nueva = self.plt.figure(numero)
        visual.interactiva = True
        individuo = maximizacion.TIndividuo(genes=[True], x=2, aptitud=3)
        with patch.object(visual.figura.canvas, 'flush_events') as flush, patch.object(visual, '_dibujar') as dibujar:
            visual.actualizar(1, 'Evaluación', [individuo], 0, forzar=True)
        self.assertTrue(visual._cerrada)
        self.assertEqual(flush.call_count, 0)
        self.assertEqual(dibujar.call_count, 0)
        self.assertIs(self.plt.figure(numero), nueva)
        self.assertIn((2, 3), visual.muestras.items())
        self.assertEqual(len(visual.historial), 1)

    def test_banderas_incompatibles_fallan_antes_de_crear_figura(self):
        with patch.object(self.grafica, 'GraficaEnVivo') as crear:
            with self.assertRaisesRegex(SystemExit, 'Elige solo una bandera'):
                self.grafica.main(['-mini', '-maxi'])
        crear.assert_not_called()

    def test_main_captura_todas_las_evaluaciones(self):
        args = ['0', '32', '0.0001', '50', '3', '0.4', '0.01', '--semilla', '7']
        esperadas = {}
        original = maximizacion.adaptacion

        def capturar(individuo, *parametros):
            valor = original(individuo, *parametros)
            esperadas[individuo.x] = valor
            return valor

        with ejecucion_temporal(), patch.object(self.plt, 'show'), patch.object(maximizacion, 'adaptacion', capturar):
            visual = self.grafica.main(args)
        self.assertEqual(visual.muestras, esperadas)


@unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('matplotlib'),
                     'GUI opcional: requiere numpy y matplotlib')
class GraficaGUI(unittest.TestCase):
    def test_pixeles_marcador_se_mueven_y_se_conservan_tras_zoom_y_final(self):
        import importlib.util
        import subprocess
        import textwrap
        if not any(importlib.util.find_spec(m) for m in ('PyQt6', 'PySide6', 'PyQt5', 'PySide2')):
            self.skipTest('Qt no está instalado')
        programa = textwrap.dedent("""
            from types import SimpleNamespace
            import numpy as np
            import matplotlib.pyplot as plt
            import grafica, maximizacion
            visual=grafica.GraficaEnVivo(SimpleNamespace(x_min=0,x_max=32,num_gen=2))
            ind=maximizacion.TIndividuo(genes=[True],x=2,aptitud=3)
            def rojo_en(x,y):
                rgba=np.asarray(visual.figura.canvas.buffer_rgba())
                px,py=map(round,visual.curva.transData.transform((x,y)))
                fila=rgba.shape[0]-1-py
                ventana=rgba[max(0,fila-2):fila+3,max(0,px-2):px+3,:3]
                return np.any((ventana[:,:,0]>200)&(ventana[:,:,1]<80)&(ventana[:,:,2]<80))
            visual.actualizar(0,'Inicialización',[ind],0,forzar=True)
            assert rojo_en(2,3)
            visual.curva.set_xlim(0,4)
            visual.curva.set_ylim(0,6)
            visual.figura.set_size_inches(7,4)
            visual.figura.canvas.draw()
            ind.x,ind.aptitud=3,4
            visual.actualizar(1,'Mutación',[ind],0,forzar=True)
            assert rojo_en(3,4), 'no se ve marcador nuevo tras zoom/resize'
            assert not rojo_en(2,3), 'quedó una estela roja del marcador anterior'
            visual.finalizar()
            visual.figura.canvas.draw()
            assert rojo_en(3,4), 'se pierde marcador en render final normal'
            plt.close('all')
        """)
        resultado=subprocess.run([sys.executable,'-c',programa],cwd=ROOT,
                                 env=dict(os.environ,MPLBACKEND='QtAgg',QT_QPA_PLATFORM='offscreen'),
                                 capture_output=True,text=True,timeout=30)
        self.assertEqual(resultado.returncode,0,resultado.stdout+resultado.stderr)

    def test_qt_actualiza_blit_redimensiona_y_cierra_sin_esperas(self):
        import importlib.util
        import subprocess
        import textwrap
        if not any(importlib.util.find_spec(m) for m in ('PyQt6', 'PySide6', 'PyQt5', 'PySide2')):
            self.skipTest('Qt no está instalado')
        programa = textwrap.dedent('''
            from types import SimpleNamespace
            from unittest.mock import patch
            import grafica
            import maximizacion
            import matplotlib.pyplot as plt
            from matplotlib.backend_bases import ResizeEvent
            visual = grafica.GraficaEnVivo(SimpleNamespace(x_min=0, x_max=32, num_gen=2))
            assert visual.interactiva
            assert visual._usar_blit
            individuo = maximizacion.TIndividuo(genes=[True], x=2, aptitud=3)
            with patch.object(plt, 'pause', side_effect=AssertionError('pause prohibido')), patch('time.sleep', side_effect=AssertionError('sleep prohibido')), patch.object(visual.figura.canvas, 'blit', wraps=visual.figura.canvas.blit) as blit:
                visual.actualizar(0, 'Inicialización', [individuo], 0, forzar=True)
                individuo.x, individuo.aptitud = 3, 4
                visual.actualizar(1, 'Mutación', [individuo], 0, forzar=True)
                visual.figura.set_size_inches(7, 4)
                ResizeEvent('resize_event', visual.figura.canvas)._process()
                visual.actualizar(2, 'Evaluación', [individuo], 0, forzar=True)
                assert blit.call_count > 0
                assert tuple(visual.marcador.get_offsets()[0]) == (3, 4)
                assert len(visual.figura.axes) == 1
                visual.figura.canvas.flush_events()
                plt.close(visual.figura)
                assert visual._cerrada
                visual.actualizar(2, 'Finalizado', [individuo], 0, forzar=True)
            plt.close('all')
        ''')
        entorno = dict(os.environ, MPLBACKEND='QtAgg', QT_QPA_PLATFORM='offscreen')
        resultado = subprocess.run([sys.executable, '-c', programa], cwd=ROOT,
                                   env=entorno, capture_output=True, text=True, timeout=30)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == '__main__':
    unittest.main()
