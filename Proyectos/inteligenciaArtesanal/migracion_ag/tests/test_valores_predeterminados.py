import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compatibilidad as cpp


class ValoresPredeterminados(unittest.TestCase):
    def test_sin_argumentos_usa_intervalos_del_libro_y_semilla_automatica(self):
        casos = [('maximizacion', False, (0.0,32.0)),
                 ('minimizacion', False, (-250.0,250.0)),
                 ('multivariable', True, ('0,0','100,100'))]
        for nombre, multi, limites in casos:
            with self.subTest(programa=nombre), patch('secrets.randbits', return_value=12345):
                args = cpp.argumentos(multivariable=multi, programa=nombre, argv=[])
                self.assertEqual((args.x_min,args.x_max),limites)
                self.assertEqual(float(args.TOL),0.0001)
                self.assertEqual((args.tam_pob,args.num_gen),(500,1000))
                self.assertEqual((args.prob_cruce,args.prob_mut),(0.4,0.001))
                self.assertEqual(cpp.SEMILLA_USADA,12345)

    def test_valores_explicitos_siguen_teniendo_prioridad(self):
        args=cpp.argumentos(argv=['1','5','0.01','50','10','0.2','0.1','--semilla','7'])
        self.assertEqual((args.x_min,args.x_max,args.TOL),(1,5,0.01))
        self.assertEqual((args.tam_pob,args.num_gen),(50,10))
        self.assertEqual(cpp.SEMILLA_USADA,7)


if __name__ == '__main__':
    unittest.main()
