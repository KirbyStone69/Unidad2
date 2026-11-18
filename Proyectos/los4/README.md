# Visualizador de rutas · PyQt6

Aplicación de solo lectura con fondo gris oscuro, nodos `#397d5a` y aristas verdes. El mapa estándar de las cuatro interfaces es **grafo_final.jpeg**: **30 nodos, 63 aristas dirigidas**, coordenadas sobre 1600 × 977 píxeles y nodo **666**. Se conservan las flechas, los pesos y las dos aristas paralelas 12 → 16 (16 y 3). La imagen sirve para transcribir los datos; no se dibuja como fondo.

## Ejecutar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

La rueda controla el zoom, arrastrar desplaza y «Ajustar» muestra el grafo completo. Los campos de origen/destino aceptan números escritos y muestran una alerta específica cuando alguno no existe. Los grafos no se editan.

## Variantes y algoritmos

| Algoritmo | Variante inicial | Interfaz propia |
| --- | --- | --- |
| Dijkstra | Positiva | Configuración y matrices desplegables inferiores |
| Bellman–Ford | Original con negativos | Lista de arcos, vectores V/d/Π, relajación y pasos |
| A* | Positiva | Heurística, tabla g/h/f, abiertos/cerrados y pasos |
| Floyd–Warshall | Positiva | Matrices de distancias/recorridos y consulta de rutas |

Ambas variantes proceden de una **única transcripción**. La positiva aplica valor absoluto a los pesos; no cambia nodos, posiciones, sentidos ni claves. Son objetos independientes. Dijkstra y A* bloquean pesos negativos; Bellman–Ford y Floyd–Warshall los admiten y detectan ciclos negativos cuando existen. El mapa final dirigido no tiene ciclos negativos: un peso negativo por sí solo no implica un ciclo negativo.

**17 → 10 es inalcanzable**, respetando las flechas. Un ejemplo alcanzable para probar Dijkstra/A* es **10 → 17**: ruta 10 → 1 → 12 → 16 → 17, costo **22** en el positivo. En el original pueden cambiar tanto el costo como la ruta óptima.

Todos los algoritmos se implementan mediante lógica propia; NetworkX se utiliza para almacenar los datos y exportarlos. No se llaman sus funciones de búsqueda.

## A*

La pestaña inicia con el ejemplo alcanzable 10 → 17. Al encontrarlo, una partícula recorre las aristas ganadoras y luego los nodos parpadean cinco veces. Permite elegir heurística euclidiana calibrada o cero, animar cada paso, avanzar/retroceder, pausar, reiniciar y usar debug para mostrar directamente el resultado conservando la traza. Muestra g (costo acumulado), h (estimación restante), f = g + h, predecesor y estado abierto/cerrado.

Los píxeles del dibujo no son costos. Se calcula `α = min(peso / longitud)` sobre los arcos con longitud positiva y `h(n) = α × distancia(n, destino)`, con un pequeño margen numérico. Así la estimación respeta las unidades y no sobreestima el costo restante. Si no existe una escala informativa se usa cero. La [explicación de A* de Red Blob Games](https://www.redblobgames.com/pathfinding/a-star/introduction.html) describe el requisito de no sobreestimar para obtener rutas óptimas.

## Animaciones y matrices

Los nodos visitados se oscurecen; el nodo actual conserva el borde neón. Las rutas ganadoras se iluminan y, en Dijkstra, A* y las consultas de Floyd–Warshall, parpadean cinco veces. Cambiar parámetros, grafo o pestaña cancela la reproducción anterior.

Las matrices de Dijkstra tienen adyacencia de 30 × 30 (cantidad de arcos salientes por par) e incidencia de 30 × 63 (−1 en origen, +1 en destino). Cada paralela tiene su columna. El resaltado animado recorre una cruz completa y avanzar/retroceder reconstruye las consultas sin alterar los valores.

Bellman–Ford ofrece paso a paso, reproducción rápida por bloques y debug directo, saltos por pasada/verificación e inspección de la traza. Conserva los apartados del documento `Bellman-Ford__Ejemplo`.

Floyd–Warshall conserva la referencia documental opcional A–H de `warshall_floyd.xlsx`, separada del mapa estándar. Carga su matriz inicial y calcula las iteraciones; no copia los resultados anotados de las hojas. La referencia no dirigida conserva adyacencia simétrica e incidencia sin signo.

## Estructura

- `main.py`: entrada y tema de la aplicación.
- `grafo.py`: factories públicas de las dos variantes y exportación JSON.
- `modelos/datos_grafo.py`: única fuente de nodos, posiciones y aristas.
- `modelos/`: adyacencia, matrices, identidad de arista, validación y referencia XLSX.
- `algoritmos/`: lógica pura y contratos de resultados/eventos; registro de los cuatro algoritmos.
- `interfaz/`: ventana, dibujo con flechas, tema y reproducción compartida.
- `interfaz/algoritmos/`: controles y tablas independientes para cada algoritmo.
- `tests/`: pruebas de lógica, datos y Qt sin pantalla.
- `docs/superpowers/`: diseño y plan de esta migración.

Esta separación mantiene los datos fuera del dibujo y sigue la arquitectura [modelo/vista de Qt](https://doc.qt.io/qt-6/model-view-programming.html). Agregar una interfaz no impone las matrices ni la configuración de otro algoritmo.

## Capturas e informes PDF

«Capturas + PDF por paso» está activado inicialmente. PyQt6 captura la interfaz del algoritmo con sus colores, tablas y el punto medio de cada animación; [ReportLab](https://docs.reportlab.com/reportlab/userguide/ch2_graphics/) escribe las imágenes JPEG en bloques de64 páginas; [pikepdf/qpdf](https://pikepdf.readthedocs.io/en/stable/topics/jobs.html) une esos bloques desde disco en un PDF con una página por evento. Esto evita retener todas las capturas en memoria. Se usa [QWidget.grab](https://doc.qt.io/qt-6/qwidget.html#grab) para capturar la aplicación sin depender del escritorio o de otras ventanas.

Las cuatro carpetas son `informes/dijkstra/`, `informes/bellman_ford/`, `informes/warshall_floyd/` e `informes/a_estrella/`. Cada ejecución guarda su PDF y una subcarpeta `pasos/` con las capturas numeradas. El nombre incluye la variante y una huella del algoritmo, pesos, posiciones, sentidos y parámetros; cambiar una búsqueda genera otro informe. En Floyd, la huella corresponde al cálculo de todos los pares; origen/destino solo consultan esa matriz.

Si ese PDF ya está completo, se omite el algoritmo y se avisa «PDF existente». «Abrir informes» abre las carpetas. Para volver a animar sin generar capturas, desmarca la casilla. Las ejecuciones interrumpidas no se publican como PDF final; pueden iniciarse nuevamente. Cambiar parámetros o pestaña, navegar manualmente o pulsar «Cancelar grabación» detiene la captura.

La grabación muestra y captura **todos** los eventos incluso al elegir rápido/debug. El PDF se genera sin esperas añadidas, independientemente del slider. La reproducción sin capturas alcanza 20 ms por evento y 16 ms de refresco al máximo. El tiempo real del PDF depende del renderizado y la escritura de imágenes. Los artefactos generados se excluyen de Git.

## Verificación enfocada

Para esta mejora se ejecutan únicamente pruebas específicas, respetando el límite solicitado de menos de20 casos:

```bash
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -p test_informes.py -v
```

Los ocho casos verifican PDF/capturas en las cuatro interfaces, número de páginas, caché sin recalcular, cancelación, colores, recorrido y cinco parpadeos de A*, velocidad máxima e identidad de las ejecuciones. Se añaden tres regresiones seleccionadas, sin ejecutar la suite completa.

Para actualizar el archivo exportado a partir de la transcripción:

```bash
.venv/bin/python grafo.py
```
