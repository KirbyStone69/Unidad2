# Comparación de élites y población

Solicitud: sustituir la gráfica temporal del panel 04 por funciones élite y
puntos representativos de la población. Conservar métricas y controles.

- Configurar cantidad de élites reales conservadas (por defecto 2) y muestra de
  población para comparar (por defecto 5, máximo 20). Ajustar máximo de élites
  cuando cambie población. Validar ambos parámetros en el motor.
- Señales: Snapshot inmutable incluye élites, muestra y tamaño de población, con
  expresión y errores de entrenamiento. Muestrear por rangos de selección sin
  consumir RNG evolutivo ni usar valores reservados de validación.
- Mantener élites al generar y seleccionar siguiente población. Si toda la
  población es élite, no hay variación ni ajuste local; explicarlo en tooltip.
- Panel 04: pestaña Funciones con todas las élites y la muestra, métricas y
  expresiones copiables/tooltip; pestaña Curvas con datos, curvas élite y puntos
  predichos por muestra de población. No crear escena de árboles por individuo.
- QTableWidget con scroll y canvas con colecciones/blitting. Solo actualizar la
  pestaña visible y una vez por refresco existente, no por cada señal acumulada.
- Pruebas: elitismo 1/3/toda población, tamaños y procedencia de muestra, no consumir
  RNG, inmutabilidad; UI cuenta/limpieza/cambio de pestaña; regresión completa,
  incluido CSV y cancelación/reparación; inspección visual y revisión independiente.


## Completado

- Motor: 8 regresiones nuevas de élites, población y RNG. Pruebas inicialmente
  fallaron por campos ausentes; implementación y regresiones pasan.
- UI: contador, snapshot por señales, copia, limpieza, outliers y ajuste final
  oculto cubiertos. Se eliminó un redraw costoso del canvas oculto.
- Revisión independiente sin defectos en conservación o muestreo; observaciones
  de límites/copia/ajuste final resueltas con pruebas.
- Suite final: 132 passed en 30.55 s. Capturas y docs actualizadas.
