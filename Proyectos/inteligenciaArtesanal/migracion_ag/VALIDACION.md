# Validación realizada

Fecha: 13 de octubre de 2026. Entorno: Linux, Python 3.13, g++ con C++17;
IEEE-754 binary32/binary64, biblioteca matemática del sistema.

## Pruebas automatizadas

Comando desde la raíz del proyecto:

```bash
python3 -m unittest discover -s migracion_ag/tests -v
```

**74 pruebas aprobadas, ninguna omitida**, incluidas las tres diferenciales.
Registro completo: [referencia/pruebas.txt](referencia/pruebas.txt).
Se comprobaron operaciones genéticas, copias por valor, binario LSB primero,
float32, umbrales, inversión de bits, élite original, acceso al final de ruleta,
selección impar, cruce fuera de rango y modo estricto, fitness cero, límites
numéricos extremos y ejecución por CLI de cada programa.

La suite primero falló por módulos ausentes; cada programa se migró y verificó
secuencialmente. La comparación diferencial detectó y permitió corregir los
intermedios float32 y la diferencia sinf/sin double en multivariable. La prueba
regresiva distingue una entrada para la cual sinf difiere en un ulp de redondear
math.sin. Los límites extremos también se verificaron fallando antes de corregir
el manejo del error. No se impone una prueba de convergencia universal.

## Comparación contra C++

[preparar_referencia.py](referencia/preparar_referencia.py) parte de los archivos
transcritos en `original/`, aplica R1–R8 y crea los enlaces multivariable E1.
Se compila con `-std=c++17 -O0 -ffp-contract=off` en un directorio temporal.
El driver añadido reemplaza main para observar cada fase. Las transcripciones
no se modifican ni se confunden con la referencia ejecutable.

Se usaron tres secuencias independientes de enteros (semillas 0, 7, 42),
RAND_MAX=32767, 50 individuos y tres generaciones en cada variante.
Inicialización más selección/reproducción/mutación/evaluación por generación
produce 13 estados observados por ejecución: **117 estados de población y
5850 registros de individuos** en las nueve ejecuciones comparadas.

Se comparan:

- Todos los bits y elite, con igualdad exacta.
- Índice del mejor y número de llamadas a rand, con igualdad exacta.
- Fenotipos, aptitud, aptitud bruta, puntuación relativa, acumulado, cmax y suma,
  con tolerancia absoluta 1e-11.

Las longitudes son 5 en escalares y [5,4,6] en multivariable; se usan tasas de
cruce 0.8 y mutación 0.15 para ejercitar frecuentemente las operaciones.
Los CLI prueban además el cálculo de longitud y los intervalos del libro.
La referencia de maximización conserva su `<` y la élite conserva su
sobrescritura de slots. La prueba no compara contra memoria sin inicializar.

## Ejecuciones de los tres programas

Todas finalizaron con código de salida 0 y semilla 7:

| Programa | Población × generaciones | Resultado |
|---|---|---|
| Maximización, ejemplo íntegro del libro | 500 × 1000 | 22.3137 en 31.5005 |
| Minimización, intervalo [-250,250] | 500 × 100 | -201.843 en -203.814 |
| Multivariable, dos intervalos [0,100] | 500 × 100 | -127.27 en [65.5536,65.5449] |

Comandos, salida, incidencias R1 y tiempos están guardados en
[ejemplo_libro.txt](referencia/ejemplo_libro.txt),
[ejecucion_minimizacion.txt](referencia/ejecucion_minimizacion.txt) y
[ejecucion_multivariable.txt](referencia/ejecucion_multivariable.txt).

El libro indica 22.3136 para el máximo en 31.5005; la ejecución de su fórmula
muestra 22.3137 a seis cifras significativas. No se cambió la fórmula para
forzar la cifra del texto. El mínimo escalar es simétrico por el valor absoluto
exterior, por lo que el punto negativo coincide con el valor publicado.

También se ejecutó `python3 -m py_compile` sobre los cuatro módulos de uso.
La revisión independiente encontró únicamente el manejo de desbordamientos de
entrada, corregido con una prueba que falló antes y pasó después. En el cotejo
visual final ampliado se identificó Tvac_int y se registró como errata R8.

## Límites de esta evidencia

La plataforma histórica de C++ y su generador rand no están especificados.
La misma semilla en otra biblioteca C no basta para producir igual población.
El tratamiento de comportamiento indefinido y los enlaces ausentes no tienen
una equivalencia literal demostrable con el documento. Están enumerados en
[REPORTE.md](REPORTE.md); las pruebas verifican la reconstrucción declarada.


## Salida TXT añadida

Los tres CLI se ejecutaron en carpetas temporales y se verificó que sus
TXT contienen los parámetros, la semilla 7, el resultado real mostrado por
consola, el genotipo y el recuento de correcciones. La comparación C++
sigue pasando después de añadir la salida. La gráfica guarda 1000 filas
con las dos columnas x/f(x), comprobadas con ejecución sin interfaz gráfica.

La gráfica ahora ejecuta maximización y utiliza el fenotipo y aptitud
del individuo devuelto por main. Se verificó la ejecución completa con
500 individuos y 1000 generaciones sin interfaz gráfica: el marcador rojo
coincide exactamente con ese individuo y el TXT registra los mismos valores.


## Panel fijo y semilla automática

Se observaron primero las pruebas fallando por ausencia del panel y por usar
el segundo actual como semilla. Tras implementar la visualización, se verificó
la salida interactiva de los tres programas, incluidos padres/hijos reales,
corte, mutación y última generación. El resultado y la población completa
con/sin panel coinciden exactamente para la misma semilla. La generación de
semilla automática y el override explícito se verificaron por separado.
También se ejecutó maximización en una terminal real PTY con 50 individuos y
5 generaciones: bloque fijo de 16 líneas, semilla automática y TXT generado.
La suite diferencial C++ sigue pasando y el total es 45 pruebas aprobadas.


## Comandos sin argumentos

47 pruebas aprobadas tras añadir defaults. Se ejecutaron además los tres
scripts sin ningún argumento, en carpetas temporales: todos terminaron con
código 0, usaron 500 individuos y 1000 generaciones y guardaron una semilla
automática numérica en su TXT. Registro: referencia/prueba_sin_argumentos.txt.
Los parámetros explícitos y las comparaciones C++ siguen pasando.


## Gráfica en vivo

Suite completa ejecutada con el Python de entorno: 49 pruebas aprobadas,
ninguna omitida. Se verificó la secuencia real de fases, el resultado idéntico
con/sin observador, los offsets de toda la población y mejor punto, los tiempos
crecientes y el TXT de evolución. La prueba visual usa backend Agg, sin ventanas,
y una ejecución de 30 generaciones registró 121 fases y produjo la imagen de
comprobación. La interacción con la ventana requiere un backend gráfico en el
entorno del usuario; no se prueba un escritorio GUI desde esta ejecución sin pantalla.


## Gráfica mínima y reducción de trabajo gráfico

52 pruebas aprobadas con el entorno completo. Se verificaron minimización
con/sin observador con población idéntica, curva mínima no positiva,
aptitud_bruta para los puntos y archivos de salida separados. Se comprobaron
una sola figura de ejes por modo y ausencia de preparación de puntos cuando
aún no corresponde refrescar; cada fase sigue registrándose. No se introdujo
sleep ni pausa artificial, aunque dibujar tiene su propio costo de procesamiento.


## Gráfica basada exclusivamente en datos del algoritmo

53 pruebas aprobadas. Se verificó que la figura empieza vacía y no contiene
una curva predefinida; dos observaciones producen exactamente los dos pares
recibidos. Una ejecución repetida con la misma semilla y observador independiente
produjo el mismo conjunto de pares que grafica.py. El TXT ahora tiene una fila
por x observado, sin requerir 1000 filas. Los operadores siguen coincidiendo
con la referencia C++ y las pruebas con/sin observador.


## Validación de visualización revisada

68 pruebas, ninguna omitida, incluidas dos pruebas de GUI QtAgg offscreen.
Se compararon evaluaciones completas, poblaciones y RNG; se probó limpieza del
observador, exportación pendiente y precisión, cap visual, eventos de cierre y
reutilización de números, límites estrictamente expansivos y reloj desde fin
del refresco. La prueba de píxeles valida marcador sin estela tras zoom/resize
y en el render final. Nuevas mediciones e interpretación en ANALISIS_GRAFICA.md.
Se conserva la comparación diferencial C++ del algoritmo. La cobertura GUI
actual amplía los experimentos anteriores realizados solo con Agg.


## Demo de reinas

Cuatro nuevas pruebas: vector impreso y orientación del tablero, único conflicto
diagonal de ese vector, OX con resultados conocidos, conservación de permutaciones
en 100 cruces aleatorios y rechazo de entradas inválidas. GUI Tkinter ejecutada
con cuatro tableros/32 reinas, botones y vista compacta comprobados en 944×508.
La revisión independiente no encontró errores en cruce, colores o coordenadas.
Las imágenes no especifican el operador OX: se identifica como añadido didáctico.


Búsqueda automática de reinas: 74 pruebas aprobadas en la suite completa.
Las nuevas pruebas verifican 20 semillas, conservación de permutaciones,
elitismo, solución sin ataques y detención del algoritmo, además de mutación
por intercambio sin modificar el padre. Se comprobó la ventana Tkinter hasta
el ganador, el guardado TXT, reinicio y cierre con actualización pendiente.


Actualización de vista continua: suite completa con 75 pruebas aprobadas.
La prueba Tkinter verifica el quinto tablero debajo de los cuatro originales,
dos soluciones sucesivas sin detener las actualizaciones y ausencia de
escrituras de resultados. El ganador permanece visible al iniciar la siguiente búsqueda.


Continuidad del elitismo: 76 pruebas aprobadas en la suite completa.
Se verifica que continuar después de un ganador conserva por copia las dos
mejores cadenas y aumenta la generación, sin sustituir la búsqueda ni escribir
resultados. La interfaz muestra ambas élites con sus conflictos. El contador
de hallazgos se identifica explícitamente como incluyendo repeticiones.


Comportamiento final: se detiene al primer ganador. Las 76 pruebas pasan;
la prueba de interfaz confirma que no quedan actualizaciones programadas,
la generación deja de cambiar y el ganador queda debajo de los cuatro tableros.
El reinicio manual inicia otra búsqueda, manteniendo el elitismo y sin TXT.


N reinas configurable: suite completa de 79 pruebas aprobadas.
Se verificaron permutaciones y conteo equivalente para N=1,4,8,20,100;
rechazo de N=0, negativos,2,3; mutación guiada contra evaluación exhaustiva
de todos los intercambios para una reina; y soluciones de 100 reinas con
semillas 0,1,2 en 34,57,67 generaciones (aprox. 1.9,3.0,3.5 s de cálculo).
La prueba GUI verifica un solo tablero de 10000 casillas y 100 reinas,
cambio de tamaño, secuencias conservadas, parada y ausencia de TXT.
También se ejecutó la interfaz completa de 100 reinas hasta un ganador válido.
Captura: referencia/vistas/reinas_100.png.


Interfaz PyQt6: validación acotada a 13 pruebas distintas del módulo reinas,
todas aprobadas (9.55 s). Se respetó el límite de 20 ejecuciones de pruebas
automatizadas: 18 en total, incluidas las comprobaciones previas y la prueba
inicial que detectaba la interfaz antigua. No se ejecutó la suite completa.
Se cubrieron pausa/reanudación, reinicio, tamaño inválido, detención al ganar,
un solo tablero, geometría cuadrada en ventanas altas y anchas, vista compacta
de 720×520 y el algoritmo manual con 100 reinas. La aplicación también se
abrió con el backend gráfico real y se inspeccionó visualmente.
La captura actual está en referencia/vistas/reinas_pyqt6.png.
