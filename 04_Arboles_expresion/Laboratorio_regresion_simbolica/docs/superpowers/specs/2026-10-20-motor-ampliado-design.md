# Motor ampliado de regresión simbólica

## Intención y alcance
Mejorar la capacidad de descubrir expresiones, incluidas oscilaciones con argumento
no lineal y coeficientes reales, a partir exclusivamente de pares x/y. Conservar
PyQt6, QThread, CSV, controles y animaciones educativas. No introducir la fórmula
ni los coeficientes del usuario en el código del buscador. Sin garantías de éxito
universal ni de extrapolación a partir de un ajuste sobre datos finitos.

## Diseño elegido
Programación genética híbrida: evolución de estructuras + ajuste numérico local
acotado con scipy.optimize.least_squares. Frente a solo añadir operadores, permite
descubrir números reales; frente a sustituir el motor por una biblioteca opaca,
conserva árboles propios, operadores educativos y control de presupuestos.

- Registro explícito de primitivas y aridad. +, -, *, / protegida, sin, cos,
  square, cube, exp, log, sqrt, tanh y abs. Funciones seleccionables por familias.
- Árboles inmutables validados, constantes reales, pi/e, simplificación segura,
  evaluación vectorizada finita, límite de altura y de cantidad de nodos.
- Población mixta: árboles aleatorios, estructuras sencillas de la misma gramática
  (potencias, funciones de potencias y composiciones), constantes aleatorias y
  calibración afín. Inmigrantes estructurados introducidos con presupuesto por
  generación. Las estructuras no dependen del CSV y los números se ajustan usando
  exclusivamente entrenamiento. No se enumera una fórmula conocida del usuario.
- Torneo, elitismo, selección con penalización de complejidad, mutaciones de
  subárbol/operador/constante y poda. Diversidad por eliminación de duplicados,
  inmigración y aumento de exploración ante estancamiento. Archivo de mejor MSE
  de entrenamiento monotónico, independiente de la penalización de complejidad.
- Caché acotada de fitness. Optimización local de pocos candidatos por generación,
  acotada en evaluaciones y cooperativa con cancelación. No evaluar mediante eval.
- División determinista entrenamiento/validación configurable, desactivable para
  muestras pequeñas; validación no interviene en selección ni optimización.
  MSE/NMSE/R² de entrenamiento y NMSE de validación identificados en interfaz.
- Parada al alcanzar objetivo configurable, límite de generaciones o cancelación.
  Estados de convergencia/error/pausa separados del diagnóstico de calidad.
- Interfaz: familias de funciones, presupuesto de ajuste, tamaño máximo,
  validación, objetivo NMSE, complejidad/diversidad/estancamiento; números largos
  abreviados en nodos, representación y evaluación correctas para funciones unarias.

## Validación
Pruebas de primitivas/seguridad, aridades, constantes, simplificación, presupuestos,
herencia/cancelación, reproducibilidad y separación de validación. Pruebas de
regresión numéricas: polinomio, coseno con argumento cúbico, seno con fase,
exponencial y racional con parámetros distintos de los del usuario. Benchmark
reproducible sobre gr.csv y sobre datos no vistos; reportar tiempo, error y semilla.
Pruebas Qt offscreen de controles, funciones unarias, configuración y diagnóstico.
