"""Contratos derivados del impreso, antes de implementar los módulos.
Cambiar orden de bits, copias, umbrales, elitismo o posición de reevaluación
haría fallar estas pruebas; no se exige convergencia de un proceso estocástico.
"""
import importlib
import importlib.util
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def f32(x):
    return struct.unpack('f', struct.pack('f', x))[0]


class OperacionesEscalares(unittest.TestCase):
    nombre = 'maximizacion'

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(self.nombre),
                             f'Falta implementar {self.nombre}')
        self.m = importlib.import_module(self.nombre)
        self.m.configurar_azar(7, 32767)

    def individuo(self, genes, elite=False):
        ind = self.m.TIndividuo(genes=list(genes), elite=elite)
        f = self.m.adaptacion(ind, len(genes), 0.0, 32.0)
        if self.nombre == 'maximizacion':
            ind.aptitud = f
        else:
            ind.aptitud_bruta = f
        return ind

    def test_binario_lsb_y_decodificacion(self):
        self.assertEqual(self.m.bin_dec([True, False, True, False], 4), 5)
        self.assertEqual(self.m.decod([False]*4, 4, -250, 250), -250)
        self.assertEqual(self.m.decod([True]*4, 4, -250, 250), 250)
        self.assertEqual(self.m.decod([True, False, True, False], 4, 0, 30), 10)

    def test_conversion_float_del_numerador(self):
        genes = [True] + [False]*23 + [True]
        expected = f32(2**24 + 1) / (2**25-1)
        self.assertEqual(self.m.decod(genes, 25, 0, 1), expected)

    def test_generacion_umbral_entero_y_aptitud(self):
        with patch.object(self.m, 'rand', side_effect=[0, 16382, 16383, 32767]):
            ind = self.m.genera_indiv(4, 0, 32)
        self.assertEqual(ind.genes, [False, False, True, True])
        self.assertEqual(ind.x, 32*12/15)
        f = self.m.adaptacion(ind, 4, 0, 32)
        self.assertEqual(ind.aptitud if self.nombre == 'maximizacion'
                         else ind.aptitud_bruta, f)
        self.assertFalse(ind.elite)

    def test_objetivo_del_libro(self):
        ind = self.individuo([True]*4)
        x = ind.x
        expected = (20+math.exp(1)-20*math.exp(-0.2*abs(x))
                    -math.exp(math.cos(2*math.pi*x)))
        if self.nombre != 'maximizacion':
            expected = -abs(x*math.sin(math.sqrt(abs(x))))
        self.assertEqual(self.m.adaptacion(ind, 4, 0, 32), expected)

    def test_cruce_un_punto_y_copias(self):
        p1 = self.individuo([False]*4)
        p2 = self.individuo([True]*4)
        h1, h2 = self.m.TIndividuo(), self.m.TIndividuo()
        self.m.cruce(p1, p2, h1, h2, 4, 2, 0, 32)
        self.assertEqual(h1.genes, [False, False, True, True])
        self.assertEqual(h2.genes, [True, True, False, False])
        h1.genes[0] = True
        self.assertEqual(p1.genes, [False]*4)
        self.assertFalse(h1.elite)

    def test_mutacion_probabilidad_y_elite(self):
        pob = [self.individuo([False]*4), self.individuo([False]*4, True)]
        with patch.object(self.m, 'rand', return_value=0) as rng:
            self.m.mutacion(pob, 2, 4, 1, 0, 32)
        self.assertEqual(rng.call_count, 8)
        self.assertEqual(pob[0].genes, [True]*4)
        self.assertEqual(pob[1].genes, [False]*4)
        self.assertEqual(pob[0].x, 32)

    def test_reevaluacion_dentro_del_bucle(self):
        pob = [self.individuo([False]*4)]
        original = self.m.adaptacion
        with patch.object(self.m, 'rand', side_effect=[0,32767,32767,32767]), \
             patch.object(self.m, 'adaptacion', wraps=original) as adap:
            self.m.mutacion(pob, 1, 4, 0.1, 0, 32)
        self.assertEqual(adap.call_count, 4)
        self.assertEqual(pob[0].genes, [True,False,False,False])

    def test_evaluacion_float32(self):
        pob = [self.individuo([False]*4) for _ in range(3)]
        for ind, apt in zip(pob, [1.0, 2.0, 3.0]):
            ind.aptitud = apt
        pos, total = self.m.evaluacion(pob, 3)
        self.assertEqual((pos,total), (2,6.0))
        self.assertEqual(pob[1].punt_acu, 2/6 + f32(1/6))
        self.assertEqual(pob[2].punt_acu, 3/6 + f32(f32(1/6)+2/6))

    def test_ruleta_limite_inclusivo_y_copia_por_valor(self):
        pob = [self.individuo([True,False]), self.individuo([False,True])]
        pob[0].punt_acu, pob[1].punt_acu = 0.5, 1.0
        with patch.object(self.m, 'rand', side_effect=[16384, 16384]):
            self.m.seleccion(pob, 2)
        self.assertEqual([i.genes for i in pob], [[True,False]]*2)
        pob[0].genes[0] = False
        self.assertEqual(pob[1].genes, [True,False])

    def test_ruleta_cota_y_redondeo_de_f(self):
        # Último acumulado menor que prob: C++ accede fuera del vector;
        # Python utiliza el fallback pos_super-1 ya presente en el impreso.
        pob = [self.individuo([True]), self.individuo([False])]
        pob[0].punt_acu = pob[1].punt_acu = 0.0
        with patch.object(self.m, 'rand', return_value=32767):
            self.m.seleccion(pob, 2)
        self.assertEqual([i.genes for i in pob], [[False],[False]])

    def test_elite_original_no_se_ordena(self):
        pob = [self.individuo([False]) for _ in range(100)]
        for ind in pob:
            ind.aptitud, ind.punt_acu = 1.0, 1.0
        pob[1].aptitud, pob[2].aptitud, pob[3].aptitud = 100.0, 50.0, 150.0
        with patch.object(self.m, 'rand', return_value=0):
            self.m.seleccion(pob, 100)
        self.assertFalse(pob[1].elite)
        self.assertTrue(pob[2].elite)
        self.assertTrue(pob[3].elite)
        # El libro sobrescribe el slot 0 sin desplazar 100 al slot 1:
        # conserva 150 y 50, aun cuando 100 es el segundo mejor.
        self.assertEqual(sum(i.elite for i in pob), 2)

    def test_comparacion_reproduccion_con_elite_literal(self):
        pob = [self.individuo([True]*4, True), self.individuo([False]*4)]
        with patch.object(self.m, 'rand', side_effect=[0,0,0]):
            self.m.reproduccion(pob,2,4,1,0,32)
        if self.nombre == 'maximizacion':
            # El impreso usa < incluso para maximizar: deja empeorar al élite.
            self.assertEqual(pob[0].genes,[True,False,False,False])
            self.assertFalse(pob[0].elite)
        else:
            # R6 compara brutas; aquí el hijo es peor y el élite se conserva.
            self.assertEqual(pob[0].genes,[True]*4)
            self.assertTrue(pob[0].elite)

    def test_reproduccion_descarta_ultimo_impar(self):
        pob = [self.individuo([False,False]), self.individuo([True,True]),
               self.individuo([True,False])]
        ultimo = pob[2].genes[:]
        with patch.object(self.m, 'rand', side_effect=[0,0,0,0]):
            self.m.reproduccion(pob, 3, 2, 1, 0, 32)
        self.assertEqual(pob[0].genes, [False,True])
        self.assertEqual(pob[1].genes, [True,False])
        self.assertEqual(pob[2].genes, ultimo)

    def test_punto_fuera_de_rango_documentado(self):
        pob = [self.individuo([False]*4), self.individuo([True]*4)]
        with patch.object(self.m, 'rand', side_effect=[0,0,32767]):
            self.m.reproduccion(pob, 2, 4, 1, 0, 32)
        self.assertEqual([i.genes for i in pob], [[False]*4,[True]*4])
        import compatibilidad
        compatibilidad.CRUCE_ESTRICTO = True
        try:
            with patch.object(self.m, 'rand', side_effect=[0,0,32767]):
                with self.assertRaises(ValueError):
                    self.m.reproduccion(pob, 2, 4, 1, 0, 32)
        finally:
            compatibilidad.CRUCE_ESTRICTO = False

    def test_fitness_cero_no_se_inventa_ruleta(self):
        pob = [self.individuo([False]*4)]
        pob[0].aptitud = 0
        with self.assertRaises(ValueError):
            self.m.evaluacion(pob, 1)


class Minimizacion(OperacionesEscalares):
    nombre = 'minimizacion'

    def test_transformacion_exacta_con_signo_original(self):
        pob = [self.individuo([False]*4) for _ in range(3)]
        for ind, raw in zip(pob, [-5.0, -2.0, -8.0]):
            ind.aptitud_bruta, ind.aptitud = raw, 1000.0
        cmax = self.m.revisar_adap_mini(pob, 3, 4, 0, 0, 32)
        self.assertEqual(cmax, -2.02)
        for ind, expected in zip(pob, [2.98,-0.02,5.98]):
            self.assertAlmostEqual(ind.aptitud, expected, places=14)


class Multivariable(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('multivariable'),
                             'Falta implementar multivariable')
        self.m = importlib.import_module('multivariable')
        self.m.configurar_azar(7, 32767)
        self.m.NUM_VAR = 2

    def test_generacion_vectores_independientes(self):
        with patch.object(self.m, 'rand', side_effect=[0,32767,32767,0,0]):
            ind = self.m.genera_indiv([2,3], [0,0], [100,100])
        self.assertEqual(ind.vec_genes, [[False,True],[True,False,False]])
        self.assertEqual(ind.vec_x, [f32(200/3), f32(100/7)])
        f=0.0
        for x in ind.vec_x:
            raiz=f32(math.sqrt(f32(abs(x))))
            seno=f32(math.sin(raiz))
            f=f32(f-f32(x*seno))
        self.assertEqual(ind.aptitud_bruta, f)

    def test_cruce_punto_por_variable(self):
        p1 = self.m.TIndividuo(vec_genes=[[False]*2,[False]*3])
        p2 = self.m.TIndividuo(vec_genes=[[True]*2,[True]*3])
        h1,h2=self.m.TIndividuo(),self.m.TIndividuo()
        self.m.cruce(p1,p2,h1,h2,[2,3],[1,2],[0,0],[100,100])
        self.assertEqual(h1.vec_genes, [[False,True],[False,False,True]])
        self.assertEqual(h2.vec_genes, [[True,False],[True,True,False]])
        h1.vec_genes[0][0]=True
        self.assertFalse(p1.vec_genes[0][0])

    def test_mutacion_reevalua_una_vez_y_respeta_elite(self):
        pob = [self.m.TIndividuo(vec_genes=[[False]*2,[False]*3]),
               self.m.TIndividuo(vec_genes=[[False]*2,[False]*3],elite=True)]
        original=self.m.adaptacion
        with patch.object(self.m,'rand',return_value=0) as rng, \
             patch.object(self.m,'adaptacion',wraps=original) as adap:
            self.m.mutacion(pob,2,[2,3],1,[0,0],[100,100])
        self.assertEqual(rng.call_count,10)
        self.assertEqual(adap.call_count,1)
        self.assertEqual(pob[0].vec_genes, [[True]*2,[True]*3])
        self.assertEqual(pob[1].vec_genes, [[False]*2,[False]*3])

    def test_objetivo_multivariable_sin_abs_exterior(self):
        ind=self.m.TIndividuo(vec_genes=[[True]*3,[True]*3])
        result=self.m.adaptacion(ind,[3,3],[0,0],[100,100])
        producto=f32(100*f32(math.sin(f32(math.sqrt(100)))))
        expected=f32(f32(-producto)-producto)
        self.assertEqual(result,expected)
        self.assertGreater(result,0)


class CompatibilidadNumerica(unittest.TestCase):
    def test_seno_float_usa_sinf_no_sin_double_redondeado(self):
        import compatibilidad
        self.assertTrue(hasattr(compatibilidad, 'seno32'), 'Falta puente sinf')
        # Entrada que distingue sinf de convertir el resultado double.
        self.assertEqual(compatibilidad.seno32(8.980265617370605),
                         0.4300176501274109)



class Programas(unittest.TestCase):
    def test_limites_extremos_se_rechazan_sin_traceback(self):
        commands = [('maximizacion.py',['--','-1e308','1e308','1','2','0','0','0']),
                    ('multivariable.py',['0','1e100','1','2','0','0','0'])]
        for file,args in commands:
            with self.subTest(file=file), tempfile.TemporaryDirectory() as carpeta:
                result=subprocess.run([sys.executable,str(ROOT/file),*args],
                                      capture_output=True,text=True,timeout=30,cwd=carpeta)
                self.assertNotEqual(result.returncode,0)
                self.assertNotIn('Traceback',result.stderr)
                self.assertIn('rango',result.stderr)

    def test_cli_tres_programas(self):
        commands = [('maximizacion.py',['0','32','0.0001','50','3','0.4','0.001']),
                    ('minimizacion.py',['-250','250','0.001','50','3','0.4','0.001']),
                    ('multivariable.py',['0,0','100,100','0.001','50','3','0.4','0.001'])]
        for file,args in commands:
            with self.subTest(file=file), tempfile.TemporaryDirectory() as carpeta:
                self.assertTrue((ROOT/file).exists(),f'Falta implementar {file}')
                result=subprocess.run([sys.executable,str(ROOT/file),*args,'--semilla','7'],
                                      capture_output=True,text=True,timeout=30,cwd=carpeta)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn('Aptitud del mejor(',result.stdout)


if __name__ == '__main__':
    unittest.main()
