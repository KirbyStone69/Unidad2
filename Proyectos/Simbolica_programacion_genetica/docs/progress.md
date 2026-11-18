# Registro — plan: docs/superpowers/plans/2026-10-23-plataforma.md
Diseño aprobado: «dale we».
Decisión: ejecución directa en el directorio solicitado; no hay repositorio Git ni rama que aislar. Se preservan scripts y entorno.
Pre-flight: Tree/Point alimentan visualizaciones y motor; Question/Attempt alimentan evaluaciones y progreso. Un solo núcleo compartido.

Task 1: núcleo implementado; 19 pruebas iniciales verdes. La instalación tardó y bloqueó ejecutar el rojo inicial del núcleo: pruebas escritas antes del código, pero primer resultado ejecutable ya fue verde. No se afirma TDD completo para esa parte.
Task 2: ocho unidades, 80 problemas de curso y 46 avanzados; variantes calculadas, opciones barajadas, corrección y almacenamiento versionado.
Task 3: curso, prácticas y evaluaciones montados; SVG, tabla de métricas, selección, cuatro mutaciones, reparación, ciclo paso a paso y motor en worker. Primer test de interfaz falló con App ausente y pasó después de implementarlo.
Revisión independiente: seis hallazgos importantes reproducidos. Corregidos con regresiones observadas en rojo y verde: repetición de originales; nota importada incoherente; comillas CSV mal colocadas; media desbordada y métricas no finitas; entradas extremas que desmontaban React; alturas fraccionarias. Se extendió revisión CSV a cabecera malformada y se corrigió con regresión.
Decisión: importación CSV inválida bloquea archivo entero; evita aceptar datos silenciosamente.
Decisión: entradas numéricas del curso limitadas a ±10000, avisado en interfaz; evita desbordamientos y mantiene ejemplos legibles.
Decisión: versión explícita de preguntas (revision 1) además del esquema de progreso; copias incompatibles se rechazan con aviso.
Decisión: examen final usa exclusivamente 46 problemas avanzados, con distribución 2,3,5,2,5,4,5,4. El curso mantiene 10 originales guiados por unidad.
Dependencias: actualización de Vitest y KaTeX, peer @testing-library/dom explícito; npm install sin flags y npm audit sin vulnerabilidades. KaTeX fijado a 0.18.2 por compatibilidad con Node 20 y parche del aviso de confianza.
Verificación intermedia: 47 pruebas verdes; build de producción exitoso sin aviso de chunks grandes tras separar KaTeX.

Revisión visual: capturas de escritorio y móvil inspeccionadas; diseño responsivo y paneles de árboles verificados. Se añadió favicon tras reproducir un 404 en consola.
Pruebas adicionales RED→GREEN: fases de corte/intercambio/reconexión; normalización de coordenadas SVG para valores extremos; recuperación sin repetir variante inmediata; ordenamiento con opciones barajadas y espacios; explicación de mutación sin nodo elegible.
Verificación final funcional: 56 pruebas unitarias/integración y 6 pruebas Playwright en Chromium (escritorio + Pixel 7) verdes. La suite de navegador se ejecutó sobre dist/ servido por Vite preview, con bloqueo de recursos no locales en el recorrido del curso. CSV y motor worker reales, reloj/respuestas tras recarga, corrección solo al entregar y ausencia de errores de consola verificados.
Se verifican también los tipos del propio harness E2E antes de ejecutarlo; @types/node es dependencia explícita.
Limitaciones documentadas: PG acotada sin optimizador local de constantes; no garantiza recuperar la fórmula objetivo. Métricas del laboratorio son de entrenamiento. Estado evolutivo efímero al salir del laboratorio. El contenido educativo se sirve localmente, sin PWA ni sincronización remota.
No hay hallazgos críticos/importantes pendientes de la revisión independiente. No se integró ni publicó en ningún servicio externo; este directorio no es repositorio Git.
