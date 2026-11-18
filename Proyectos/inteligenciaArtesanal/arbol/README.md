# ARBOL · Genetic Lab

Laboratorio de regresión simbólica de escritorio, exclusivamente PyQt6, con motor
propio de programación genética híbrida, NumPy, SciPy y Matplotlib embebido.
Interfaz en español, árboles interactivos y animaciones educativas.

## Ejecutar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Si ya tienes el entorno, actualiza dependencias con el segundo comando: esta
versión incorpora SciPy. Reinicia la aplicación para cargar los cambios.
Linux necesita una sesión gráfica y bibliotecas Qt de X11/Wayland. Las pruebas
usan `QT_QPA_PLATFORM=offscreen` y no requieren escritorio.

## Buscar una expresión

El botón **Random**, junto al título **03 / Datos y predicción**, crea 80 puntos
de una nueva función aleatoria usando las funciones habilitadas. Limpia el resultado
anterior y deja los datos listos para pulsar **Iniciar**. Está desactivado durante
una búsqueda; la fórmula generada no se entrega al motor.

1. **Cargar CSV**: encabezados y separadores coma, punto y coma o tabulador.
   Se eligen automáticamente las primeras dos columnas, x/y. Puedes cambiar las
   columnas en el panel y pulsar **Aplicar columnas**. Notación científica admitida;
   valores finitos con punto decimal, sin celdas vacías, dentro de ±1e6.
2. Elige familias de funciones y presupuesto. Los valores iniciales recomendados
   son 100 individuos, altura 6, 127 nodos, generaciones sin límite y 4 ajustes locales
   de hasta 100 evaluaciones por generación.
3. **Iniciar** crea una búsqueda reproducible con la semilla seleccionada.
   **Pausar** actúa al terminar la generación actual; **Continuar** reanuda;
   **Una generación** inicia en pausa o avanza un paso. **Detener** cancela también
   dentro del ajuste numérico y conserva la mejor generación publicada.
4. No hay límite de tiempo. **Generaciones: Sin límite** (valor 0) permite buscar
   hasta alcanzar el objetivo NMSE de entrenamiento o pulsar **Detener**. Puedes
   indicar un límite de generaciones o desactivar la parada por error. Aumentar la altura
   amplía la gramática, pero también aumenta el espacio de búsqueda.
5. **Ver mejor árbol** muestra la candidata encontrada. Rueda: zoom; arrastrar:
   desplazar; **Ajustar**: encuadrar. El texto de la expresión puede seleccionarse.
   **Copiar fórmula** copia una expresión NumPy con precisión completa y las mismas
   protecciones numéricas; requiere `import numpy as np` y una variable `x`.

La curva representa la mejor candidata disponible. La interfaz distingue entre
ajuste insuficiente, parcial y objetivo alcanzado. Nunca se garantiza encontrar
una expresión exacta o extrapolar correctamente fuera del dominio observado.
Expresiones diferentes pueden representar la misma función, por ejemplo coseno
y seno con un desfase de π/2.

## Comparar las mejores soluciones por generación

El panel **04 / Mejor solución por generación** registra una sola propuesta por
generación, con expresión, MSE, NMSE y cantidad de nodos. La generación 0 es la
población inicial. El historial conserva todas las generaciones aunque el motor
avance entre dos refrescos de pantalla. Una actualización de la misma generación
reemplaza su registro. **Copiar expresión seleccionada** copia la fórmula NumPy
con precisión completa.

La gráfica del **panel 03** muestra las curvas de ese mismo historial junto a los
datos originales y destaca la predicción ganadora en rojo oscuro (`#B83240`).
Los colores del historial corresponden a las
filas de la tabla. **Mejores por generación** muestra u oculta las curvas del
historial. **Rango de datos** mantiene el encuadre de los datos; desmárcalo para
incluir también las predicciones alejadas. CSV, Random y una nueva búsqueda
limpian tanto la tabla como las curvas.

**Elitismo** configura cuántos individuos conserva el algoritmo entre generaciones
(por defecto 2). La visualización siempre guarda únicamente el campeón por MSE
de cada generación. Los errores mostrados son de entrenamiento. La evaluación de
curvas se cachea por árbol y el refresco utiliza blitting.

## Entrenamiento y validación

Por defecto, 80% de las filas se usa para entrenar y 20% se reserva mediante una
división aleatoria determinista. Los valores reservados **no** intervienen en la
evolución, ajuste de constantes ni selección de la mejor candidata. La división
se desactiva con menos de 10 filas o fracción cero.

MSE, NMSE y R² son de **entrenamiento**. El NMSE de validación se muestra aparte
con los tamaños de ambas muestras. NMSE = MSE / max(var(y), 1e-12); R² = 1 − NMSE.
En datos constantes se utiliza ese denominador de protección. Si el objetivo de
entrenamiento se alcanza y la validación es mala, aparece una advertencia de
posible sobreajuste. La validación es orientativa; datos correlacionados pueden
requerir una partición temporal o por grupos que esta versión no implementa.

## Biblioteca y motor

- Aritmética `+ − × ÷` y funciones seleccionables: `sin`, `cos`, `square`, `cube`,
  `exp`, `log`, `sqrt`, `tanh`, `abs`. El grupo opcional **Extras** añade
  `atan` (arcotangente), `sigmoid` (sigmoide estable) y `neg` (negación).
  Actívalo en la biblioteca para incluir esas funciones en la búsqueda y en Random. Terminales `x`, constantes reales y `pi`/`e`.
- Árboles inmutables con aridad validada; evaluación vectorizada y simplificación
  de identidades seguras. Límites independientes de altura y cantidad de nodos.
- Inicialización mixta, torneo de cuatro, elitismo, cruce de subárboles y
  mutaciones de constante, operador, subárbol y poda. Se conserva un archivo de
  mejor error de entrenamiento, aunque la penalización de tamaño favorezca otra
  candidata en la selección.
- Inmigración y exploración reforzada tras 12 generaciones sin mejora significativa.
  La diversidad mostrada cuenta estructuras distintas, ignorando sus constantes.
- Propuestas de gramática: potencias, sumas polinómicas, racionales y funciones
  elementales con distintas escalas/fases. Son propuestas iniciales para la misma
  evolución, independientes de y; no son un reconocimiento garantizado de fórmulas.
- Ajuste afín y optimización local acotada de hasta diez constantes por candidato.
  Se distribuye el presupuesto entre propuestas estructurales y mejores individuos.
  Cada evaluación del residual cuenta, también las usadas para el Jacobiano.
- Caché acotada de fitness, semilla fija y cancelación cooperativa.

El ajuste local usa [least_squares de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
La búsqueda combina exploración genética de estructuras y ajuste numérico de
coeficientes. Con ajustes locales en cero se conserva la evolución estructural.

### Semántica numérica protegida

Cada terminal/resultado se limita a ±1e6. División con |denominador| ≤ 1e-8 devuelve
1; `log(x)` significa log(max(|x|, 1e-12)); `sqrt(x)` significa sqrt(|x|);
`exp(x)` recorta el argumento entre −20 y log(1e6). Las funciones trigonométricas
usan radianes. Estas protecciones forman parte del modelo, también al exportarlo.

## Modo educativo

Cruce: rama saliente rosa y entrante verde, con desplazamiento. Mutación: valor
anterior → nuevo. Reparación: espécimen con exceso de altura y sustitución por
terminales x. El espécimen con exceso usa una cadena de tamaño lineal, y el
resultado respeta tanto la altura como el límite de nodos. Al cancelar, cambiar
datos o cerrar la ventana se invalidan frames y callbacks anteriores.
Las operaciones actúan sobre una **copia educativa**; no cambian
la población. La gráfica se identifica como educativa y las métricas inferiores
siguen perteneciendo a la búsqueda. **Ver mejor árbol** restaura su predicción.

**Evaluar árbol** recorre desde terminales hasta raíz y muestra resultados de un
valor de x en los tooltips. **⏯ Animación** pausa/reanuda la animación actual;
la velocidad se aplica a la siguiente animación. Las funciones activadas también
se respetan en los ejemplos educativos.

## Rendimiento y verificación

El motor no depende de Qt. Un QThread publica instantáneas inmutables. Los widgets
solo se actualizan en el hilo principal y la escena no se reconstruye por candidato
ni por generación automática. La predicción se refresca cada 120 ms como máximo;
la gráfica compartida usa
[caché de fondo y blitting de Matplotlib](https://matplotlib.org/stable/users/explain/animations/blitting.html).
La gráfica del panel 03 puede enfocar el rango de los datos o incluir todas las
predicciones mediante el control **Rango de datos**. No hay una segunda gráfica
en el panel 04.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
.venv/bin/python -m benchmarks.search
.venv/bin/python -m benchmarks.desktop
```

Resultados reproducibles y capturas:

- [Benchmark](docs/benchmark.json)
- [Informe](docs/VALIDATION.md)
- [Mejores soluciones por generación](docs/POPULATION-PANEL.md)
- [Reparación y pruebas nativas de Qt](docs/REPAIR-2026-10-21.md)
- [Responsividad Qt](docs/responsiveness.json)
- [Vista previa](docs/preview.png)

Archivos: `expressions.py` define la gramática; `optimization.py`, ajuste local;
`engine.py`, evolución; `worker.py`, concurrencia; `tree_view.py`, escena;
`plots.py`, gráficas; `window.py`, controles y datos.


## Pruebas de reparación y ciclo de vida de Qt

Las pruebas de `tests/test_native_animation.py` se ejecutan en procesos separados:
pueden detectar abortos/segfaults nativos sin derribar el resto de pytest. Cubren
operaciones rápidas, funciones unarias, cambios de tamaño, fases de animación,
cierre y destrucción de ventanas, y un trabajador activo durante reparación.
El bucle de eventos permanece vivo después del cierre para procesar señales
pendientes y `deleteLater`. También hay pruebas de callbacks cancelados, carga
de CSV durante reparación, presupuestos de nodos y propiedades de reparación
con diferentes alturas, tamaños y funciones.
