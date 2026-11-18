"""Compara con C++ derivado de la transcripción, fase por fase.

No compara con C++ indefinido: usa exactamente R1-R8 y E1 descritos en el
reporte. Se requieren g++; los programas Python no dependen de él.
"""
import importlib
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@unittest.skipUnless(shutil.which('g++'), 'g++ no disponible para comparación diferencial')
class EquivalenciaCPP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('preparar_referencia',
                        ROOT/'referencia/preparar_referencia.py')
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        cls.tmp = tempfile.TemporaryDirectory(prefix='ag_cpp_')
        cls.path = Path(cls.tmp.name)
        prepare.construir(cls.path)
        for mode in ('maximizacion','minimizacion','multivariable'):
            result = subprocess.run(['g++','-std=c++17','-O0','-ffp-contract=off',
                                     str(cls.path/f'{mode}.cpp'),'-o',str(cls.path/mode)],
                                     capture_output=True,text=True,timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def comparar(self, mode, seed):
        m = importlib.import_module(mode)
        m.configurar_azar(seed, 32767)
        multi = mode == 'multivariable'
        mini = mode != 'maximizacion'
        if multi:
            m.NUM_VAR = 3
            lcrom, x_min, x_max = [5,4,6],[0.0]*3,[100.0,80.0,60.0]
        else:
            lcrom, x_min, x_max = 5,0.0,32.0
        rng = random.Random(seed)
        values = [rng.randint(0,32767) for _ in range(10000)]
        result = subprocess.run([str(self.path/mode)],input='\n'.join(map(str,values)),
                                capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        lines = iter(result.stdout.splitlines())
        with patch.object(m,'rand',side_effect=values) as rand:
            pob = m.poblacion_inicial(50,lcrom,x_min,x_max)
            cmax = m.revisar_adap_mini(pob,50,lcrom,0,x_min,x_max) if mini else 0
            pos,total = m.evaluacion(pob,50)

            def comprobar(stage):
                head = next(lines).split()
                self.assertEqual(head[0],stage)
                self.assertEqual(int(head[1]),pos, (mode,seed,stage,'mejor'))
                self.assertAlmostEqual(float(head[2]),total,delta=1e-11)
                self.assertAlmostEqual(float(head[3]),cmax,delta=1e-11)
                self.assertEqual(int(head[4]),rand.call_count, (mode,seed,stage,'azar'))
                for index,ind in enumerate(pob):
                    raw = ind.aptitud_bruta if mini else ind.aptitud
                    xs = ind.vec_x if multi else [ind.x]
                    genes = ([g for chromosome in ind.vec_genes for g in chromosome]
                             if multi else ind.genes)
                    expected = ([int(ind.elite),ind.aptitud,raw,ind.puntuacion,ind.punt_acu]
                                + xs + [int(g) for g in genes])
                    actual = list(map(float,next(lines).split()))
                    self.assertEqual(len(actual),len(expected))
                    for field,(cpp,py) in enumerate(zip(actual,expected)):
                        if field == 0 or field >= 5+len(xs):
                            self.assertEqual(cpp,py,(mode,seed,stage,index,field))
                        else:
                            self.assertAlmostEqual(cpp,py,delta=1e-11,
                                                   msg=str((mode,seed,stage,index,field)))

            comprobar('inicial')
            for generacion in range(3):
                m.seleccion(pob,50)
                comprobar('seleccion')
                m.reproduccion(pob,50,lcrom,0.8,x_min,x_max)
                comprobar('reproduccion')
                m.mutacion(pob,50,lcrom,0.15,x_min,x_max)
                comprobar('mutacion')
                if mini:
                    cmax = m.revisar_adap_mini(pob,50,lcrom,cmax,x_min,x_max)
                pos,total = m.evaluacion(pob,50,pos,total)
                comprobar('evaluacion')
            self.assertEqual(list(lines),[])

    def test_maximizacion_fase_a_fase(self):
        for seed in (0,7,42):
            with self.subTest(seed=seed):
                self.comparar('maximizacion',seed)

    def test_minimizacion_fase_a_fase(self):
        for seed in (0,7,42):
            with self.subTest(seed=seed):
                self.comparar('minimizacion',seed)

    def test_multivariable_fase_a_fase(self):
        for seed in (0,7,42):
            with self.subTest(seed=seed):
                self.comparar('multivariable',seed)


if __name__ == '__main__':
    unittest.main()
