# Mejor solución por generación

El panel 04 registra una propuesta por generación, incluida la generación 0
(población inicial). Cada fila muestra generación, MSE, NMSE, número de nodos y
expresión; permite copiar su fórmula NumPy completa.

La única gráfica está en 03: datos originales, curvas de los mismos registros
que aparecen en la tabla y predicción ganadora destacada en rojo oscuro (`#B83240`). El control «Mejores por
generación» oculta o muestra el historial; «Rango de datos» controla el encuadre.
Los colores de las filas corresponden a las curvas. CSV, Random y nueva búsqueda
limpian los registros y la caché de curvas.

Cada señal del trabajador se registra antes de limitar el refresco visual. Así
se conservan generaciones rápidas. Las actualizaciones repetidas de una misma
generación reemplazan su entrada sin duplicarla. El archivo guarda únicamente
árbol y métricas, y la tabla actualiza las filas que cambian. La evaluación de
curvas se cachea por árbol. El control Elitismo sigue configurando la conservación
de individuos del motor; no determina la cantidad de filas mostradas.

Pruebas de interfaz: ráfaga de generaciones sin refresco intermedio, duplicados,
copia coherente, limpieza con Random/CSV, curvas fuera de rango, un único canvas
y controles de visibilidad. Se mantiene la suite del motor y reparación Qt.
La revisión independiente no encontró defectos bloqueantes.

[Vista de escritorio](preview.png).

Verificación final: **134 pruebas aprobadas en 29.86 s**. Medición de escritorio
con 1,000 observaciones: convergencia en generación 11, 1.65 s, 87 pulsos Qt y
máximo intervalo de 0.106 s. Se revisó visualmente la captura del escritorio.

La barra de progreso se eliminó. La interfaz inicia con Generaciones «Sin límite»
(0), sin plazo de tiempo. Se puede detener manualmente, al alcanzar el objetivo
de error o mediante un límite de generaciones opcional.
