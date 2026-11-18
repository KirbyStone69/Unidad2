# Laboratorio de programación genética
Aplicación de escritorio exclusivamente PyQt6 para regresión simbólica univariable.
Motor NumPy independiente con árboles inmutables, división protegida, torneo,
elitismo, cruce, mutación y reparación por altura. MSE, NMSE y R².
Trabajador QThread con condiciones de pausa y avance individual; señales con
instantáneas inmutables por generación. Sin animaciones durante búsqueda.
Paneles QSplitter: configuración/CSV, árbol QGraphicsView, Matplotlib y métricas.
Modo educativo con animación de creación, evaluación, cruce, mutación y reparación;
operadores sobre copias del mejor árbol, sin alterar la población evolucionada.
CSV numérico con encabezado y elección de columnas. Datos iniciales x²+x+1.
Validar valores finitos, tamaños y parámetros. Cancelar y esperar hilo al cerrar.
