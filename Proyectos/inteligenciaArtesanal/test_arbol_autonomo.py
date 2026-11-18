"""Verificar que arbol.py funciona solo, incluso desde otra carpeta."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class AutonomoTests(unittest.TestCase):
    def test_script_y_csv_sin_modulos_auxiliares(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d)
            shutil.copy(Path(__file__).with_name('arbol.py'), destino/'arbol.py')
            (destino/'gr.csv').write_text('x,y\n-2,4\n-1,1\n0,0\n1,1\n2,4\n')
            programa = '''
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('arbol_aislado', sys.argv[1])
modulo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = modulo
spec.loader.exec_module(modulo)
from PyQt6.QtWidgets import QApplication
app = QApplication([])
v = modulo.VentanaArbol()
assert v.datos is not None, 'No cargó gr.csv automáticamente'
assert len(v.datos.x) == 5
assert v.reloj_busqueda.isActive(), 'No comenzó la búsqueda automáticamente'
for _ in range(10):
    v.procesar_busqueda()
assert v.busqueda.mejor.mse == 0
v.close()
print('Script autónomo y carga automática correctos')
'''
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
            resultado = subprocess.run([sys.executable, '-I', '-c', programa,
                                        str(destino/'arbol.py')], cwd='/', env=env,
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == '__main__':
    unittest.main()
