"""Lectura de puntos x,y y métricas de ajuste sobre todos los datos."""
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def vector_finito(valores):
    vector = np.array(valores, dtype=float, copy=True)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise ValueError('Se requiere una lista no vacía de números finitos.')
    return vector


@dataclass(frozen=True)
class DatosGrafica:
    x: object
    y: object
    nombre: str = 'Datos x,y'

    def __post_init__(self):
        x, y = vector_finito(self.x), vector_finito(self.y)
        if x.shape != y.shape:
            raise ValueError('x e y deben tener la misma cantidad de puntos.')
        x.setflags(write=False)
        y.setflags(write=False)
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)


def cargar_csv(ruta):
    x, y = [], []
    with Path(ruta).open(encoding='utf-8-sig', newline='') as archivo:
        muestra = archivo.read(4096)
        archivo.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=',;\t')
        except csv.Error:
            dialecto = csv.excel
        lector = csv.DictReader(archivo, dialect=dialecto)
        if lector.fieldnames is None:
            raise ValueError('El CSV está vacío. Se requieren columnas x,y.')
        nombres = {nombre.strip().lower(): nombre for nombre in lector.fieldnames}
        if 'x' not in nombres or 'y' not in nombres:
            raise ValueError('El CSV debe tener encabezados x,y.')
        for fila in lector:
            try:
                vx, vy = float(fila[nombres['x']]), float(fila[nombres['y']])
                if not np.isfinite(vx) or not np.isfinite(vy):
                    raise ValueError('Dato no finito')
            except (ValueError, TypeError, KeyError) as error:
                raise ValueError(f'Valores x,y inválidos en la fila {lector.line_num}.') from error
            x.append(vx)
            y.append(vy)
    return DatosGrafica(x, y, Path(ruta).name)


def calcular_errores(esperado, predicho):
    y, pred = vector_finito(esperado), vector_finito(predicho)
    if y.shape != pred.shape:
        raise ValueError('Las predicciones deben corresponder a todos los datos.')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            sse = float(np.sum(np.square(pred - y)))
            energia = float(np.sum(np.square(y)))
            mse = sse / y.size
            nmse = sse / energia if energia != 0 else None
    except (FloatingPointError, OverflowError) as error:
        raise ValueError('El error excede el rango numérico.') from error
    if not np.isfinite(mse) or (nmse is not None and not np.isfinite(nmse)):
        raise ValueError('El error no es finito.')
    return mse, nmse
