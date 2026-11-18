# Reporte de equivalencias y modificaciones

Se inspeccionaron las **12 páginas completas** del PDF, incluidas ambas
mitades de cada escaneo y todas las continuaciones. El código se transcribió
antes de migrarlo. [original/LECTURA.md](original/LECTURA.md) ubica cada bloque;
[manifest.json](original/manifest.json) identifica el PDF y las imágenes.

## Equivalencias conservadas

| C++ | Python |
|---|---|
| struct TIndividuo | dataclass con los mismos campos; elite añadido solo donde falta |
| vector<bool>, vector<TIndividuo> | list de bool y list de individuos |
| Tvec_genes / Tvec_var / Tvec_int | listas de cromosomas / float32 / int |
| push_back y asignación de individuos | append y deepcopy por valor; sin compartir genes entre supervivientes |
| double | float de Python (IEEE-754 binary64 en el entorno verificado) |
| float y cast `(float)` | redondeo IEEE-754 binary32 explícito; sinf/sqrtf para sobrecargas float |
| referencias de salida | mutación de objetos/listas; tuplas para pos_mejor y sumaptitud; retorno para cmax |
| rand / RAND_MAX | enteros inclusivos con random estándar, umbrales y divisiones del libro |

Se conservan los nombres de las diez funciones base y `revisar_adap_mini`,
las tres funciones objetivo, la codificación **LSB primero**, la fórmula de
longitud, la ruleta con comparación `prob > punt_acu`, elite del 2 % con
truncamiento entero, el orden de parejas, el descarte del último seleccionado
impar, un punto compartido entre parejas, inversión de bits y el número fijo
de generaciones. En escalares se reevalúa dentro del bucle de genes tras la
primera mutación; en multivariable se reevalúa una vez por individuo.

## Correcciones y enlaces explícitos

| ID | Hallazgo del impreso | Tratamiento en la versión ejecutable |
|---|---|---|
| R1 | pp. 302/311: fórmula del punto produce 1..lcrom+1; cruce indexa fuera de genes | Mantener fórmula/azar; solo lcrom+1 pasa a lcrom. Opción estricta para detenerse. Cambia la masa del punto final; no existe comportamiento C++ definido que reproducir en ese caso. |
| R2 | pp. 300/309: ruleta indexa antes de comprobar pos_super < tam_pob | Comprobar límite primero y ejecutar el fallback pos_super-1 ya impreso. |
| R3 | Campos escalares de individuos/hijos y pos_mejor sin inicialización | Valores iniciales 0 y elite=False; pos_mejor inicial 0. No se simula memoria basura. |
| R4 | pp. 304/313: división por suma cero; int pot puede desbordar | Suma nula/no finita detiene con explicación; CLI acepta 1..30 bits en modelo int32. No se cambia la selección. |
| R5 | pp. 305–307: cmax no declarado en main; falta prototipo; `cmax;` no declara nada; se compara aptitud pero se asigna aptitud_bruta | Declarar/inicializar cmax y usar aptitud_bruta para encontrar el máximo bruto. Omitir expresión sin efecto. Conservar `cmax+cmax/100`. |
| R6 | p. 311: hijos solo reciben aptitud_bruta en cruce, pero reproducción consulta aptitud sin inicializar | Comparar aptitud_bruta del hijo contra la adaptación bruta del progenitor; conservar `<` y `or !elite`. |
| R7 | p. 313: struct multivariable omite elite; p. 316 lo usa | Añadir elite=False para enlazar selección y mutación del libro. |
| R8 | p. 314: genera_indiv recibe Tvac_int, tipo que no está declarado | Interpretar Tvec_int definido en p. 313. La transcripción conserva Tvac_int; la ampliación está en original/detalles/. |
| E1 | Multivariable publica solo tipos y cuatro funciones | Añadir main, NUM_VAR derivado de límites y firmas vectoriales de población/reproducción/transformación. Heredar selección/evaluación/decodificación; sortear un punto por variable una vez por reproducción. El CLI vectorial y estos enlaces no son líneas recuperadas del PDF. |

`<vector.h>` se moderniza a `<vector>` solo en la referencia de pruebas.
El PDF omite includes de E/S/tiempo usados por main; Python importa sus módulos
correspondientes. La referencia usa un driver añadido en vez de ejecutar ese
main incompleto. La inicialización explícita evita comportamiento indefinido.
Las reparaciones elegidas no son las únicas posibles; se preserva íntegra la
transcripción para revisar o adoptar otra decisión.

El libro no especifica biblioteca/compilador ni RAND_MAX. Se eligió 32767
configurable. Los enteros de Python no desbordan: con RAND_MAX grande,
`rand()*(lcrom+1)` evita el overflow intermedio del C++ int32; la referencia
hace esa multiplicación en double. `--semilla` facilita repetir Python, pero
no reproduce automáticamente una secuencia histórica de rand.

La precisión de multivariable se coteja con **C++17 y las sobrecargas float**
de math.h en el sistema actual. No se puede establecer qué sobrecargas tenía
el compilador histórico que aceptaba vector.h. Esta elección está identificada;
las funciones matemáticas no cambian. sinf puede diferir del double redondeado
en un ulp; por eso se usa ctypes para llamar a la función float del sistema.

## Peculiaridades deliberadamente conservadas

- La lista de élite sobrescribe un slot sin desplazar los anteriores; puede
  perder el segundo mejor o repetir índices. No se sustituyó por un ordenamiento.
- En maximización la reproducción impresa usa **`hijo.aptitud < adaptación`**;
  puede sustituir un élite por un hijo peor. Se mantuvo y se probó expresamente.
- La transformación `cmax+cmax/100` puede ser negativa si el peor bruto es
  negativo; entonces algunos pesos de ruleta son negativos y el acumulado
  puede dejar de ser monótono. No se cambió por abs(cmax) ni por otro escalado.
- Mejor aptitud y acumuladores son float32, aunque aptitud y puntuación sean
  double. Las comparaciones y acumulaciones conservan esos redondeos.

Estos programas reproducen el método del libro y sus defectos definidos;
no se promete elitismo correcto, pesos siempre válidos o convergencia general.

## Partes no recuperables y verificación

No quedó una instrucción del apéndice B ilegible. Faltan por omisión del
propio documento el main/enlaces multivariable y el valor de NUM_VAR.
En PDF 1/p. 294 solo hay asignaciones, un bucle y cierres del apéndice anterior:
se conservan y traducen como fragmento, pero falta su contexto para ejecutarlo.
La bibliografía de PDF 12 no contiene código.

La comparación diferencial pasa para tres semillas, tres variantes y todas
las fases de tres generaciones (50 individuos): cromosomas/elite/índices y
consumo de azar exactos; campos numéricos con tolerancia absoluta 1e-11.
Compara C++ **con las reparaciones declaradas**, no el original indefinido.
Resultados detallados: [VALIDACION.md](VALIDACION.md).


## Añadidos posteriores solicitados

`grafica.py` ejecuta maximización y dibuja la función con numpy/matplotlib,
marcando el individuo encontrado en esa ejecución con un punto rojo. Los tres main
guardan un TXT de sus parámetros y resultado mediante guardar_resultado;
la gráfica guarda las parejas x/f(x). Estos añadidos de visualización y
salida no provienen del PDF ni cambian las operaciones genéticas.


## Panel y semilla automática (14 de octubre)

Se añadieron observadores del cruce y de la inversión de bits. Capturan un
primer ejemplo de cada operación por generación, etiquetado con su generación,
sin participar en las decisiones ni consumir azar genético. El panel ANSI
solo se activa en una terminal y se refresca como máximo a 10 Hz, sin dormir.
Una comparación con/sin panel confirma poblaciones completas idénticas para
la misma semilla en las tres variantes. El script de gráfica usa el mismo panel.
A petición del usuario, la semilla predeterminada pasa del tiempo en segundos
a un entero automático de 64 bits generado por secrets; se registra en el TXT.
La opción de semilla explícita se conserva para comprobaciones reproducibles.


## Ejecución sin parámetros (14 de octubre)

Los siete argumentos posicionales ahora son opcionales a petición del usuario.
Se usa el ejemplo del libro para maximización (0,32,0.0001,500,1000,0.4,0.001),
los intervalos publicados para minimización (-250,250) y dos variables [0,100]
para multivariable, conservando los demás valores. Son defaults añadidos, no
supuestos sobre el main original. Parámetros explícitos siguen teniendo prioridad;
la semilla automática también se genera cuando no se proporciona ningún argumento.


## Visualización en vivo (14 de octubre)

main de maximización admite un observador opcional, llamado después de la
inicialización y tras cada fase genética. No interviene en las decisiones,
no consume rand y no modifica individuos. grafica.py usa ese observador para
actualizar población, mejor punto, cromosoma y progreso según tiempo real.
Registra todas las fases y limita únicamente los redibujos a 20 Hz; no añade
sleeps. No se afirma animar cada bit individual ni cambiar el criterio de parada.
Una ejecución con/sin observador produjo poblaciones y resultados idénticos.


## Minimización gráfica y refresco (14 de octubre)

El observador opcional también se añadió a minimizacion.main sin alterar
operadores ni aptitudes. grafica.py -mini utiliza aptitud_bruta y la
función -abs(x*sin(sqrt(abs(x)))) en [-250,250]. Se eliminó el gráfico temporal
en ambos modos a petición del usuario; solo queda función/población/mejor punto.
El historial temporal continúa guardándose en TXT. La preparación de artistas
se omite entre refrescos, además de limitar el redibujado; no se añaden sleeps.


## Gráfica construida desde datos observados

Se retiraron linspace y la evaluación vectorial precalculada de la función en
la gráfica. Solo se agregan pares x/aptitud reales de las poblaciones recibidas
tras cada fase (aptitud_bruta en minimización), deduplicados por x. Se muestran
como puntos, sin interpolar una curva inventada. La población actual y su mejor
individuo se resaltan sobre las muestras acumuladas. El archivo de gráfica
contiene esos pares observados, no una malla fija. No modifica la evaluación
matemática del algoritmo ni pretende capturar evaluaciones internas transitorias.


## Revisión de visualización con subagentes e investigación

Se separó la captura de todas las adaptaciones del refresco de pantalla.
Observadores de evaluación opcionales reciben x/f calculados por el original,
incluidos hijos descartados; el contextmanager se restaura ante errores.
La figura usa blit cuando el canvas GUI lo soporta, con fondo renovado en
resize/redraw/cambio de límites y alternativa de redibujado normal. Se desactivó
el redibujado automático por cada setter. El intervalo se mide desde el final
y aumenta según el coste. No cambia genes, ruleta, reproducción, mutación,
aptitudes ni consumo de azar. El límite de pantalla conserva solo coordenadas
reales; la exportación mantiene todos los pares únicos con 17 cifras.
Estudio completo con documentación primaria, mediciones y límites en
ANALISIS_GRAFICA.md. Esta revisión sustituye el alcance anterior de muestras
observadas únicamente en poblaciones de fin de fase.
