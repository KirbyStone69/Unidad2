# Migración del apéndice B de a.pdf a Python

Tres programas separados, con operaciones genéticas implementadas manualmente:
[maximizacion.py](maximizacion.py), [minimizacion.py](minimizacion.py) y
[multivariable.py](multivariable.py). Mantén junto a ellos
[compatibilidad.py](compatibilidad.py). No se necesita instalar paquetes.

**Lee [REPORTE.md](REPORTE.md): el C++ impreso contiene errores y la variante
multivariable está incompleta.** Las reparaciones y los enlaces añadidos
están marcados en el código. La [transcripción original](original/LECTURA.md)
conserva esos errores, junto con las imágenes y el OCR de las 12 páginas.

## Ejecución

Python **3.9 o posterior**. Desde este directorio:

```bash
# Invocación del ejemplo del libro; semilla generada automáticamente.
python3 maximizacion.py 0.0 32.0 0.0001 500 1000 0.4 0.001

# Intervalo y función de minimización del libro; los demás valores se eligen aquí.
python3 minimizacion.py -250 250 0.0001 500 1000 0.4 0.001

# Dos variables de la función multivariable del libro.
# Esta interfaz no se publica en el PDF: es el enlace E1 documentado.
python3 multivariable.py 0,0 100,100 0.0001 500 1000 0.4 0.001
```

Los siete argumentos son opcionales y conservan el orden del programa escalar:

| Posición | Parámetro | Significado |
|---|---|---|
| 1 | x_min | Límite inferior |
| 2 | x_max | Límite superior |
| 3 | TOL | Resolución para calcular la longitud binaria |
| 4 | tam_pob | Número de individuos |
| 5 | num_gen | Número fijo de generaciones; puede ser cero |
| 6 | prob_cruce | Probabilidad de seleccionar cada individuo para cruzar |
| 7 | prob_mut | Probabilidad de mutar cada bit |

Multivariable recibe límites separados por comas, sin espacios, y obtiene
`NUM_VAR` de su longitud. TOL puede ser un valor común o una lista de igual
longitud: `0.001,0.0001`. No se concatenan cromosomas: hay una lista de bits
por variable y un punto de cruce por lista. Si se escriben listas con valores
negativos al comienzo, usa `--` para separar opciones de parámetros.

Las funciones objetivo permanecen fijadas al texto del libro:

- Maximización: `20+exp(1)-20*exp(-0.2*abs(x))-exp(cos(2*pi*x))`.
- Minimización: `-abs(x*sin(sqrt(abs(x))))`.
- Multivariable (minimización): `sum(-x_i*sin(sqrt(abs(x_i))))`.

`TOL` no causa una terminación temprana: el bucle ejecuta `num_gen`
generaciones. La salida conserva la aptitud y el fenotipo; en minimización
se muestra `aptitud_bruta`, no la aptitud transformada. Se usan seis cifras
significativas como el `cout` predeterminado de C++.

## Azar y errores del impreso

- La semilla se genera automáticamente con `secrets.randbits(64)` y queda
  visible en el panel y en el TXT. Esto evita repetirla al ejecutar dos veces
  en el mismo segundo. `--semilla N` sigue disponible para repetir una ejecución
  concreta; no implica la misma secuencia que un `rand` de C.
- `--rand-max N`: máximo del entero aleatorio, inclusivo; por defecto 32767.
  El libro no identifica plataforma ni RAND_MAX. Se permite hasta 2147483647.
- `--cruce-estricto`: detiene la ejecución cuando la fórmula del libro genera
  `lcrom+1`. Sin esta opción, ese valor se lleva al extremo `lcrom` (R1),
  se conserva el consumo de azar y se informa cuántas veces ocurrió por stderr.

Los límites deben ser finitos y crecientes, TOL positiva, población positiva,
generaciones no negativas y probabilidades en [0,1]. Longitudes superiores
a 30 bits se rechazan porque el `int pot` del original desbordaría en el
modelo de enteros de 32 bits. Una suma nula de aptitudes se informa como error;
no se inventa una ruleta uniforme.

La transformación mínima del libro puede generar pesos negativos. Se conserva
su expresión exacta: no se introduce escalado alternativo, valor absoluto ni
una selección distinta. Véase el reporte para sus limitaciones.

El multivariable conserva operaciones `float` de C++17, incluyendo `sinf` y
`sqrtf` de la biblioteca matemática del sistema llamadas por `ctypes`
(biblioteca estándar). En Linux están normalmente disponibles en el proceso;
se busca también libm o el runtime C de Windows. Si no están disponibles,
se informa el error; no se sustituye silenciosamente su precisión.

## Pruebas y comparación con C++

Desde la raíz del proyecto:

```bash
python3 -m unittest discover -s migracion_ag/tests -v
```

Desde este directorio:

```bash
python3 -m unittest discover -s tests -v
```

Las pruebas de operaciones y ejecución no requieren compilador. Las tres
pruebas diferenciales requieren `g++` con C++17; si falta, unittest las marca
como omitidas. Compilan en un directorio temporal y comparan cada individuo
tras inicialización, selección, reproducción, mutación y evaluación.
Se suministran exactamente los mismos enteros aleatorios a los dos lenguajes.

La referencia C++ se genera **desde las transcripciones**, aplicando las
mismas reparaciones R1–R8 y enlaces E1. No se afirma equivalencia con lecturas
indefinidas de memoria del código impreso. Para inspeccionar esa referencia:

```bash
python3 referencia/preparar_referencia.py
```

Los archivos aparecerán en `referencia/generada/`; nunca se modifica
`original/`. [VALIDACION.md](VALIDACION.md) registra alcance y resultados.

## Archivos

- Los tres `.py` repiten las funciones equivalentes del libro para mantener
  cada programa separado y fácil de cotejar. No hay una clase nueva de algoritmo.
- `compatibilidad.py`: tipos numéricos, azar, argumentos y guardas documentadas;
  no implementa selección, reproducción, cruce ni mutación.
- `original/`: transcripción C++, imágenes, OCR bruto, mapa de lectura y hashes.
- `tests/`: operaciones, límites, ejecución y comparación diferencial.
- `referencia/`: generador reproducible de C++ y registros de ejecución.
- `REPORTE.md`: equivalencias, correcciones y partes no recuperables.

## Gráfica en vivo

```bash
python grafica.py -maxi
python grafica.py -mini
```

La ventana empieza vacía y se construye con las evaluaciones reales:

- Azul: coordenadas evaluadas acumuladas, sin repetir x.
- Gris: población actual.
- Rojo: mejor individuo actual; puede retroceder si el algoritmo pierde una solución.

En minimización se muestra `aptitud_bruta = f(x)`, no el peso transformado
usado por la ruleta. Hay una sola gráfica y no se interpola una curva.
Generación, fase, semilla y cromosoma aparecen como texto. Se aceptan los
mismos parámetros opcionales que el algoritmo. Por ejemplo:

```bash
python grafica.py -mini -250 250 0.0001 50 30 0.4 0.001
```

El script gráfico requiere numpy/matplotlib, ya presentes en `entorno`.
Los algoritmos sin gráfica usan la biblioteca estándar. Al terminar la ventana
permanece abierta. Si se cierra antes, el algoritmo sigue calculando y guarda
sus resultados sin preparar más dibujos.

El refresco reutiliza el fondo cuando el backend admite blitting y se ajusta
al costo del dibujo. No hay sleeps ni pausas artificiales. La pantalla muestra
hasta 10 000 coordenadas reales de la nube acumulada; el TXT conserva todas.
El límite afecta solo la pantalla y el contador indica cuántos puntos se ven.

## Datos al ejecutar

Los algoritmos guardan sus parámetros, semilla real y mejor individuo final
en `datos_maximizacion.txt`, `datos_minimizacion.txt` o `datos_multivariable.txt`.
La gráfica añade `datos_grafica.txt` y `datos_evolucion.txt`; en minimización
se llaman `datos_grafica_minimizacion.txt` y `datos_evolucion_minimizacion.txt`.

El archivo de gráfica contiene todos los pares únicos x/f(x) realmente
calculados, incluidos hijos luego rechazados e intermedios de mutación.
No es una malla prefijada de 1000 puntos. El historial registra tiempo,
generación, fase y resultado actual. Los archivos se guardan en la carpeta
de ejecución y se reemplazan al ejecutar otra vez el mismo modo.

[COMO_EJECUTAR.txt](COMO_EJECUTAR.txt) contiene los comandos paso a paso.
[ANALISIS_GRAFICA.md](ANALISIS_GRAFICA.md) explica el diseño, las fuentes,
los benchmarks y las pruebas de GUI.

## Panel fijo de la terminal

Los tres algoritmos muestran un bloque fijo con semilla, generación,
mejor resultado y ejemplos reales de cruce y mutación. El corte se marca
con `|`; la mutación muestra antes/después. No se introducen esperas ni se
imprime una línea por operación. El panel final permanece visible.
Con salida redirigida a archivo se imprime solamente el resumen, sin ANSI.

## Ejecutar sin parámetros

```bash
python maximizacion.py
python minimizacion.py
python multivariable.py
```

Usan semilla automática, 500 individuos, 1000 generaciones, TOL=0.0001,
cruce=0.4 y mutación=0.001. Intervalos: [0,32], [-250,250] y dos variables
[0,100]. Estos defaults son una comodidad solicitada posteriormente;
el main impreso del libro exigía los siete parámetros.


## N reinas: interfaz PyQt6

Con tu entorno activado:

```bash
python -m pip install -r requirements-reinas.txt
python reinas.py
```

La ventana abre con 100 × 100 y 100 reinas. Cambia N y pulsa
`Iniciar / reiniciar` para otro tamaño: 1 o cualquier entero desde 4.
Los tamaños 2 y 3 no tienen solución. `Pausar` / `Continuar` permite examinar
una generación sin perder la población.

Arriba quedan las cuatro secuencias, con colores y una barra horizontal
compartida. Naranja/azul indica origen, verde marca genes mutados y subrayado
marca el segmento OX. Debajo hay un único tablero cuadrado: se centra y se
ajusta automáticamente a la ventana, sin zoom manual ni desplazamiento.
En ventanas bajas, la cabecera y las estadísticas se compactan para dar más
espacio al tablero. A tamaño pequeño cada punto representa una reina;
cuando las casillas tienen espacio se dibujan coronas. Rojo significa ataque;
verde significa reina sin ataques. Pasa el ratón para consultar fila y columna.

Muestra el mejor tablero actual y **se detiene al encontrar cero conflictos**,
dejando visible la solución. No guarda ni carga resultados en TXT.
Solo `Iniciar / reiniciar` inicia una población nueva.

La interfaz utiliza PyQt6; el algoritmo sigue siendo manual: población de 64,
torneo de 3, OX, dos élites en memoria y mutación de probabilidad 0.5 por hijo.
La opción `Mutación guiada` se aplica al iniciar; busca el mejor intercambio
para una reina atacada. Al desactivarla se usa el intercambio aleatorio.
Las dos élites y sus conflictos se muestran en las estadísticas.

Con N=8 se conserva la cadena [8,3,7,4,2,5,1,6] de `2.png` como primer
individuo, con la orientación de `1.png`. Para otros tamaños las cadenas
iniciales son permutaciones aleatorias de 1 a N. La búsqueda es una demo
añadida, independiente de los algoritmos de a.pdf.

Referencia de la interfaz: [pintado y redimensionado de QWidget](https://doc.qt.io/qt-6/qwidget.html).
Captura: `referencia/vistas/reinas_pyqt6.png`.


## Ubicación actual de N-reinas

La práctica gráfica, sus dependencias y pruebas se trasladaron a [02_N_reinas](../../02_N_reinas/). Los comandos antiguos que mencionan `reinas.py` deben ejecutarse desde esa carpeta.
