"""Visualización de eventos reales, sin modificar las operaciones genéticas."""
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import compatibilidad as cpp


class Terminal(io.StringIO):
    def isatty(self):
        return True


class PanelTerminal(unittest.TestCase):
    def test_semilla_automatica_no_depende_del_segundo_actual(self):
        with patch('secrets.randbits', side_effect=[111, 222]):
            cpp.configurar_azar()
            self.assertEqual(cpp.SEMILLA_USADA, 111)
            cpp.configurar_azar()
            self.assertEqual(cpp.SEMILLA_USADA, 222)
        cpp.configurar_azar(7)
        self.assertEqual(cpp.SEMILLA_USADA, 7)

    def test_tres_programas_muestran_cruce_mutacion_y_panel_fijo(self):
        for nombre, limites in [('maximizacion',['0','32']),
                                ('minimizacion',['-250','250']),
                                ('multivariable',['0,0','100,100'])]:
            with self.subTest(programa=nombre), tempfile.TemporaryDirectory() as carpeta:
                m = importlib.import_module(nombre)
                terminal = Terminal()
                argv = [nombre,*limites,'0.1','50','3','1','1','--semilla','7']
                anterior = Path.cwd()
                try:
                    os.chdir(carpeta)
                    with patch('sys.argv', argv), patch('sys.stdout', terminal), patch('sys.stderr', io.StringIO()):
                        pob, pos, suma = m.main()
                    texto = terminal.getvalue()
                    self.assertIn('Semilla: 7', texto)
                    self.assertIn('Generación: 3/3', texto)
                    self.assertIn('Padre 1:', texto)
                    self.assertIn('Padre 2:', texto)
                    self.assertIn('Hijo 1:', texto)
                    self.assertIn('Hijo 2:', texto)
                    self.assertIn('|', texto)
                    self.assertIn('Mutación observada', texto)
                    self.assertIn('Antes:', texto)
                    self.assertIn('Después:', texto)
                    self.assertIn('\033[2K', texto)
                    self.assertIn('Datos guardados', texto)
                    # El panel no debe cambiar el resultado ni consumir azar.
                    with patch('sys.argv', argv), patch('sys.stdout', io.StringIO()), patch('sys.stderr', io.StringIO()):
                        sin_panel, otro_pos, otra_suma = m.main()
                    self.assertEqual(pos, otro_pos)
                    self.assertEqual(suma, otra_suma)
                    self.assertEqual(pob, sin_panel)
                finally:
                    os.chdir(anterior)


if __name__ == '__main__':
    unittest.main()
