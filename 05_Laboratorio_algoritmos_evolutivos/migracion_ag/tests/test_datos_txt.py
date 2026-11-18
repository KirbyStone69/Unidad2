"""Verifica que los CLI guardan datos reales de la ejecución."""
from pathlib import Path
import subprocess
import os
import io
from unittest.mock import patch
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DatosTXT(unittest.TestCase):
    def test_main_recibe_parametros_desde_la_grafica(self):
        sys.path.insert(0, str(ROOT))
        import maximizacion
        with tempfile.TemporaryDirectory() as carpeta, patch('sys.argv', ['grafica.py']), patch('sys.stdout', io.StringIO()):
            anterior = Path.cwd()
            try:
                os.chdir(carpeta)
                pob, pos, total = maximizacion.main(
                    ['0','32','0.0001','50','3','0.4','0.001','--semilla','7'])
                self.assertEqual(len(pob), 50)
                self.assertGreater(total, 0)
                self.assertIn(str(pob[pos].x), Path('datos_maximizacion.txt').read_text())
            finally:
                os.chdir(anterior)

    def test_cada_programa_guarda_parametros_y_resultado(self):
        casos = [('maximizacion', ['0','32','0.0001','50','3','0.4','0.001']),
                 ('minimizacion', ['-250','250','0.0001','50','3','0.4','0.001']),
                 ('multivariable', ['0,0','100,100','0.0001','50','3','0.4','0.001'])]
        for nombre, args in casos:
            with self.subTest(programa=nombre), tempfile.TemporaryDirectory() as carpeta:
                result = subprocess.run([sys.executable, str(ROOT/f'{nombre}.py'),
                                         *args, '--semilla','7'], cwd=carpeta,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                archivo = Path(carpeta)/f'datos_{nombre}.txt'
                self.assertTrue(archivo.exists(), 'Falta guardar el TXT de ejecución')
                datos = archivo.read_text(encoding='utf-8')
                self.assertIn('Semilla usada: 7', datos)
                self.assertIn('Población: 50', datos)
                self.assertIn('Generaciones: 3', datos)
                self.assertIn('Genes (LSB primero):', datos)
                self.assertIn('Puntos de cruce corregidos:', datos)
                self.assertIn(result.stdout.splitlines()[0], datos)
                self.assertIn(f'datos_{nombre}.txt', result.stdout)


if __name__ == '__main__':
    unittest.main()
