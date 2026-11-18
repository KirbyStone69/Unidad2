# Motor ampliado Implementation Plan

> Ejecución nativa en esta sesión mediante superpowers:executing-plans, autorizada
> por el usuario: planificar primero, implementar y ejecutar pruebas después.

**Goal:** Buscar expresiones con funciones científicas y coeficientes reales,
con presupuesto explícito y diagnóstico honesto de ajuste.
**Architecture:** Separar expresiones/primitivas, optimización y evolución.
Mantener engine.py como API compatible para Qt y pruebas existentes.
**Tech Stack:** Python, NumPy, SciPy, PyQt6, Matplotlib, pytest.
**Spec:** docs/superpowers/specs/2026-10-20-motor-ampliado-design.md

## Restricciones globales
Interfaz exclusivamente PyQt6. Motor independiente. Semilla reproducible.
No codificar fórmula/coefs del usuario. No usar validación para entrenar.
Cancelar cooperativamente; no animar candidatos durante búsqueda automática.

## Riesgos a comprobar
- Funciones unarias y decimales no deben romper escenas ni operadores educativos.
- Exp/log/división en extremos deben producir resultados finitos documentados.
- Un ajuste pobre o solo entrenamiento no debe anunciar una solución exacta.
- La cancelación durante ajuste numérico debe liberar el hilo con rapidez.
- Desactivar trigonometría debe excluirla también de las semillas estructuradas.

## Tareas
- [x] 1. Expresiones: crear laboratorio/expressions.py; pruebas de primitivas,
  aridades, simplificación y límites en tests/test_expressions.py. Ejecutar rojo,
  implementar y verificar verde. Reexportar Node/random_tree/repair desde engine.
- [x] 2. Ajuste: crear laboratorio/optimization.py con ajuste afín y optimización
  de constantes acotada, cancelación y semillas de gramática. Pruebas de ajuste,
  generalidad y separación de datos en tests/test_optimization.py. Añadir SciPy.
- [x] 3. Evolución: ampliar Config/Snapshot/Evolution, operadores de variación,
  caché y control de diversidad. Probar límites, monotonía y determinismo;
  pruebas numéricas de descubrimiento en tests/test_search.py.
- [x] 4. Qt: adaptar worker.py a cancelación/parada por objetivo; ampliar controles
  en window.py y números/unarias en tree_view.py. Probar cierre, pausa, selección
  de primitivas, diagnósticos y escenas en tests/test_gui.py.
- [x] 5. Ejecutar suite completa y benchmark multisemilla sobre datasets distintos.
  Revisar código/resultados; corregir defectos concretos y repetir pruebas afectadas.
  Documentar ejecución, semántica protegida y límites; guardar informe reproducible.


## Registro de ejecución
- Expresiones: nuevas pruebas fallaron por ausencia de unarias/aridades; implementación y pruebas verdes.
- Ajuste: tres pruebas nuevas fallaron antes de crear optimization.py; después pasaron.
- Evolución: nuevas pruebas de descubrimiento/límites/validación fallaron; tras implementación pasaron.
- Hallazgo: racionales se proponían después de demasiadas trigonométricas. Se equilibró el currículo; la prueba racional pasó sin relajar tolerancias.
- Qt: pruebas fallaron por controles/diagnóstico/parada aún ausentes; implementación y pruebas verdes.
- Ruling: las pruebas de avance exacto desactivan la parada por objetivo, pues ahora puede converger antes del límite. Una prueba independiente exige la parada temprana.
- Hallazgo: el repintado completo de Matplotlib bloqueaba temporizadores con el trabajador activo. Se reprodujo y midió, se cambió a blitting y se añadió una regresión de redibujado y latencia.
- Revisión independiente: reparar espécimen educativo también debe usar funciones activas; corregido. Sin hallazgos bloqueantes.
- Exportación: añadida precisión completa y protecciones por nodo; probada contra evaluación del motor para todas las primitivas.
- Suite: 74 pruebas aprobadas. Benchmark: 18 ejecuciones alcanzaron objetivo con validación y malla adicional. Detalles y límites en docs/VALIDATION.md.
