# Laboratorio de regresión simbólica — diseño propuesto

## Propósito y alcance
Aplicación educativa en español para un estudiante universitario con programación básica. Enseña regresión simbólica mediante programación genética desde fundamentos hasta un simulacro exigente. La especificación funcional es el encargo del usuario del 23 de octubre de 2026; este documento concreta arquitectura y criterios de aceptación sin reducir ese alcance.

## Enfoques
1. **Propuesta recomendada: curso completo y núcleo matemático compartido desde el inicio.** Ocho unidades, banco de preguntas, exámenes y progreso forman la primera entrega funcional; los laboratorios se integran progresivamente sobre funciones matemáticas probadas. Prioriza estudiar y preparar el examen.
2. **Laboratorio primero.** Permite experimentar antes con evolución, pero retrasa cobertura pedagógica y evaluaciones. No encaja tan bien con la prioridad indicada.
3. **Backend con cuentas.** Añade sincronización, pero requiere infraestructura y conexión innecesarias para el objetivo local. Se descarta.

La opción 1 es una propuesta del desarrollador pendiente de aprobación, no una decisión atribuida al usuario.

## Arquitectura
Proyecto Vite + React + TypeScript en este directorio, conservando grafica.py, list-buckets.py y entorno. CSS con la paleta solicitada, componentes accesibles, SVG para árboles y curvas, KaTeX con recursos locales para fórmulas. Sin dependencias de CDN ni API para el curso. npm install, npm run dev, npm run build y npm test serán los comandos públicos.

Separación: src/domain para árboles, métricas, evolución y corrección; src/content para lecciones y preguntas; src/components para visualizaciones reutilizables; src/features para curso, evaluaciones, laboratorio y progreso. Motor separado de React para pruebas deterministas. Trabajo evolutivo en un Web Worker para mantener la interfaz receptiva.

## Navegación e interfaz
Inicio con continuar estudio, ocho unidades y acceso a laboratorio, repaso, examen y progreso. Cada unidad contiene introducción, conceptos, visualización, ejemplo resuelto, práctica guiada, evaluación y resumen. Navegación libre para volver a estudiar. Una evaluación solo cuenta como superada con un resultado real de al menos 80%; umbral propuesto por el desarrollador. Se distinguen lectura, intento y dominio.

Tema oscuro: fondo #07130D, paneles #10241A y #193528, acentos #39FF88 y #00FF99, texto #E4FBEA y #8BAF99, advertencias #FFB84D, errores #FF5577. Diseño responsivo, foco visible, etiquetas de formulario y controles equivalentes al arrastre para teclado y móvil. Animaciones pausables y respeto a prefers-reduced-motion.

## Contenido por unidad
1. Heurísticas, exactitud, AG, PG, regresión simbólica, directo/inverso y DDM. Puntos (1,1), (2,4), (3,9), curva x² ocultable y candidatas. Aclarar que datos finitos no identifican una única función.
2. Estructura, aridad, genotipo/fenotipo, tamaño y altura en aristas. Árbol completo sqrt(2*x²+5*x-3), editor con arrastre y selección alternativa; validación estructural y distinción de validez de dominio. Nmax=2^(h+1)-1 es cota para árboles binarios.
3. Preorder, inorder y postorder con animación y secuencias; evaluación paso a paso para x. Inorder sin paréntesis puede perder estructura. Postorder permite evaluar hijos antes que padre.
4. Biblioteca +,-,*,/,%,potencia,sqrt,log,sin,cos,tan, aridades y dominios reales. Generación aleatoria con altura máxima, hojas forzadas en límite y mediciones separadas.
5. Tabla editable x,y,ŷ,y-ŷ,(y-ŷ)²,y²,y-ȳ,(y-ȳ)². MSE=SSE/n, NMSE=SSE/Σy², R²=1-SSE/SST. Denominadores nulos dan resultado no definido explícito. Ejercicios de celdas faltantes, R² negativo y valores mayores que uno.
6. Población de funciones, evaluación, torneo binario, ruleta w=1/(1+MSE) y SUS. Distinguir error minimizado de peso de selección maximizado. Ruleta SVG y probabilidades normalizadas; SUS usa un desplazamiento aleatorio y punteros equiespaciados.
7. Cruce por aristas elegidas manual o aleatoriamente; padres, cortes y dos hijos visibles. Mutaciones terminal, operador, switching y regeneración. Sustitución de operador por defecto conserva aridad; cambio explícito binario→unario conserva un hijo elegido y elimina el otro, unario→binario genera el faltante. Pm decide si mutar antes de seleccionar tipo con pesos configurables. Reparación por poda al límite y alternativa de rechazo con intentos acotados y retorno al padre válido.
8. Ocho individuos y ciclo por operaciones: generar, evaluar, seleccionar, cruzar, mutar, reparar, élites, reemplazar y parar. Controles avanzar operación/generación, reproducir, pausar y reiniciar. Gráfica de mejor MSE y promedio. Élites se copian a siguiente población; archivo histórico no sustituye elitismo.

Cada unidad tendrá preguntas de comprensión dentro de la explicación, ejemplos calculados y al menos diez ejercicios originales con soluciones justificadas.

## Modelo matemático
Árbol inmutable con terminal variable/constante y operador de aridad conocida. Caminos de índices identifican subárboles. Cruce y mutación no modifican padres. Validación comprueba aridad, constantes finitas y altura. Evaluación devuelve valor o error de dominio; nunca eval ni ejecución de texto arbitrario. La potencia rechaza resultados no reales o no finitos; división y módulo rechazan divisor cero; log requiere positivo; sqrt requiere no negativo. Tangente rechaza polos mediante tolerancia documentada. Operaciones protegidas, si se añaden, serán otra semántica expresamente rotulada.

Individuos con evaluación no finita reciben error infinito y peso cero. Si todos son inválidos, selección regenera candidatos en lugar de dividir entre cero. Población y métricas usan solo filas válidas, con errores de importación visibles; no se descartan filas silenciosamente.

## Evaluaciones y recuperación
Banco inicial de al menos 80 ejercicios originales, diez por unidad, con variantes numéricas verificadas. Cada unidad selecciona entre 5 y 10 preguntas y evita repetir el conjunto del intento inmediatamente anterior. Formatos: selección única, verdadero/falso con justificación elegida, entrada numérica con tolerancia, ordenamiento, interpretación de árbol y código Python mostrado como texto.

Cada pregunta declara tema, dificultad, solución y explicación de distractores. Los cálculos tienen derivación reproducible. No se califica razonamiento libre con coincidencias de palabras. Cuando se requiere justificar, se usan opciones de razonamiento corregibles inequívocamente.

Simulacro de 30 preguntas, tiempo configurable, distribución propuesta por unidades: 2,3,5,2,5,4,5,4. Banco de variantes adicionales para que los temas con cinco preguntas también tengan rotación. No hay claves ni correcciones en pantalla durante el examen; entrega manual o automática al agotarse tiempo. Resultado por tema y corrección completa después. El temporizador usa fecha límite persistida; recargar no reinicia el reloj. En una aplicación cliente las claves no pueden ser secretas frente a inspección del código: es preparación, no evaluación supervisada.

Recuperación prioriza conceptos fallados y genera variantes; los errores se conservan históricamente y se distinguen de pendientes actuales. Nunca se fabrican calificaciones ni unidades completadas.

## Laboratorio CSV y evolución
Datos iniciales: 1000 puntos uniformes incluyendo extremos de [0,1], y=6.67+11*cos(7.23*x³). La fórmula solo genera el conjunto de referencia; el motor recibe exclusivamente pares x,y y configuración. CSV de dos columnas x,y con encabezado opcional, separador coma o punto y coma, comillas y validación de números finitos; se informan líneas incorrectas. Exportación del conjunto de referencia.

Búsqueda real simplificada con árboles aleatorios, torneo, cruce, mutación, poda y elitismo, constantes aleatorias y límites de población, altura y generaciones. Semilla configurable para reproducibilidad. No promete recuperar la expresión exacta. Curvas de datos/candidata y error generacional. Si alguna visualización usa una secuencia prefijada, llevará etiqueta de simulación y nunca se presentará como descubrimiento real. Submuestreo solo para dibujar; las métricas usan todas las filas aceptadas.

## Persistencia
LocalStorage versionado para progreso y sesión de examen. Guarda intentos con fecha, respuestas, versión de preguntas, resultados, unidades, errores por concepto y mejor nota. Validación al cargar y recuperación segura frente a JSON corrupto. Si no hay almacenamiento disponible, avisar y mantener sesión en memoria. Exportación/importación JSON validada y borrado con confirmación. No guardar resultados derivados de una clave de preguntas que haya cambiado sin su versión.

## Verificación y aceptación
Vitest: métricas conocidas y denominadores cero; tres recorridos; altura/tamaño/aridades; cruces sin mutar padres; cuatro mutaciones; reparación; selección y probabilidades; generación con semillas; calificación numérica, ordenamiento y distractores; persistencia y corrupción; CSV; independencia del motor respecto de fórmula objetivo.

Pruebas de interfaz: estudiar→intentar→entregar→corregir→recargar; recuperación; examen sin revelar respuestas antes de entrega; reloj persistente; carga CSV; controles de simulación. Comprobar escritorio y móvil, consola, navegación por teclado, compilación de producción y funcionamiento sin red después de servir el build local.

README en español con requisitos Debian/Node, instalación, ejecución, pruebas, arquitectura, convenciones matemáticas y limitaciones de búsqueda. No se modifica el script Python para ofrecer la interfaz.

## Etapas de entrega
A. Núcleo matemático probado, ocho unidades completas, banco, evaluaciones, simulacro y progreso.
B. Editores SVG, tablas y selección, cruces/mutaciones/reparación y ciclo animado.
C. CSV, evolución real simplificada, revisión pedagógica y pruebas de integración.

Las etapas organizan la implementación; no convierten B y C en botones pendientes dentro de una entrega presentada como completa.

## Revisión del diseño
Revisión independiente realizada: sin bloqueos matemáticos ni preguntas imprescindibles de alcance. Se fija un único núcleo matemático desde A. La importación CSV con filas inválidas bloquea la búsqueda hasta corregirlas o aceptar explícitamente el subconjunto válido. La recuperación se supera con 80% y no borra los intentos históricos. Los límites concretos y tolerancias se documentarán junto a sus pruebas durante implementación.
