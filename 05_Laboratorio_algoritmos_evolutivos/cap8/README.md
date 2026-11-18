# Hyperparameter / Genetic Lab

CLI educativa en español para optimizar **AdaBoost sobre Wine** con tres estrategias
basadas en el capítulo 8 de *Hands-On Genetic Algorithms with Python*.
Python **3.13**, Rich, DEAP y scikit-learn moderno. El diseño del laboratorio anterior
se adapta a terminal: paneles verde bosque, acentos neón, texto claro y avisos ámbar.
Las gráficas destacan la mejor accuracy observada en rojo oscuro.

## Instalar y ejecutar

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

El entorno `.venv` de esta carpeta ya está instalado. También puedes ejecutar:

```bash
.venv/bin/python main.py
.venv/bin/python -m tuning --help
```

`requirements.txt` fija las dependencias principales verificadas;
`requirements.lock.txt` registra además las dependencias transitivas del entorno.
No se descarga Wine de la red: se utiliza `sklearn.datasets.load_wine()`.

## Menú y comandos

El menú tiene las ocho opciones solicitadas: información de Wine, grid exhaustivo,
grid genético, AG directo, comparación, estadísticas, exportación y salida.
Los argumentos configuran también las ejecuciones iniciadas desde el menú.

```bash
# Comparación completa: cuadrícula compatible con el libro (100 combinaciones)
python main.py --method compare --population 20 --generations 5 \
  --mutation 0.3 --crossover 0.8 --seed 42 --output results --plots

# Prueba más corta con una cuadrícula de nueve combinaciones
python main.py --method compare --grid examples/grid-small.json \
  --population 8 --generations 2 --folds 3 --output results/short --plots

python main.py --method grid --grid examples/grid-small.json
python main.py --method genetic-grid --elite 2 --generations 10
python main.py --method genetic-direct --bounds examples/bounds.json
python main.py --method info

# Leer resultados existentes sin volver a entrenar
python main.py --method stats --input results/results.json --plots --output results/review
python main.py --input results/results.json --plots

# Menú con configuración personalizada
python main.py --population 30 --generations 8 --mutation 0.001 --plots
```

`--output` es un **directorio**. En ejecuciones sin menú, se exporta al finalizar;
en el menú, la opción 7 permite elegir dónde guardar. Se usan nombres de archivo
fijos: una nueva exportación al mismo directorio reemplaza esos archivos.
`--quiet` omite las líneas de cada evaluación/generación, conservando el resumen.
Las barras de progreso aparecen en terminales interactivas; se desactivan al
redirigir la salida. `Ctrl-C` cancela con código 130, sin presentar una ejecución
incompleta como terminada. Errores de configuración devuelven código 2.

## Datos y función de aptitud

Wine contiene **178 observaciones**, **13 características químicas** y **3 clases**
(59, 71 y 48 muestras). La carga local usa etiquetas 0, 1 y 2, a diferencia de la
codificación 1, 2, 3 mencionada en el libro.

- **Hiperparámetros**: se fijan antes de entrenar, aquí `n_estimators` y `learning_rate`.
- **Parámetros aprendidos**: por ejemplo, divisiones de los árboles débiles,
estimadores ajustados y pesos del ensamble. AdaBoost los obtiene durante `fit()`.
- **Fitness**: media aritmética de `accuracy` en los folds; se maximiza.

Se usa `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` por defecto.
Cada fold entrena un modelo nuevo y evalúa observaciones que no utilizó para ese
entrenamiento. Se fija también `random_state` del clasificador. Todos los métodos
con igual semilla/folds comparten exactamente los mismos índices de partición;
el JSON registra un hash SHA256 para comprobarlo. `--folds` admite de 2 a 48,
limitado por la clase más pequeña.

**La CV se utiliza para seleccionar hiperparámetros**. La mejor media observada
puede ser optimista por esa selección: no es accuracy de un conjunto de prueba
independiente. Una estimación de generalización final requiere prueba reservada
o validación anidada; esta herramienta no afirma realizar ninguna de ellas.

## Las tres estrategias

| Método | Representación | Operadores | Alcance |
|---|---|---|---|
| `grid` | Todas las combinaciones de listas | `ParameterGrid` y evaluación CV explícita | Mejor score garantizado de la cuadrícula evaluada |
| `genetic-grid` | Dos índices enteros de esas listas | Cruce uniforme, mutación uniforme entera, torneo | Explora un subconjunto; no garantiza el mejor de la cuadrícula |
| `genetic-direct` | Dos genes reales dentro de límites | SBX acotado, mutación polinómica acotada, torneo | Puede proponer valores fuera de las listas; no garantiza óptimo global |

La cuadrícula por defecto usa `n_estimators=10,20,...,100` y diez valores de
`np.logspace(-2,0,10)` para `learning_rate`: **100 combinaciones y 500 fits CV**
con cinco folds, además de la evaluación de referencia. La exhaustividad cuesta
el producto de las cardinalidades: añadir ejes o valores multiplica los modelos
que hay que entrenar.

El AG directo utiliza `[1,100]` y `[0.01,1.0]`. Un cromosoma `[69.4,0.628]` se
convierte en `n_estimators=69, learning_rate=0.628`. Solo el primer gen se redondea
con `round()` de Python (empates al entero par); el segundo se conserva. No se
truncan silenciosamente genes fuera de rango: se rechazan. Los operadores de DEAP
reciben los límites de cada eje.

### Ciclo evolutivo

1. Crear la población aleatoria y evaluar la generación 0.
2. Clonar los mejores `--elite` individuos, conservándolos sin variación.
3. Seleccionar el resto mediante `selTournament` (`--tournament`, por defecto 2).
4. Aplicar cruce con probabilidad `--crossover` por pareja.
5. Aplicar mutación con probabilidad `--mutation` por individuo; dentro de ella,
cada gen tiene probabilidad `1/2` de mutar.
6. Evaluar los individuos con fitness invalidado; conservar fitness válidos.
7. Registrar estadísticas y repetir hasta `--generations`.

En directo se usan `cxSimulatedBinaryBounded` y `mutPolynomialBounded` con `eta=20`
(configurable con `--eta`). El hall of fame guarda el mejor observado. Si todas
las plazas son élites, se avisa: no habrá variación. Cero generaciones evalúa
únicamente la población inicial. No hay una parada temprana oculta por accuracy.

Las estadísticas incluyen generación, población, individuos evaluados, **CV nuevas**,
mejor, promedio, peor y desviación estándar de la población. “Evaluados” cuenta
solicitudes de fitness; “CV nuevas” cuenta configuraciones distintas realmente
entrenadas. Una caché por ejecución evita recalcular cromosomas que representan
los mismos hiperparámetros. Cada método tiene caché independiente: ejecutar grid
primero no regala evaluaciones al AG. Se conserva el estado global de `random`
al salir de cada búsqueda.

## Definir cuadrículas y rangos

`--grid archivo.json` acepta únicamente las dos claves siguientes:

```json
{"n_estimators": [10, 30, 50], "learning_rate": [0.01, 0.1, 1.0]}
```

Los valores repetidos se deduplican; se rechazan listas vacías, estimadores no
enteros, NaN, infinitos, tasas no positivas y ejes desconocidos.
`--bounds archivo.json` define los rangos del AG directo:

```json
{"n_estimators": [1, 100], "learning_rate": [0.01, 1.0]}
```

Los extremos deben ser finitos y mínimo < máximo; los de `n_estimators` deben ser
enteros positivos. El rango de learning_rate es positivo. Cambiar la cuadrícula
no cambia automáticamente el rango directo: son espacios diferentes, declarados
en cada resultado.

## Resultados y visualizaciones

- `results.json`: esquema versionado, configuración completa, espacio, semilla,
versiones, CV y hash, baseline, ganador, evaluaciones por fold e historial.
- `summary.csv`: método, mejor accuracy, hiperparámetros, tiempo, solicitudes,
CV únicas, número de fits y referencia.
- `evaluations.csv`: una fila por configuración distinta entrenada, con scores de
cada fold serializados como lista JSON.
- `history.csv`: estadísticas de la población de cada generación. Una ejecución
solo exhaustiva produce este CSV con encabezados y sin filas.
- `evolution.png` (`--plots`): mejor accuracy y promedio por generación; para grid
exhaustivo muestra scores por configuración y mejor acumulado, sin inventar generaciones.
- `comparison.png` (`--plots`): accuracy observada, tiempo y mejores hiperparámetros.

Los resultados importados se validan: ganador dentro del espacio, score consistente
con sus folds y las evaluaciones, historial y contadores completos, hash de CV y
esquema soportado. Esta validación detecta inconsistencias; no certifica la
procedencia de archivos ajenos. No se utiliza pickle ni `eval()`.

El tiempo de búsqueda incluye evaluación, evolución y mensajes de la ejecución;
excluye el baseline, la exportación y el dibujo PNG. El baseline utiliza los
valores por defecto actuales (50 estimadores, learning_rate=1.0), con sus propios
folds y caché; sus scores y tiempo se guardan aparte. Las diferencias temporales
pequeñas dependen del equipo y del volumen de salida.

**Comparar no implica presupuestos iguales**: grid agota su espacio; los AG usan
población/generaciones. Pueden encontrar algo peor, igual o mejor (en directo,
por ampliar los valores disponibles). No hay garantía de que sean más rápidos.
Con varias semillas se puede estudiar la variabilidad; una sola ejecución no
prueba superioridad estadística.

## Qué cambió respecto al PDF

Referencia principal: PDF local de 16 páginas, capítulo 8, páginas impresas 207–222.

| PDF | Implementación actual |
|---|---|
| `algorithm` con `SAMME` y `SAMME.R` | SAMME fijo; no se pasa `algorithm` |
| Grid 10 × 10 × 2 = 200 | Grid 10 × 10 = 100 |
| Tres genes, uno categórico redondeado | Dos genes; no se añade un gen ficticio para una categoría constante |
| `sklearn-deap.EvolutionaryAlgorithmSearchCV` | DEAP directamente, con ciclo elitista visible y probado |
| `GridSearchCV` | `ParameterGrid` + `cross_val_score`, para mostrar cada configuración y su score |
| Validación K-Fold | Stratified K-Fold con mezcla y semilla explícitas |
| Resultados numéricos del libro | Se recalculan con API, algoritmo y particiones actuales; no se promete reproducirlos |

La firma instalada se inspeccionó **antes de programar**:

```text
scikit-learn 1.9.1
AdaBoostClassifier(estimator=None, *, n_estimators=50,
                   learning_rate=1.0, random_state=None)
```

`SAMME.R` fue deprecado en 1.4 y eliminado en 1.6;
[documentación oficial 1.5](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.AdaBoostClassifier.html).
`algorithm` fue deprecado en 1.6 con eliminación prevista en 1.8;
[documentación oficial 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.AdaBoostClassifier.html).
Estas son **adaptaciones modernas**, no afirmaciones literales del PDF. No se
fuerzan dependencias antiguas para recuperar SAMME.R. El código también evita
`base_estimator`, renombrado a `estimator` en versiones modernas.

## Pruebas y organización

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

Las pruebas ejecutan CV real de modelos pequeños, comparan fitness con scikit-learn,
comprueban límites después de cientos de cruces/mutaciones, elitismo,
reproducibilidad, caché, comparación de folds, JSON/CSV/PNG, menú y CLI mediante
subprocesos. Incluyen entradas inválidas y resultados manipulados/inconsistentes.

```text
tuning/spaces.py       Configuración, individuos, conversiones y operadores DEAP
tuning/evaluation.py   Wine, CV fija, fitness y caché
tuning/search.py       Exhaustivo, AG discreto y AG directo elitista
tuning/persistence.py  JSON versionado y CSV con Pandas
tuning/charts.py       PNG con Matplotlib/Agg, sin servidor gráfico
tuning/cli.py          Menú Rich, argumentos y mensajes educativos
tests/                Pruebas automatizadas
examples/             Cuadrícula y rangos editables
docs/                 Diseño, plan y ejecución de validación
```

Se puede usar el motor sin terminal:

```python
from tuning.search import run_search
from tuning.spaces import SearchConfig, DirectSpace
result = run_search("genetic-direct", SearchConfig(seed=42), DirectSpace())
print(result.best_params, result.best_accuracy)
```

Referencias: PDF local, documentación oficial de
[DEAP](https://deap.readthedocs.io/en/master/api/tools.html),
[AdaBoost](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.AdaBoostClassifier.html)
y [StratifiedKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html).

## Ejecución verificada

La comparación completa con las opciones por defecto se conserva en
[docs/VALIDATION.md](docs/VALIDATION.md), junto con resultados JSON/CSV,
gráficas y [vista de la terminal](docs/terminal-preview.svg).

Verificación final: **54 pruebas aprobadas** y `pip check` sin conflictos.
