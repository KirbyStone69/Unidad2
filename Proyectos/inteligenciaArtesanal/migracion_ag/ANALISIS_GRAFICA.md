# Elección de la gráfica y validación

La opción elegida para este proyecto es **una gráfica de dispersión x/f(x)**,
que empieza vacía y crece con las evaluaciones reales del algoritmo. Conserva
población actual y mejor individuo actual como capas diferenciadas. Se mantienen
`-maxi`, `-mini`, la semilla automática y la ejecución sin otros argumentos.

## Requisitos y alternativas

| Alternativa | Ventaja | Decisión para este proyecto |
|---|---|---|
| Curva matemática calculada de antemano | Muestra inmediatamente toda la función | Descartada: el usuario quiere construirla desde los datos del algoritmo |
| Unir los puntos con una línea | Apariencia de una curva continua | Descartada: sugeriría valores intermedios no evaluados |
| Solo población actual | Poco trabajo gráfico | Válida, pero al converger desaparece la exploración anterior |
| Puntos acumulados + población actual + mejor actual | Explica qué regiones se exploraron y dónde está la población | Elegida, con refresco separado del cálculo |

No se añade una segunda gráfica de tiempo ni se fuerza un máximo histórico.
En minimización el eje vertical representa **aptitud_bruta = f(x)**; los pesos
transformados de ruleta no representan una función fija de x.

## Problemas encontrados y correcciones

Tres subagentes revisaron, por separado, diseño/semántica, rendimiento y pruebas.
Las revisiones y los experimentos identificaron:

1. **Pérdida de evaluaciones:** observar solo las poblaciones tras cada fase
   omitía hijos rechazados e intermedios de mutación. En una prueba reproducible
   había 122 pares evaluados únicos y solo 119 observados en poblaciones.
   Ahora adaptacion emite el par x/f realmente calculado; el registro es completo.
2. **Saturación de dibujos:** medir el intervalo desde el inicio del render
   permitía dibujar consecutivamente si un render ya tardaba más de 50 ms.
   Ahora se mide desde el final y se ajusta el intervalo al costo observado.
3. **Redibujos automáticos adicionales:** se desactivó el autoscheduling de
   pyplot. La aplicación controla el render y atiende los eventos explícitamente.
4. **Coste de redibujar ejes y etiquetas:** el renderer usa blitting cuando
   el canvas lo admite, y redibujado completo como alternativa.
5. **Límites móviles y caché:** los límites Y solo se expanden cuando los datos
   lo requieren; redimensionar o redibujar renueva el fondo de blitting.
6. **Cierre y números reutilizados:** se observa el evento de cierre y la
   identidad de la figura; cerrar deja de preparar/redibujar artistas.
7. **Exportación pendiente:** guardar obtiene los datos completos actuales,
   aunque la pantalla no se haya refrescado. La precisión exportada es de
   17 cifras significativas para conservar los float de Python.

## Estructura final

- `maximizacion.py` y `minimizacion.py` mantienen las operaciones originales.
  Sus main admiten observadores opcionales de fase y evaluación.
- `compatibilidad.py` restaura el observador de evaluación al terminar o ante
  una excepción; la captura no consume números del generador genético.
- `grafica.py` separa captura, preparación de puntos, renderer y exportación.
  El dibujo reutiliza los objetos de Matplotlib, en lugar de crear figuras
  o series nuevas en cada fase.
- Azul: todas las coordenadas evaluadas acumuladas, sin duplicar x.
- Gris: población actual, incluidos los individuos superpuestos.
- Rojo: individuo actual que señala el algoritmo; no se le atribuye ser el
  mejor histórico global.

La pantalla muestra como máximo **10 000 puntos reales** de la nube histórica,
seleccionados determinísticamente cuando hay más. No se interpolan coordenadas.
El contador indica cuántos puntos existen y cuántos son visibles. La población
actual y el marcador se dibujan aparte. **Los TXT conservan todos los pares
únicos**, incluyendo los que no se muestran por el límite visual.

Los refrescos regulares esperan al menos 50 ms desde el dibujo anterior,
y ese intervalo aumenta si dibujar resulta costoso. Los estados inicial/final
pueden forzar un refresco para que sean visibles. El factor adaptativo es una heurística: no garantiza
un porcentaje máximo de overhead. No hay time.sleep ni pyplot.pause.
Entre dibujos se atienden eventos GUI; cerrar la ventana no cambia el criterio
de terminación original y el algoritmo sigue calculando/guardando sin dibujar.

## Fuentes consultadas

La documentación oficial recomienda atender la GUI mediante flush_events y
solicitar redibujos mediante draw_idle; advierte que atenderla más a menudo
consume recursos que podrían dedicarse al cálculo.
[Guía de interacción de Matplotlib](https://matplotlib.org/stable/users/explain/figure/interactive_guide.html).

Blitting conserva un fondo estático y dibuja únicamente los artistas que
cambian. Depende del soporte del canvas y requiere actualizar el fondo si la
figura cambia de tamaño. Estos aspectos se implementaron y probaron.
[Documentación oficial de blitting](https://matplotlib.org/stable/users/explain/animations/blitting.html).

Se distingue un canvas de ventana GUI de uno que solo genera archivos, en
lugar de mantener una lista negativa de nombres de backend.
[Backends de Matplotlib](https://matplotlib.org/stable/users/explain/figure/backends.html).

## Mediciones

Se usó Python 3.13 y Matplotlib 3.11.1, con Agg para comparar render y QtAgg
offscreen para ejecutar una GUI real sin abrir ventanas en el escritorio.
Semilla 12345, funciones originales, intervalo configurado [-10,10].
Todos los modos producen **la misma población completa y el mismo estado RNG**.

### Comparación del renderer

50 individuos, 30 generaciones, mutación 0.01, tres repeticiones; mediana.
Se fuerzan los mismos 121 frames para comparar métodos con igual cantidad de
trabajo. Estos modos son experimentos, no la frecuencia de la aplicación normal.

| Tiempo del algoritmo + render | Maximización | Minimización |
|---|---:|---:|
| Redibujar toda la figura | 9.709 s | 7.893 s |
| Redibujado parcial (blit) | 3.056 s | 2.655 s |
| Reducción medida | 68.5 % | 66.4 % |

Datos: `referencia/benchmark_grafica_despues.json`. Esta comparativa se realizó
antes del último ajuste del espacio de la leyenda, con ambos métodos usando el
mismo diseño. No se equiparan los números históricos de un constructor anterior,
que tenía argumentos incorrectamente enlazados; esa limitación está registrada.

### Carga mayor con refresco normal

500 individuos, 100 generaciones, mutación 0.001, una repetición por modo.
Esta prueba mide el tamaño de población habitual, pero no la totalidad de las
1000 generaciones predeterminadas. La construcción inicial de la figura y la
exportación gráfica final quedan fuera del tiempo medido.

| Tiempo | Maximización | Minimización |
|---|---:|---:|
| Solo algoritmo | 3.031 s | 3.879 s |
| Captura completa sin dibujar | 3.145 s | 4.172 s |
| Captura + GUI normal | 5.098 s | 5.051 s |

Datos: `referencia/benchmark_grafica_realista.json`. Hubo 18/20 blits y un
redibujado completo por ejecución; se guardaron 4913/4515 muestras únicas.
La GUI procesó 105 eventos de un timer en cada ejecución; sus mayores intervalos
observados fueron 94/98 ms. Esto demuestra atención de eventos en ese experimento,
no una garantía de latencia ni una prueba de interacción humana.

Una segunda comprobación del código final está en
`referencia/benchmark_grafica_verificacion_final.json`; conserva la equivalencia
de población y RNG. Los tiempos varían entre tandas y no deben interpretarse
como garantías de velocidad. **Mostrar una gráfica cuesta tiempo**, aunque no
haya sleeps; la optimización reduce ese coste, no lo elimina.

## Pruebas

**68 pruebas aprobadas**, ninguna omitida en el entorno completo:

- Captura de todas las llamadas a adaptacion, incluyendo hijos descartados.
- Mismo resultado, población completa y RNG con/sin observadores.
- Limpieza del observador tras excepciones y contextos anidados.
- Gráfica inicialmente vacía, una sola figura de ejes y sin interpolación.
- Minimización con aptitud bruta; flags exclusivos; semilla y cero generaciones.
- Cap visual sin pérdida en el TXT y exportación con muestras pendientes.
- Refresco medido desde el fin del dibujo y límites que solo se expanden.
- GUI QtAgg offscreen: blit, resize, cierre, eventos y prohibición de sleep/pause.
- Píxeles: el marcador se mueve sin dejar estela y permanece correcto tras
  zoom, resize y render final normal.
- Comparación de algoritmos contra la referencia C++ declarada.

Registro: `referencia/pruebas.txt`. Vistas de comprobación en `referencia/vistas/`.

## Reproducir

```bash
python grafica.py -maxi
python grafica.py -mini
python -m unittest discover -s tests -v
python referencia/benchmark_grafica.py --gui
python referencia/benchmark_grafica.py --gui --population 500 --generations 100 \
  --mutation 0.001 --repetitions 1 --modes baseline capture gui
```

El benchmark usa carpetas temporales y conserva los TXT del usuario. Sus
resultados se imprimen como JSON; puede redirigirse la salida a un archivo.
