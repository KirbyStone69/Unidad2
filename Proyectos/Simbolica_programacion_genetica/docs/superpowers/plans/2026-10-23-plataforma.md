# Plataforma de regresión simbólica Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Ejecución continua autorizada por el usuario.

**Goal:** Curso interactivo completo con ocho unidades, evaluación persistente y laboratorio de PG.
**Architecture:** Núcleo TypeScript puro compartido; React para curso, exámenes y SVG; evolución en worker.
**Tech Stack:** React, TypeScript, Vite, KaTeX, Vitest, CSS responsivo.
**Spec:** docs/superpowers/specs/2026-10-23-plataforma-regresion-design.md

## Global Constraints
Español; paleta solicitada; conservar archivos existentes; sin cuentas/CDN; métricas indefinidas explícitas; no eval; raíz nivel cero; ≥10 ejercicios por unidad; simulacro 30; datos no fórmula en búsqueda.

## Review Focus
- CSV malformado: informar línea y bloquear importación.
- Datos constantes/cero: NMSE y R² indefinidos según denominador.
- Recarga de examen: conservar respuestas y fecha límite.
- LocalStorage corrupto o lleno: recuperar/avisar sin bloquear estudio.
- Mutaciones y cruces: respetar aridad y reparar altura sin modificar padres.

### Task 1: Núcleo y configuración
Files: package.json, tsconfig.json, vite.config.ts, src/domain/{tree,metrics,evolution,csv}.ts, tests/domain.test.ts.
Interfaces: Tree, Point, metrics(points,predictions), traverse(tree,order), height(tree), crossover(a,b,pathA,pathB), mutate(tree,type,rng), repair(tree,maxHeight), evolve(population,points,config,rng).
- [x] Escribir tests con resultados conocidos para métricas, árboles, selección, CSV y límites; ejecutar y observar fallo por módulos ausentes. Nota: la instalación bloqueó ese rojo inicial; excepción registrada en docs/progress.md, no se afirma TDD completo.
- [x] Implementar funciones puras y generador determinista; correr npm test hasta verde.

### Task 2: Contenido, calificación y persistencia
Files: src/content/{lessons,questions}.ts, src/domain/{assessment,storage}.ts, tests/assessment.test.ts.
Interfaces: Question con id/unit/type/answer/explanation/concept; grade(question,response); buildExam(mode,unit,seed,previous); Progress con attempts y activeExam.
- [x] Tests para 80+ originales, respuestas numéricas/orden, 30 preguntas ponderadas, persistencia corrupta y resultados reales; observar fallo.
- [x] Implementar banco, ocho lecciones y servicios; ejecutar suite.

### Task 3: Aplicación y visualizaciones
Files: src/{App,main}.tsx, src/styles.css, src/components/{TreeView,Plot,Math}.tsx, src/features/{Lessons,Activities,Assessment,Progress,Lab}.tsx, src/evolution.worker.ts.
Interfaces: consumir módulos de tareas 1/2; estado persistente de examen con deadline absoluta.
- [x] Tests de integración para entregar intento, recarga, repaso y temporizador; observar fallo.
- [x] Implementar navegación, lecciones, ejercicios, SVG, métricas, selección, operadores, evolución y CSV.
- [x] Verificar npm test y npm run build, escritorio/móvil y controles en navegador.

### Task 4: Revisión y entrega
Files: README.md, docs/progress.md, tests de regresión para hallazgos.
- [x] Revisar requisitos y código con revisor independiente; corregir hallazgos importantes con prueba RED→GREEN.
- [x] Ejecutar suite completa y build; documentar Debian, semántica matemática y límites.
