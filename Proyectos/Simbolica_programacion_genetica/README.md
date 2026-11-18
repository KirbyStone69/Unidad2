# Simbólica · Laboratorio de programación genética

Aplicación educativa en español para estudiar regresión simbólica: ocho unidades con explicaciones, ejemplos resueltos, comprobaciones, ejercicios guiados y evaluaciones; simulacro universitario; repaso de errores; laboratorio evolutivo real sobre CSV.

## Ejecutar en Debian

Necesitas Node.js **20.19 o posterior** y npm. Comprueba `node --version` y `npm --version`. Si Debian ofrece una versión anterior, instala una versión LTS compatible desde el distribuidor oficial de Node.js o tu gestor de versiones habitual.

```bash
cd /home/kirby/aws_curso
npm install
npm run dev
```

Abre la dirección que imprime Vite, normalmente **http://localhost:5173**. El entorno Python no interviene. Se conservan `grafica.py`, `list-buckets.py` y `entorno/`.

```bash
npm test             # matemáticas, árboles, contenido, persistencia e integración React
npm run build        # comprobación TypeScript y producción en dist/
npm run preview      # sirve la compilación local
```

El curso y las fuentes matemáticas se sirven localmente: no requieren cuenta, CDN ni conexión a Internet después de instalar dependencias. Mantén el servidor local encendido. No es una PWA instalada ni un servicio en la nube.

Para pruebas de navegador opcionales:

```bash
npx playwright install chromium
# En una Debian mínima, si faltan bibliotecas de sistema:
# npx playwright install-deps chromium
npm run test:e2e
# Verificar también la compilación de producción:
npm run build
E2E_PRODUCTION=1 npm run test:e2e
```

## Cómo estudiar

1. **Vista general:** selecciona cualquiera de las ocho unidades o continúa donde estudiaste por última vez.
2. **Lección:** lee conceptos, ejemplos y abre las comprobaciones de comprensión. Registrar lectura no aprueba la unidad.
3. **Laboratorio:** modifica datos y árboles. Cada botón tiene una operación concreta; los editores ofrecen selección con clic/teclado además del arrastre.
4. **Práctica:** diez problemas guiados originales por unidad. La solución aparece después de comprobar.
5. **Evaluación:** siete preguntas por intento, sin solución durante el intento. Se necesita al menos 80% para marcar la unidad como superada.
6. **Examen final:** 30 preguntas avanzadas, tiempo de 30 a 120 minutos, entrega automática al terminar. Distribución por unidades: 2,3,5,2,5,4,5,4. Reloj y respuestas sobreviven a recargas; salir a otra sección no pausa el reloj.
7. **Recuperación:** selecciona hasta diez errores pendientes con otra variante. El último resultado de cada problema determina si sigue pendiente; los fallos históricos se conservan.
8. **Mi progreso:** resultados por unidad, notas, historial, errores recurrentes y exportación/importación de copias JSON. El borrado requiere confirmación.

Banco: **126 problemas originales** (80 de curso + 46 avanzados) y variantes numéricas. Los reintentos de unidad cambian el conjunto de originales, aunque pueden compartir algunas preguntas. No se generan claves aleatorias. Las preguntas numéricas usan tolerancia absoluta ±0.001, indicada en pantalla. Verdadero/falso incluye razones seleccionables; el razonamiento libre no se corrige mediante palabras clave.

## Laboratorios

- Problema inverso: coeficientes y estructuras candidatas; curva original ocultable y puntos observados.
- Árboles: editor SVG con operadores y terminales; altura, tamaño y estructura; edición por arrastre o seleccionando un nodo y una pieza.
- Recorridos: preorder, inorder y postorder animados, pausa, avance y evaluación postorder para x.
- Generación: grow/full con altura máxima entera y biblioteca de aridades.
- Métricas: tabla editable completa y ejercicio de celdas faltantes con variantes.
- Selección: errores editables, torneo, ruleta de probabilidades y SUS.
- Genética: cruce manual/aleatorio por aristas, cuatro mutaciones, pesos configurables y Pm; poda y rechazo/repetición acotados.
- Ciclo: ocho individuos, avance por operación o generación, reproducción, pausa, reinicio, élite y gráficas.

Las entradas de las actividades numéricas del curso se limitan a ±10 000 para mantener los cálculos legibles. El motor CSV acepta números finitos más generales, y comunica los errores de dominio o rango.

## Búsqueda evolutiva sobre CSV

El laboratorio independiente genera por defecto **1000** muestras uniformes, incluyendo extremos de [0,1], de `6.67 + 11*cos(7.23*x**3)`. Puedes descargar ese CSV o cargar otro. Se acepta encabezado `x,y` opcional, separador coma o punto y coma, campos entrecomillados y punto decimal. Límites: 5 MB y 50 000 muestras. Una fila inválida impide importar el archivo entero y conserva los datos anteriores; se informa su línea.

El buscador recibe **solo puntos y configuración**, nunca la fórmula generadora. Ejecuta PG real simplificada en un Web Worker: población aleatoria (8–64), torneo binario con reemplazo, cruce de ramas cuando ambos padres tienen aristas, Pm configurable, cuatro tipos de mutación equiprobables, poda al límite y una élite. Altura 1–5; presupuesto 1–200 generaciones. Las constantes iniciales son décimas entre −5 y 5. La mutación terminal puede alternar variable y constante. No hay optimizador local de constantes: la convergencia a funciones oscilatorias es limitada y **no se promete descubrir la ecuación de referencia**.

Puedes pausar, reanudar, avanzar una generación y reiniciar con otra semilla. Datos/configuración/implementación iguales y semilla igual permiten reproducir la búsqueda. Toda métrica usa todas las muestras; solo se submuestrea el dibujo. Se muestran error de entrenamiento y promedio de candidatos finitos; el número de inválidos se informa por separado. El laboratorio no hace partición automática entrenamiento/validación: no interpretes la curva como error de generalización.

## Convenciones matemáticas

- Raíz en profundidad cero; altura en **aristas**; tamaño en nodos. Máximo binario `2^(h+1)-1` es cota, no tamaño obligatorio.
- Terminales: x o constante finita. Aridades registradas: `+ - * / % ^` binarias; `sqrt log sin cos tan` unarias.
- Evaluación ordinaria sobre reales. División/módulo por cero, sqrt de negativo, log de no positivo, potencia no real y resultados no finitos invalidan el candidato. Para tan se rechaza `abs(cos(argumento)) < 1e-10` por cercanía numérica al polo. Los ángulos usan radianes y se adopta la convención computacional `0^0=1`. `%` usa resto de JavaScript (signo del dividendo); para entradas positivas coincide con módulo habitual. No se ofrece una semántica protegida encubierta.
- `MSE = SSE/n`; `NMSE = SSE/Σy²`; `R² = 1−SSE/SST`, donde `SST=Σ(y−ȳ)²` y la media usa **y reales**. No se usa otra normalización de NMSE.
- Denominadores cero → no definido. R² puede ser negativo; MSE/NMSE pueden superar 1. R²=1 no prueba identidad de ecuaciones ni generalización.
- Errores de dominio o desbordamiento de un árbol → error infinito y peso cero; si todos los individuos son inválidos, el motor regenera la población. La herramienta aislada de probabilidades usa distribución uniforme como fallback explícito para un total nulo.
- Cruces y mutaciones no cambian padres. El cruce por aristas excluye cortar por encima de la raíz. Mutación de operador automática conserva aridad; el ejercicio explícito binario→sin conserva el hijo izquierdo. Regenerar puede exceder altura antes de la reparación.
- Poda reemplaza operadores en el nivel límite por terminal x. Rechazo intenta hasta veinte propuestas; la alternativa de respaldo es un padre previamente ajustado al límite. Todo árbol modificado se reevalúa.
- Elitismo inserta copias en la población siguiente. Un archivo histórico solo registra mejores soluciones y no reemplaza elitismo.

## Estructura

```text
src/domain/       árboles, métricas, selección/evolución, CSV, calificación, almacenamiento
src/content/      ocho lecciones, 80 ejercicios de curso, 46 avanzados
src/components/   SVG de árboles, gráficas, KaTeX, práctica guiada
src/features/     curso, actividades, exámenes, progreso y laboratorio
src/evolution.worker.ts
src/App.tsx       navegación y coordinación del progreso
src/styles.css    tema oscuro responsivo y animaciones reducidas
 tests/           pruebas unitarias e integración React
 e2e/             pruebas de navegador
 docs/            diseño, plan y registro de decisiones/verificación
```

LocalStorage `simbolica-v1` guarda respuestas, versiones de preguntas, intentos y sesión activa. Una copia incompatible o corrupta no se carga; se muestra aviso y permite estudiar en memoria. Si el navegador impide guardar, exporta antes de cerrar. El laboratorio evolutivo es efímero: se reinicia al salir de su sección y no forma parte del progreso académico.

Las claves residen en el cliente y no son secretas frente a inspección del código. Este producto prepara exámenes; no pretende ser una plataforma de evaluación supervisada.
