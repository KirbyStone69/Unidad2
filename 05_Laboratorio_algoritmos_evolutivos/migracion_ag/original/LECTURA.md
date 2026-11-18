# Reconstrucción del documento

Las 12 páginas del PDF son imágenes de dobles páginas del libro. Se leyeron
ambas mitades de todas las imágenes, en orden izquierda → derecha. No había
capa de texto: `pdftotext` solo devolvió 12 separadores de página. Se guardan
imágenes, OCR bruto (que **no** es la transcripción) y SHA-256 en manifest.json.
El OCR se contrastó visualmente; no se ejecutó como código.

| PDF | Libro | Contenido revisado y destino |
|---|---|---|
| 1 | 294–295 | Final del apéndice anterior → fragmento_previo.cpp; portada y explicación del apéndice B |
| 2 | 296–297 | Parámetros/ejemplo; funciones.h completo (cruce continúa en mitad derecha); función máxima y comienzo de main |
| 3 | 298–299 | Continuación y fin de main; poblacion_inicial; genera_indiv; primera mitad de seleccion |
| 4 | 300–301 | Fin de seleccion; adaptacion continúa de izquierda a derecha; decod; bin_dec |
| 5 | 302–303 | reproduccion; cruce; mutacion completos |
| 6 | 304–305 | evaluacion; struct de minimización; función mínima; comienzo de main mínimo |
| 7 | 306–307 | Fin del main mínimo; revisar_adap_mini continúa de izquierda a derecha; poblacion_inicial y genera_indiv |
| 8 | 308–309 | seleccion continúa de izquierda a derecha; adaptacion mínima; firma de decod |
| 9 | 310–311 | Cuerpo de decod; bin_dec; reproduccion continúa de izquierda a derecha; cruce incompleto |
| 10 | 312–313 | Fin de cruce; mutacion; evaluacion continúa de izquierda a derecha; tipos y objetivo multivariable |
| 11 | 314–315 | genera_indiv multivariable; adaptacion continúa de izquierda a derecha; cruce multivariable |
| 12 | 316 y bibliografía | mutacion multivariable completa; bibliografía sin código |

## Transcripciones

- `funciones.h` y `maximizacion.cpp`: todas las instrucciones de la versión 1.
- `funciones_minimizacion.h`: cabecera heredada según el texto de la p. 304,
  con el único cambio de struct impreso. Sus prototipos no se completaron:
  falta el de revisar_adap_mini, tal como en el documento.
  Los dos .cpp conservan el include original "funciones.h"; la cabecera mínima
  se nombra aparte aquí para distinguirla de la versión máxima.
- `minimizacion.cpp`: versión 2 íntegra, sin corregir sus errores. Repite
  las funciones reimpresas y conserva cmax sin declarar, la expresión `cmax;`,
  la comparación con aptitud y las lecturas de aptitud de hijos no asignadas.
- `multivariable.h` y `multivariable_fragmentos.cpp`: exactamente los tipos
  y cuatro funciones publicados. No se añade main, NUM_VAR ni elite aquí.
- `fragmento_previo.cpp`: no se desecha el trozo del apéndice anterior.
  `fragmento_previo_python.txt` traduce solo sus instrucciones recuperables.

Se normalizó sangría, se unieron líneas partidas, se abreviaron los marcos
ornamentales de asteriscos y algunos comentarios explicativos redundantes.
Los comentarios de procedencia se añadieron. No se suprimió ninguna
instrucción ni variable del código visible. Los nombres son `lcrom` (ele,
no número uno), `hijo1`/`padre1` (uno), `punt_acu` y `aptitud_bruta`.
En la firma de genera_indiv de p. 314 se lee `Tvac_int`, una errata de
`Tvec_int` confirmado en la ampliación detalles/pagina11_tipo.png. Se conserva
la errata en la transcripción y se corrige como R8 en la referencia ejecutable.
La mancha sobre `gen` en p. 314 se resolvió con el identificador declarado y
su posterior push_back; no hay una instrucción algorítmica ilegible.

## Fórmulas y cifras impresas

- Máximo: `20 + exp(1) - 20*exp(-0.2*abs(x)) - exp(cos(2*pi*x))`,
  intervalo [0,32], máximo indicado 22.3136 en 31.5005.
- Mínimo escalar: `-abs(x*sin(sqrt(abs(x))))`, intervalo [-250,250],
  mínimo indicado -201.843 en 203.814. Por simetría también hay un mínimo
  en el negativo; no se cambió el objetivo por una Schwefel sin valor absoluto.
- Multivariable: suma de `-x_i*sin(sqrt(abs(x_i)))`, intervalos [0,100],
  valor indicado `-n*63.63498` en cada `x_i=65.54785`.

El ejemplo de invocación impreso es:
`funciones 0.0 32.0 0.0001 500 1000 0.4 0.001`.
No son valores predeterminados del main: sus siete parámetros son obligatorios.
El número fijo de generaciones es la única condición de terminación publicada;
TOL determina bits, no un criterio dinámico de convergencia.

## Lo que el PDF no contiene

El apéndice B presenta un programa base, una versión mínima y una extensión
parcial, no tres programas completos autónomos. En multivariable faltan
main, definición/valor de NUM_VAR, prototipos adaptados y enlaces para
poblacion_inicial, reproduccion y revisar_adap_mini. Se reconstruyen y
etiquetan E1 exclusivamente en las versiones ejecutables. No se pueden
atribuir esas líneas al libro. El inicio del código de la p. 294 está fuera
del PDF y no se puede convertir en un programa completo.
