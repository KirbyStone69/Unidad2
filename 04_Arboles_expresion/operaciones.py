"""Catálogo de operaciones reales. Las funciones trigonométricas usan radianes."""
from dataclasses import dataclass
import math
import operator
import numpy as np
from typing import Callable


@dataclass(frozen=True)
class Operacion:
    nombre: str
    operandos: int
    funcion: Callable[..., float]
    funcion_vectorial: Callable | None = None

    def aplicar(self, *valores):
        if len(valores) != self.operandos:
            raise ValueError(f'{self.nombre} requiere {self.operandos} operandos.')
        if not all(math.isfinite(valor) for valor in valores):
            raise ValueError('Los operandos deben ser números reales finitos.')
        try:
            resultado = self.funcion(*valores)
            if isinstance(resultado, complex) or not math.isfinite(resultado):
                raise ValueError('Resultado fuera de los números reales finitos.')
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            raise ValueError(f'{self.nombre}: operación sin resultado real finito ({error}).') from error
        return resultado


    def aplicar_vector(self, *valores):
        if len(valores) != self.operandos:
            raise ValueError(f'{self.nombre} requiere {self.operandos} operandos.')
        if not all(np.all(np.isfinite(valor)) for valor in valores):
            raise ValueError('Los operandos deben ser finitos.')
        try:
            with np.errstate(divide='raise', invalid='raise', over='raise'):
                resultado = self.funcion_vectorial(*valores)
            if not np.all(np.isfinite(resultado)):
                raise ValueError('Resultado no finito.')
        except (FloatingPointError, OverflowError, ZeroDivisionError) as error:
            raise ValueError(f'{self.nombre}: dominio inválido en los datos.') from error
        return resultado


def tangente(angulo):
    if abs(math.cos(angulo)) < 1e-12:
        raise ValueError('Tangente indefinida cerca de π/2 + kπ.')
    return math.tan(angulo)


def tangente_vectorial(angulo):
    if np.any(np.abs(np.cos(angulo)) < 1e-12):
        raise ValueError('Tangente indefinida cerca de π/2 + kπ.')
    return np.tan(angulo)


OPERACIONES_VALIDAS = {
    '+': Operacion('Suma', 2, operator.add, np.add),
    '−': Operacion('Resta', 2, operator.sub, np.subtract),
    '×': Operacion('Multiplicación', 2, operator.mul, np.multiply),
    '/': Operacion('División', 2, operator.truediv, np.divide),
    '%': Operacion('Módulo', 2, operator.mod, np.remainder),
    '^': Operacion('Potencia', 2, math.pow, np.float_power),
    '√': Operacion('Raíz cuadrada', 1, math.sqrt, np.sqrt),
    'ln': Operacion('Logaritmo natural', 1, math.log, np.log),
    'sin': Operacion('Seno', 1, math.sin, np.sin),
    'cos': Operacion('Coseno', 1, math.cos, np.cos),
    'tan': Operacion('Tangente', 1, tangente, tangente_vectorial),
}
