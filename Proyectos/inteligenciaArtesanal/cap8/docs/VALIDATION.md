# Validación ejecutada

Python 3.13.5; dependencias exactas en requirements.lock.txt.

Comando real, no simulación:

```bash
.venv/bin/python main.py --method compare --plots --quiet --output docs/validation-run
```

Población20, generaciones5, mutación0.3, cruce0.8, élite1, seed42, folds5.
Grid por defecto100 combinaciones; directo n_estimators[1,100], learning_rate[.01,1].

| Método | Mejor accuracy CV | n_estimators | learning_rate | CV únicas | Tiempo búsqueda |
|---|---:|---:|---:|---:|---:|
| grid | 0.954920635 | 80 | 0.599484250319 | 100 | 41.830 s |
| genetic-grid | 0.954761905 | 70 | 0.599484250319 | 45 | 14.962 s |
| genetic-direct | 0.966031746 | 67 | 0.97338460634 | 75 | 33.678 s |

Los tres usan exactamente el mismo hash de particiones: `c00c8c96f1072b270d153aa31f8da7586e4842f3ef4c9428764b3ed74e8f5370`.
Baseline AdaBoost actual: 0.932539683 accuracy CV.
Los tiempos incluyen mensajes de búsqueda, excluyen baseline/exportación/PNG y
pueden variar según carga del sistema. Esta corrida coincidió parcialmente con
la suite de pruebas, por lo que no es un benchmark de rendimiento aislado.

Resultados observados de selección, sin test independiente. El grid genético
no alcanzó el máximo de la cuadrícula en esta corrida. El directo obtuvo mayor
accuracy con un espacio distinto; esto no demuestra superioridad general.

Se verificó recarga de los resultados sin reentrenamiento y se inspeccionaron
visualmente ambas gráficas PNG. La revisión independiente identificó problemas
de tema Rich, valores de entrada anidados, validación de ganadores importados y
títulos engañosos con folds distintos; se corrigieron con pruebas de regresión.

[Resumen CSV](validation-run/summary.csv) · [JSON completo](validation-run/results.json)

[Evolución](validation-run/evolution.png) · [Comparación](validation-run/comparison.png) · [Terminal](terminal-preview.svg)

## Verificación final

**54 pruebas aprobadas en 15.26 s**; `pip check`: sin dependencias rotas.
Incluye comparación contra GridSearchCV independiente, población singleton con
redondeo numérico, cero generaciones, elitismo completo, Ctrl-C sin exportación
incompleta y regresiones de todos los hallazgos de revisión.
