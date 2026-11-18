import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import maximizacion


class Observacion(unittest.TestCase):
    def test_observa_fases_reales_y_no_altera_la_poblacion(self):
        eventos=[]
        args=['0','32','0.0001','50','3','0.4','0.001','--semilla','7']
        def observar(gen,fase,pob,pos):
            eventos.append((gen,fase,len(pob)))
        with tempfile.TemporaryDirectory() as carpeta, patch('sys.stdout',io.StringIO()), patch('sys.stderr',io.StringIO()):
            anterior=Path.cwd()
            try:
                os.chdir(carpeta)
                con=maximizacion.main(args,observar=observar)
                sin=maximizacion.main(args)
            finally:
                os.chdir(anterior)
        self.assertEqual(con,sin)
        self.assertEqual(eventos[0],(0,'Inicialización',50))
        self.assertEqual(len(eventos),13)
        self.assertEqual([e[1] for e in eventos[1:5]],['Selección','Cruce','Mutación','Evaluación'])
        self.assertEqual(eventos[-1],(3,'Evaluación',50))

    def test_minimizacion_observador_no_cambia_resultado(self):
        import minimizacion
        eventos=[]
        args=['-250','250','0.001','50','3','0.4','0.001','--semilla','7']
        with tempfile.TemporaryDirectory() as carpeta, patch('sys.stdout',io.StringIO()), patch('sys.stderr',io.StringIO()):
            anterior=Path.cwd()
            try:
                os.chdir(carpeta)
                con=minimizacion.main(args,observar=lambda *e: eventos.append(e[:2]))
                sin=minimizacion.main(args)
            finally:
                os.chdir(anterior)
        self.assertEqual(con,sin)
        self.assertEqual(len(eventos),13)
        self.assertEqual(eventos[-1],(3,'Evaluación'))


@unittest.skipUnless(importlib.util.find_spec('matplotlib') and importlib.util.find_spec('numpy'),
                     'Gráfica opcional: requiere numpy y matplotlib')
class GraficaViva(unittest.TestCase):
    def test_grafica_actualiza_poblacion_tiempo_y_guarda_historial(self):
        os.environ['MPLBACKEND']='Agg'
        import grafica
        import numpy as np
        import matplotlib.pyplot as plt
        with tempfile.TemporaryDirectory() as carpeta:
            anterior=Path.cwd()
            try:
                os.chdir(carpeta)
                args=['0','32','0.0001','50','3','0.4','0.001','--semilla','7']
                with patch.object(plt,'show'), patch('sys.stdout',io.StringIO()), patch('sys.stderr',io.StringIO()):
                    visual=grafica.main(['-maxi',*args])
                self.assertEqual(len(visual.figura.axes),1)
                self.assertEqual(len(visual.historial),13)
                self.assertEqual(visual.historial[-1][1:3],(3,'Evaluación'))
                self.assertEqual(visual.puntos.get_offsets().shape,(50,2))
                self.assertEqual(visual.marcador.get_offsets().shape,(1,2))
                tiempos=[fila[0] for fila in visual.historial]
                self.assertEqual(tiempos,sorted(tiempos))
                texto=Path('datos_evolucion.txt').read_text()
                self.assertIn('tiempo_s',texto)
                self.assertIn('Mutación',texto)
                self.assertEqual(len(texto.splitlines()),14)
                self.assertGreater(len(visual.muestras),0)
                self.assertEqual(np.loadtxt('datos_grafica.txt').shape,(len(visual.muestras),2))
                vistos=set()
                def capturar(x,f):
                    vistos.add((x,f))
                with patch('sys.stdout',io.StringIO()), patch('sys.stderr',io.StringIO()):
                    maximizacion.main(args,observar_evaluacion=capturar)
                self.assertEqual(set(visual.muestras.items()),vistos)
                plt.close('all')
            finally:
                os.chdir(anterior)

    def test_grafica_minima_usa_aptitud_bruta_y_archivos_separados(self):
        os.environ['MPLBACKEND']='Agg'
        import grafica
        import numpy as np
        import matplotlib.pyplot as plt
        with tempfile.TemporaryDirectory() as carpeta:
            anterior=Path.cwd()
            try:
                os.chdir(carpeta)
                with patch.object(plt,'show'), patch('sys.stdout',io.StringIO()), patch('sys.stderr',io.StringIO()):
                    visual=grafica.main(['-mini','-250','250','0.001','50','3','0.4','0.001','--semilla','7'])
                self.assertEqual(len(visual.figura.axes),1)
                self.assertEqual(len(visual.historial),13)
                self.assertTrue(np.all(visual.y<=0))
                self.assertAlmostEqual(visual.historial[-1][4],
                                       float(visual.marcador.get_offsets()[0,1]))
                self.assertLess(visual.historial[-1][4],0)
                self.assertTrue(Path('datos_minimizacion.txt').exists())
                self.assertTrue(Path('datos_grafica_minimizacion.txt').exists())
                self.assertTrue(Path('datos_evolucion_minimizacion.txt').exists())
                self.assertFalse(Path('datos_grafica.txt').exists())
                plt.close('all')
            finally:
                os.chdir(anterior)

    def test_empieza_vacia_y_acumula_solo_datos_recibidos(self):
        os.environ['MPLBACKEND']='Agg'
        import grafica
        import matplotlib.pyplot as plt
        from types import SimpleNamespace
        visual=grafica.GraficaEnVivo(SimpleNamespace(x_min=0,x_max=32,num_gen=1))
        self.assertEqual(len(visual.muestras),0)
        self.assertEqual(len(visual.evaluados.get_offsets()),0)
        self.assertEqual(len(visual.curva.lines),0)
        uno=maximizacion.TIndividuo(genes=[True],x=2,aptitud=999)
        dos=maximizacion.TIndividuo(genes=[False],x=3,aptitud=888)
        visual.actualizar(0,'Inicialización',[uno],0,forzar=True)
        visual.actualizar(1,'Mutación',[dos],0,forzar=True)
        self.assertEqual(visual.muestras,{2:999,3:888})
        self.assertEqual(set(map(tuple,visual.evaluados.get_offsets())),{(2,999),(3,888)})
        plt.close('all')

    def test_no_actualiza_artistas_entre_refrescos(self):
        os.environ['MPLBACKEND']='Agg'
        import grafica
        import matplotlib.pyplot as plt
        from types import SimpleNamespace
        visual=grafica.GraficaEnVivo(SimpleNamespace(x_min=0,x_max=32,num_gen=1))
        visual.interactiva=True
        visual.inicio=0
        visual.ultimo_refresco=1.0
        pob=[maximizacion.TIndividuo(genes=[True],x=32,aptitud=20)]
        with patch('grafica.time.perf_counter',return_value=1.01), \
             patch.object(visual.puntos,'set_offsets',wraps=visual.puntos.set_offsets) as offsets:
            visual.actualizar(1,'Mutación',pob,0)
        self.assertEqual(len(visual.historial),1)
        self.assertEqual(offsets.call_count,0)
        plt.close('all')


if __name__=='__main__':
    unittest.main()
