# Verificación del motor ampliado

Distribución actual: curvas y puntos integrados en el panel 03, tabla en 04.
**133 pruebas aprobadas en 29.60 s**; ver [detalles](POPULATION-PANEL.md).

Panel 04 actualizado: **132 pruebas aprobadas en 30.55 s**. Ver
[comparación de élites y población](POPULATION-PANEL.md).

Actualización 2026-10-21: **119 pruebas aprobadas en 33.10 s** tras corregir
reparación y cancelación de animaciones. Véase [informe de reparación](REPAIR-2026-10-21.md).
Las mediciones del motor que siguen corresponden a la versión del 20 de octubre.

Fecha: 2026-10-20. Python 3.13.5. Plataforma: Linux-6.12.111+deb13-amd64-x86_64-with-glibc2.41.

## Pruebas automatizadas

La suite completa pasó 74 pruebas en 17.51 s. Incluye gramática/aridad, valores extremos, exportación NumPy protegida, constantes, presupuestos, cancelación, límites de árbol, reproducción con semilla, aislamiento de validación, CSV, controles y responsividad Qt.

Una revisión independiente ejecutó adicionalmente 51 pruebas de expresiones e interfaz sin fallos y verificó selección, validación y caché de dibujo.

## Descubrimiento de expresiones

100 individuos, máximo 100 generaciones, altura 6, hasta 127 nodos, 4 ajustes locales por generación y 100 evaluaciones por ajuste. Semillas 7, 42 y 91. División 80/20: validación nunca participa en optimización ni selección. Se prueban también 201 puntos adicionales, usando la función de referencia solo en el benchmark.

| Datos | Tiempo por búsqueda (s) | Generaciones | Peor NMSE entrenamiento | Peor NMSE validación | Peor NMSE en malla adicional |
|---|---:|---|---:|---:|---:|
| CSV usuario | 1.00–1.87 | 7, 11, 11 | 8.54e-32 | 6.33e-32 | 1.03e-31 |
| Coseno cúbico diferente | 0.94–2.64 | 7, 11, 11 | 1.92e-31 | 2.24e-31 | 2.31e-31 |
| Seno con fase | 0.91–2.13 | 12, 18, 26 | 2.6e-17 | 2.46e-17 | 2.57e-17 |
| Exponencial | 0.85–1.97 | 20, 12, 10 | 8.75e-32 | 9.91e-32 | 1.05e-31 |
| Racional | 0.33–0.73 | 5, 5, 5 | 1.89e-31 | 2.32e-31 | 2e-31 |
| Polinomio | 0.08–0.30 | 1, 3, 3 | 3.2e-32 | 5.41e-32 | 3.89e-32 |

Los 18 ensayos alcanzaron el objetivo. Esto describe esos conjuntos y semillas; no garantiza resultados para otras funciones, ruido o rangos.

Para gr.csv, una expresión descubierta fue `6.67 + 11*cos(7.23*cube(x) + 1.65e-16)`. La semilla 42 produjo la equivalente `6.67 - 11*sin(7.23*cube(x) - pi/2)`. Los números son ajustados a partir de entrenamiento; no figuran en la implementación de la gramática.

## Fluidez de la interfaz

Medición offscreen con el CSV del usuario: 3.34 s, 98 pulsos de un temporizador de control de 10 ms y máximo intervalo observado 0.098 s. Incluye gráficas y renderizado final. No es una garantía de latencia en otros equipos.

La prueba detectó primero redibujados completos de Matplotlib de aproximadamente 1 s durante competencia con el trabajador. La corrección conserva ejes/fondo y actualiza solo líneas mediante blitting. También hay una prueba de que diez actualizaciones consecutivas de predicción no redibujan ejes estáticos.

## Reproducir

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
.venv/bin/python -m benchmarks.search
.venv/bin/python -m benchmarks.desktop
```

Los resultados numéricos originales están en [benchmark.json](benchmark.json), la medición de Qt en [responsiveness.json](responsiveness.json) y la imagen en [preview.png](preview.png).
