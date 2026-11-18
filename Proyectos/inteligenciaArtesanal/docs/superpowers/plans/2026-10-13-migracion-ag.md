# Migración fiel de a.pdf

**Objetivo:** transcribir y migrar secuencialmente maximización, minimización y multivariable.
**Arquitectura:** tres módulos independientes con los nombres, bucles y datos del libro. Una utilidad de compatibilidad reproduce float de C++ y rand; las reparaciones se identifican individualmente.
**Tecnología:** Python 3 estándar, unittest, C++17 para comparación, OCR local solo para extracción.
**Especificación:** solicitud del usuario; a.pdf, 12 dobles páginas.

## Restricciones
No algoritmos de terceros, no objetivos nuevos, no cambiar ruleta/cruce de un punto/mutación binaria; conservar peculiaridades definidas. No atribuir al libro los enlaces multivariable que no publica.

## Revisión
Bits menos significativos primero; copias por valor; redondeo float32; campos sin inicializar; accesos fuera de rango; fitness nulo/negativo; firmas multivariable incompletas.

- [x] Renderizar y examinar las 12 páginas; guardar OCR bruto y mapa de páginas.
- [x] Transcribir cabecera/base, minimización y los cuatro fragmentos multivariable, conservando errores literales.
- [x] Escribir pruebas de operaciones y observar fallos por módulos ausentes.
- [x] Migrar maximización y verificar.
- [x] Migrar minimización y verificar.
- [x] Migrar multivariable y documentar explícitamente los enlaces no publicados.
- [x] Compilar referencia C++ con reparaciones identificadas; comparar operaciones y generaciones con la misma secuencia de enteros aleatorios.
- [x] Ejecutar los tres CLI y suite completa; README, reporte y registro de resultados.

Decisiones: directorio nuevo migracion_ag, sin modificar archivos previos. La transcripción precede a toda implementación Python. Correcciones necesarias visibles en código y reporte; límites indefinidos se detectan, no se simula memoria basura. El CLI multivariable es un enlace añadido identificado, no una transcripción del main ausente.

Verificación final: 41 pruebas; tres referencias compiladas desde transcripción; 117 poblaciones cotejadas. Revisión independiente sin omisiones. Los desbordamientos extremos se rechazaron con pruebas RED→GREEN. R8 documenta la errata Tvac_int tras ampliación visual. Resultados de CLI y advertencias R1 conservados en migracion_ag/referencia/.
