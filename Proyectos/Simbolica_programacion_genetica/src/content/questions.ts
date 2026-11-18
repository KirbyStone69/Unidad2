import { seeded } from "../domain/tree";
import { advancedDraft, advancedCounts } from "./advanced";
export type QuestionType = "choice" | "number" | "order";
export interface Question {
  revision: 1;
  id: string;
  unit: number;
  original: number;
  type: QuestionType;
  prompt: string;
  options?: string[];
  answer: string;
  explanation: string;
  concept: string;
  tolerance?: number;
  code?: string;
}
type Draft = Omit<Question, "id" | "unit" | "original" | "revision">;
const c = (
  prompt: string,
  options: string[],
  correct: number,
  explanation: string,
  concept: string,
  code?: string,
): Draft => ({
  type: "choice",
  prompt,
  options,
  answer: String(correct),
  explanation,
  concept,
  code,
});
const n = (
  prompt: string,
  answer: number,
  explanation: string,
  concept: string,
): Draft => ({
  type: "number",
  prompt,
  answer: String(answer),
  tolerance: 0.001,
  explanation,
  concept,
});
const o = (
  prompt: string,
  options: string[],
  answer: string,
  explanation: string,
  concept: string,
): Draft => ({ type: "order", prompt, options, answer, explanation, concept });
export function makeQuestion(
  unit: number,
  index: number,
  variant = 0,
): Question {
  const k = (variant % 7) + 2;
  const units: Record<number, () => Draft[]> = {
    1: () => [
      c(
        "Solo conocemos (1,1), (2,4), (3,9). ¿Qué podemos concluir?",
        [
          "x² es la única función posible",
          "x² ajusta, pero otras funciones también pueden hacerlo",
          "Cualquier función con tres constantes es correcta",
          "Se ha demostrado la ley física",
        ],
        1,
        "x² ajusta los tres puntos. También x² + a(x−1)(x−2)(x−3) para cualquier a; los datos finitos no identifican una función única.",
        "Problema inverso",
      ),
      c(
        "Una búsqueda devuelve el mejor candidato visto tras 100 generaciones. ¿Qué afirmación está justificada?",
        [
          "Es el óptimo global",
          "Es la ecuación original",
          "Es el mejor observado; no hay garantía global",
          "Su error de validación es cero",
        ],
        2,
        "Una heurística explora sin demostrar que revisó todo el espacio. El mejor observado no constituye una prueba de optimalidad ni generalización.",
        "Heurísticas",
      ),
      n(
        `Problema directo: f(x)=x²+1. Si x=${k}, ¿cuánto vale y?`,
        k * k + 1,
        `Se sustituye x: ${k}²+1=${k * k + 1}. La expresión ya es conocida; solo calculamos su salida.`,
        "Problema directo",
      ),
      c(
        "¿Qué cambio convierte regresión paramétrica en búsqueda simbólica?",
        [
          "Aumentar el número de puntos",
          "Buscar también la estructura de la expresión",
          "Reducir el MSE",
          "Usar siempre polinomios de grado dos",
        ],
        1,
        "Ajustar a y b en ax+b fija la estructura. Regresión simbólica explora operadores, estructura y constantes, dentro de una biblioteca definida.",
        "Regresión simbólica",
      ),
      c(
        "Un cromosoma binario codifica constantes de una fórmula fija. ¿Es necesariamente PG de árboles?",
        [
          "Sí, porque usa población",
          "Sí, porque minimiza error",
          "No; el uso de evolución no implica representar programas como árboles",
          "No puede ser un algoritmo genético",
        ],
        2,
        "La representación importa: un AG puede optimizar parámetros binarios. En la PG de árboles los individuos representan programas o expresiones de estructura variable.",
        "AG y PG",
      ),
      c(
        "Un modelo ajusta exactamente 4 puntos y falla en datos nuevos. ¿Qué evaluación faltó?",
        [
          "Contar nodos raíz",
          "Evaluar generalización con datos no usados para ajustar",
          "Exigir MSE negativo",
          "Cambiar todo por búsqueda exacta",
        ],
        1,
        "Un ajuste de entrenamiento puede sobreajustar. Un conjunto de validación permite estimar comportamiento fuera de las muestras usadas en búsqueda.",
        "DDM",
      ),
      c(
        "¿Cuál describe mejor extracción de conocimiento en DDM?",
        [
          "Copiar los datos como una tabla",
          "Proponer relaciones interpretables contrastadas con datos y dominio",
          "Demostrar causalidad solo con correlación",
          "Memorizar cada observación",
        ],
        1,
        "DDM construye modelos a partir de datos. Interpretar una expresión exige revisar validación, unidades y plausibilidad; correlación no demuestra causalidad.",
        "DDM",
      ),
      c(
        "Verdadero o falso, con razón: una heurística siempre es más rápida que cualquier método exacto.",
        [
          "Verdadero: no calcula errores",
          "Falso: depende del problema y presupuesto, no hay garantía universal",
          "Verdadero: nunca explora soluciones malas",
          "Falso: las heurísticas siempre son exhaustivas",
        ],
        1,
        "No existe esa garantía universal. Una búsqueda exacta puede ser rápida en instancias pequeñas, y una heurística puede gastar mucho sin una buena solución.",
        "Heurísticas",
      ),
      o(
        "Ordena un flujo básico de modelado dirigido por datos.",
        [
          "Validar en muestras reservadas",
          "Recoger y revisar datos",
          "Buscar modelos usando entrenamiento",
          "Interpretar el modelo y sus límites",
        ],
        "2,3,1,4",
        "Primero se revisan datos, después se ajusta con entrenamiento, se valida y finalmente se interpreta con evidencia de sus límites.",
        "DDM",
      ),
      c(
        "Se pide encontrar f a partir de pares x,y. ¿Qué línea corresponde al problema inverso?",
        [
          "y = f(3)",
          "buscar_expresiones(datos)",
          "print(f(2))",
          "dibujar_una_funcion_conocida()",
        ],
        1,
        "buscar_expresiones(datos) parte de observaciones para proponer una relación. Las otras operaciones parten de una función ya conocida.",
        "Problema inverso",
      ),
    ],
    2: () => [
      n(
        "¿Cuántos nodos tiene +(x, *(2,x))?",
        5,
        "Contamos raíz +, hoja x, operador *, hoja 2 y hoja x: cinco nodos. Las repeticiones de x son nodos distintos.",
        "Tamaño",
      ),
      n(
        "¿Cuál es la altura de +(x, *(2,x)), contando aristas desde la raíz?",
        2,
        "La ruta más larga es + → * → x (o 2): contiene dos aristas. Tamaño cinco no significa altura cinco.",
        "Altura",
      ),
      n(
        `¿Máximo de nodos en un árbol binario de altura ${k}?`,
        2 ** (k + 1) - 1,
        `Sumamos niveles 0 a ${k}: 1+2+…+2^${k}=2^(${k}+1)−1=${2 ** (k + 1) - 1}. Es una cota, no el tamaño de todo árbol de esa altura.`,
        "Cota binaria",
      ),
      c(
        "Para sqrt(2*x²+5*x−3), ¿cuál es la raíz?",
        ["−", "sqrt", "*", "x"],
        1,
        "La operación aplicada al resultado completo es sqrt. Tiene un único hijo: la resta cuyo resultado es el radicando.",
        "Raíz y aridad",
      ),
      c(
        "¿Cuál fragmento es estructuralmente inválido?",
        ["sin(x)", "+(x,2)", "*(x)", "sqrt(4)"],
        2,
        "Multiplicación es binaria y requiere dos hijos. sin y sqrt son unarios; los terminales no tienen hijos.",
        "Aridad",
      ),
      c(
        "Un árbol sqrt(−1) tiene aridad correcta. ¿Es evaluable en reales?",
        [
          "Sí, porque tiene dos nodos",
          "No; validez estructural y dominio matemático son condiciones distintas",
          "Sí; toda raíz está definida",
          "No; sqrt es binaria",
        ],
        1,
        "sqrt tiene un hijo, por lo que su estructura es válida. Sin embargo, un radicando negativo no produce un resultado real.",
        "Validez",
      ),
      c(
        "¿Qué relación genotipo/fenotipo es correcta en PG de árboles?",
        [
          "Genotipo: MSE; fenotipo: población",
          "Genotipo: estructura codificada; fenotipo: función o comportamiento que expresa",
          "Genotipo: datos; fenotipo: semilla",
          "Ambos son siempre cadenas binarias",
        ],
        1,
        "El árbol codificado es una representación del individuo. La expresión y el comportamiento calculado a partir de él constituyen su fenotipo.",
        "Representación",
      ),
      c(
        "¿Cuántas aristas tiene un árbol conectado de 9 nodos?",
        ["8", "9", "10", "Depende de la altura"],
        0,
        "Todo árbol conectado sin ciclos de N nodos tiene N−1 aristas: aquí 9−1=8. No depende de que sea completo.",
        "Aristas",
      ),
      c(
        "Verdadero o falso: todo árbol binario tiene exactamente dos hijos por nodo interno.",
        [
          "Verdadero, sin excepción",
          "Falso: binario significa como máximo dos; uno unario puede tener un hijo",
          "Falso: todos tienen tres",
          "Verdadero: las hojas también tienen dos",
        ],
        1,
        "Binario significa a lo sumo dos hijos. Un árbol binario lleno sí tiene exactamente dos hijos por nodo interno; las hojas tienen cero.",
        "Árboles binarios",
      ),
      c(
        "En +(x,2), ¿cuáles son las hojas?",
        ["Solo +", "+ y x", "x y 2", "Todas son raíces"],
        2,
        "Las hojas son nodos sin hijos. x y 2 son terminales. El + es raíz y nodo interno con dos hijos.",
        "Terminales",
      ),
    ],
    3: () => [
      c(
        "Preorder de *(+(x,2),−(x,3)):",
        ["*,+,x,2,−,x,3", "x,+,2,*,x,−,3", "x,2,+,x,3,−,*", "+,*,x,2,−,3,x"],
        0,
        "Preorder visita primero raíz *, después todo el subárbol + (raíz,x,2) y luego todo el subárbol − (raíz,x,3).",
        "Preorder",
      ),
      c(
        "Postorder de +(x,*(2,3)):",
        ["+,x,*,2,3", "x,2,3,*,+", "x,+,2,*,3", "2,3,x,+,*"],
        1,
        "Se procesa la hoja x; luego hijos 2 y 3 antes de *; finalmente +. La operación siempre viene después de sus operandos.",
        "Postorder",
      ),
      n(
        `Evalúa *(+(x,2),−(x,3)) para x=${k}.`,
        (k + 2) * (k - 3),
        `Primero x+2=${k + 2}; después x−3=${k - 3}; finalmente (${k + 2})×(${k - 3})=${(k + 2) * (k - 3)}.`,
        "Evaluación",
      ),
      c(
        "Una pila procesa postorder x,3,− para x=8. ¿Qué resultado debe producir?",
        ["−5", "5", "11", "24"],
        1,
        "Se apila 8, luego 3. Al ver −, se extrae primero derecho=3 y después izquierdo=8: 8−3=5. Invertirlos cambia el resultado.",
        "Pila postorder",
      ),
      c(
        "¿Qué recorrido favorece evaluación directa de abajo hacia arriba?",
        [
          "Preorder sin memoria",
          "Postorder",
          "Inorder sin paréntesis",
          "Cualquiera produce el mismo algoritmo sin adaptación",
        ],
        1,
        "En postorder cada operador se visita después de sus hijos; sus valores ya están disponibles cuando se calcula el nodo padre.",
        "Postorder",
      ),
      c(
        "El inorder sin paréntesis de +(x,*(2,3)) y *(+(x,2),3) puede ser igual. ¿Qué se pierde?",
        [
          "Los nombres de terminales",
          "La estructura de agrupación",
          "El número de nodos",
          "La aridad de todos los operadores",
        ],
        1,
        "Ambos pueden producir x,+,2,*,3. Los paréntesis o una representación de estructura son necesarios para distinguir x+(2*3) de (x+2)*3.",
        "Inorder",
      ),
      c(
        "Detecta el error de este evaluador de resta.",
        [
          "La resta debe tener tres hijos",
          "Los operandos están invertidos",
          "No hay error",
          "x no puede ser hoja",
        ],
        1,
        "Se debe evaluar izquierda menos derecha. El código devuelve derecha menos izquierda; falla en operadores no conmutativos.",
        "Código de evaluación",
        "def evaluar(n):\n    if n.hoja: return n.valor\n    return evaluar(n.derecha) - evaluar(n.izquierda)",
      ),
      o(
        "Ordena las evaluaciones para +( *(2,x), 1), con x=4.",
        ["Sumar 8+1", "Obtener 2 y 4", "Multiplicar 2*4"],
        "2,3,1",
        "Se obtienen los terminales 2 y x=4, se calcula su producto 8 y finalmente se suma 1 para obtener 9.",
        "Dependencias",
      ),
      n(
        "¿Cuántas visitas a nodos realiza un recorrido completo sobre un árbol de 13 nodos?",
        13,
        "Cada nodo se visita exactamente una vez: trece visitas. La posición de la raíz en la secuencia no cambia este conteo.",
        "Recorridos",
      ),
      c(
        "Verdadero o falso: evaluar sqrt(x−3) en x=2 por postorder elimina el problema de dominio.",
        [
          "Verdadero: postorder protege operaciones",
          "Falso: el orden de evaluación no cambia que sqrt(−1) carece de valor real",
          "Verdadero: da cero",
          "Falso: postorder nunca visita sqrt",
        ],
        1,
        "Primero se calcula 2−3=−1 y luego sqrt(−1). El recorrido correcto no convierte una operación fuera de dominio en una operación válida.",
        "Dominio",
      ),
    ],
    4: () => [
      c(
        "¿Qué biblioteca permite generar senos y productos con aridad coherente?",
        ["sin:2, *:1", "sin:1, *:2", "sin:0, *:0", "sin:2, *:2"],
        1,
        "sin recibe un argumento y multiplicación recibe dos. La biblioteca debe registrar esta aridad para generar hijos correctos.",
        "Biblioteca",
      ),
      c(
        "¿Cuál expresión falla en reales para x=0?",
        ["cos(x)", "x+1", "log(x)", "sqrt(x)"],
        2,
        "log(0) no está definido como número real finito. cos(0)=1 y sqrt(0)=0 sí están definidos.",
        "Logaritmo",
      ),
      c(
        "Se alcanza profundidad máxima h=3. ¿Qué debe generar el constructor en nivel 3?",
        [
          "Un operador binario más",
          "Un terminal",
          "Otro árbol de altura 3",
          "Siempre sin",
        ],
        1,
        "Todo nodo del nivel límite debe ser hoja. Si se coloca un operador con hijos, estos excederían la altura máxima.",
        "Generación",
      ),
      n(
        `Un árbol cadena tiene altura ${k}. ¿Cuántos nodos contiene?`,
        k + 1,
        `Una cadena de ${k} aristas contiene ${k + 1} nodos, incluyendo la raíz. La cota binaria no obliga a llenar niveles.`,
        "Altura y tamaño",
      ),
      c(
        "¿Cuál árbol tiene altura 1 y tamaño 2?",
        ["+(x,2)", "sin(x)", "x", "+(x,*(2,x))"],
        1,
        "sin(x) tiene una raíz y una hoja: dos nodos unidos por una arista. +(x,2) tiene tres nodos aunque también altura 1.",
        "Altura y tamaño",
      ),
      c(
        "Verdadero o falso: división protegida y división ordinaria representan siempre la misma función.",
        [
          "Verdadero, solo cambia velocidad",
          "Falso: al asignar un valor al divisor cero cambia la semántica",
          "Verdadero, ambas dan infinito",
          "Falso: la protegida es ternaria",
        ],
        1,
        "La división ordinaria no está definida con divisor cero. Una división protegida asigna un valor por convenio y por tanto define otra operación.",
        "Operaciones protegidas",
      ),
      c(
        "¿Qué restricción necesita sqrt(g(x)) para evaluarse en reales?",
        ["g(x)>1", "g(x)≥0", "g(x)≠0", "Ninguna"],
        1,
        "La raíz cuadrada real está definida para radicandos no negativos, incluyendo cero. No basta con que el árbol esté bien formado.",
        "Raíz cuadrada",
      ),
      c(
        "¿Cuál resultado no es real bajo la potencia ordinaria?",
        ["2^3", "0^2", "(−1)^0.5", "(−2)^2"],
        2,
        "Elevar −1 a 1/2 equivale a una raíz cuadrada negativa. Las otras tres expresiones producen valores reales finitos.",
        "Potencia",
      ),
      c(
        "¿Qué problema tiene crear siempre dos hijos para todos los operadores?",
        [
          "Ninguno",
          "Produce sin y log con aridad inválida",
          "Impide usar sumas",
          "Reduce toda altura a cero",
        ],
        1,
        "Los operadores unarios requieren un solo hijo. La generación debe consultar la aridad de cada operador en lugar de asumir que todos son binarios.",
        "Generación",
      ),
      c(
        "En módulo con divisor cero, ¿qué política ordinaria corresponde?",
        [
          "Devolver siempre el numerador",
          "Marcar error de dominio",
          "Cambiarlo por suma sin avisar",
          "Dar MSE=0",
        ],
        1,
        "El módulo por cero es indefinido. Un candidato que lo produce debe ser rechazado o penalizado, salvo semántica protegida declarada explícitamente.",
        "Módulo",
      ),
    ],
    5: () => [
      n(
        `Para y=[1,${k}], ŷ=[0,${k}], calcula SSE.`,
        1,
        "Los errores son 1−0=1 y k−k=0. Sus cuadrados suman 1²+0²=1, independientemente de k.",
        "SSE",
      ),
      n(
        `Para y=[${k},${k + 2}], ŷ=[${k - 1},${k + 1}], calcula MSE.`,
        1,
        "Ambos errores valen 1. SSE=1²+1²=2; con n=2, MSE=2/2=1. No se usa n−1.",
        "MSE",
      ),
      n(
        `Para y=[0,${k}], ŷ=[0,0], calcula NMSE=Σ(y−ŷ)²/Σy².`,
        1,
        `SSE=0²+${k}²=${k * k}. La energía Σy² también es ${k * k}; NMSE=1. Esta normalización no es la varianza.`,
        "NMSE",
      ),
      n(
        "Para y=[1,3], ŷ=[2,2], calcula R².",
        0,
        "ȳ=2. SSE=(1−2)²+(3−2)²=2. SST=(1−2)²+(3−2)²=2. R²=1−2/2=0.",
        "R²",
      ),
      n(
        "Para y=[1,3], ŷ=[4,4], calcula R².",
        -4,
        "ȳ=2 y SST=2. SSE=(1−4)²+(3−4)²=9+1=10. R²=1−10/2=−4: peor que predecir la media.",
        "R² negativo",
      ),
      c(
        "Si y=[0,0] y ŷ=[0,0], ¿qué métricas están definidas con las fórmulas del curso?",
        [
          "Todas son cero",
          "Solo MSE=0; NMSE y R² son indefinidos",
          "R²=1 necesariamente",
          "Ninguna, incluso MSE",
        ],
        1,
        "MSE=0/2=0. NMSE tiene denominador Σy²=0 y R² tiene SST=0; no dividimos entre cero ni asignamos un valor arbitrario.",
        "Denominadores",
      ),
      c(
        "Detecta el error en este cálculo de MSE.",
        [
          "No hay error",
          "Falta elevar al cuadrado cada residuo",
          "Se debe dividir por y",
          "Debe maximizarse",
        ],
        1,
        "Los errores con signos opuestos pueden cancelarse. MSE necesita sum((y_i−p_i)**2)/n para medir magnitud cuadrática.",
        "Código de métricas",
        "mse = sum(y_i - p_i for y_i, p_i in datos) / len(datos)",
      ),
      c(
        "R²=1 en entrenamiento. ¿Qué demuestra?",
        [
          "Se recuperó la expresión original única",
          "SSE=0 si SST>0; no garantiza identidad simbólica ni generalización",
          "NMSE indefinido siempre",
          "La complejidad del árbol es mínima",
        ],
        1,
        "Con SST positivo, R²=1 implica SSE=0 en esas muestras. Distintas funciones pueden coincidir allí y diferir fuera de ellas.",
        "Interpretación",
      ),
      n(
        "Datos y=[1,2,6]. ¿Cuánto vale ȳ?",
        3,
        "El promedio se calcula con valores reales: (1+2+6)/3=9/3=3. No se utiliza el promedio de predicciones.",
        "Media real",
      ),
      c(
        "Al multiplicar y y ŷ por 10, con denominadores no nulos, ¿qué ocurre?",
        [
          "MSE×100; NMSE y R² se conservan",
          "Todas se multiplican por 10",
          "MSE no cambia",
          "R²×100",
        ],
        0,
        "Cada residuo cuadrático se multiplica por 100. En NMSE y en el cociente SSE/SST se cancela ese mismo factor.",
        "Escala",
      ),
    ],
    6: () => [
      n(
        "MSE=[0,3]. Con w=1/(1+MSE), ¿probabilidad del primer individuo?",
        0.8,
        "Los pesos son 1 y 1/4. La suma es 1.25; p1=1/1.25=0.8, p2=0.2.",
        "Ruleta",
      ),
      c(
        "Torneo binario: A tiene MSE=0.2 y B=0.8. ¿Quién gana?",
        [
          "B, porque es mayor",
          "A, porque minimizamos MSE",
          "Siempre al azar",
          "Ninguno si ambos errores son positivos",
        ],
        1,
        "Al minimizar error, 0.2 es mejor que 0.8. El azar elige participantes; la comparación del torneo elige al mejor de ellos.",
        "Torneo",
      ),
      c(
        "Usar p_i=MSE_i/ΣMSE para seleccionar padres causa…",
        [
          "Más oportunidades a candidatos de mayor error",
          "Siempre selección del mínimo",
          "Pesos negativos",
          "Probabilidad uniforme garantizada",
        ],
        0,
        "El peso aumenta con MSE: se favorece precisamente a individuos peores. Debe transformarse el error a aptitud favorable, por ejemplo 1/(1+MSE).",
        "Error y aptitud",
      ),
      c(
        "SUS con cuatro selecciones usa…",
        [
          "Cuatro desplazamientos independientes",
          "Un desplazamiento aleatorio y cuatro punteros separados 1/4",
          "Solo el máximo de MSE",
          "Cuatro torneos obligatorios",
        ],
        1,
        "SUS elige un único desplazamiento en [0,1/4) y coloca los otros punteros cada 1/4 sobre la acumulación de probabilidades.",
        "SUS",
      ),
      n(
        `Un individuo tiene MSE=${k}. ¿Cuál es w=1/(1+MSE)?`,
        1 / (1 + k),
        `Sustituimos el error: w=1/(1+${k})=1/${k + 1}. Este peso aún debe normalizarse para convertirse en probabilidad.`,
        "Aptitud",
      ),
      c(
        "Todos los candidatos tienen el mismo MSE finito. ¿Cómo es la ruleta con la transformación indicada?",
        [
          "Uniforme",
          "Solo el primero puede salir",
          "No está definida",
          "Favorece al más grande",
        ],
        0,
        "La transformación da el mismo peso a todos. Al normalizar, cada uno recibe probabilidad 1/N; el tamaño no interviene en esa fórmula.",
        "Normalización",
      ),
      c(
        "¿Qué es un individuo en la PG de árboles del curso?",
        [
          "Un bit",
          "Un árbol que codifica una función candidata",
          "Una fila del CSV",
          "El promedio de población",
        ],
        1,
        "Cada árbol define una expresión evaluable en los x de los datos. Su MSE permite compararlo con los demás individuos de la población.",
        "Población",
      ),
      c(
        "Una ruleta asigna probabilidad 0.7 a A. En diez selecciones, ¿A sale exactamente siete veces?",
        [
          "Sí, por definición",
          "No; siete es el valor esperado, no una garantía de conteo",
          "Sí si MSE es cero",
          "No; solo puede salir una vez",
        ],
        1,
        "Las selecciones aleatorias independientes tienen variación. Una probabilidad de 0.7 implica esperanza 7 en diez sorteos, no un resultado obligatorio.",
        "Probabilidad",
      ),
      c(
        "Un árbol divide por cero en una muestra. ¿Cómo tratarlo en esta biblioteca no protegida?",
        [
          "Asignar MSE=0",
          "Marcar inválido y peso de selección cero; regenerar si todos son inválidos",
          "Omitir esa muestra silenciosamente",
          "Declararlo élite",
        ],
        1,
        "No se puede calcular un MSE válido ocultando errores. Se penaliza el candidato; si toda la población falla se necesita una política explícita de regeneración.",
        "Candidatos inválidos",
      ),
      c(
        "¿Qué error hay en este torneo de minimización?",
        [
          "Usa dos participantes",
          "Escoge el mayor MSE",
          "MSE debe ser binario",
          "No hay error",
        ],
        1,
        "max elige mayor error. Para minimizar MSE debe usarse min o una comparación que prefiera el menor valor.",
        "Código de selección",
        "ganador = max(participantes, key=lambda ind: ind.mse)",
      ),
    ],
    7: () => [
      c(
        "Cruce: P1=+(x,2), P2=*(3,4). Se intercambia la hoja 2 con la hoja 3. ¿Hijo 1?",
        ["+(x,3)", "*(2,4)", "+(3,2)", "*(x,4)"],
        0,
        "El contexto de P1 se conserva: +(x, □). En el hueco se inserta el subárbol 3. El otro hijo es *(2,4).",
        "Cruce",
      ),
      c(
        "La mutación 3→x en una hoja es…",
        ["Switching", "Terminal", "Cruce", "Reparación por altura"],
        1,
        "Se cambia el contenido de una hoja sin modificar su contexto. Puede cambiar una constante por variable o por otra constante.",
        "Mutación terminal",
      ),
      c(
        "¿Qué sustitución conserva aridad directamente?",
        ["+ → sin", "* → cos", "− → /", "log → +"],
        2,
        "− y / son binarios. Los otros cambios requieren eliminar o añadir hijos; cambiar solo la etiqueta dejaría un árbol estructuralmente inválido.",
        "Mutación operador",
      ),
      n(
        `Switching de x−${k}, evaluado en x=1: ¿resultado?`,
        k - 1,
        `Switching intercambia hijos: ${k}−x. Para x=1, el resultado es ${k}−1=${k - 1}. En resta el orden importa.`,
        "Switching",
      ),
      c(
        "Cambiar + por sin manteniendo dos hijos produce…",
        [
          "Un árbol válido de menor altura",
          "Aridad inválida; debe elegirse un hijo y eliminar el otro explícitamente",
          "Siempre el mismo fenotipo",
          "Una operación ternaria",
        ],
        1,
        "sin admite un solo argumento. El cambio de aridad exige una política estructural; no basta con renombrar el nodo.",
        "Cambio de aridad",
      ),
      c(
        "Pm=0.2 y probabilidad condicional de switching=0.25. ¿Probabilidad total de switching por descendiente?",
        ["0.45", "0.25", "0.05", "0.8"],
        2,
        "Primero debe ocurrir mutación (0.2), después elegirse switching (0.25). Por la regla del producto: 0.2×0.25=0.05.",
        "Ruleta de mutaciones",
      ),
      c(
        "Un descendiente tiene altura 6 y el máximo es 4. Poda al límite significa…",
        [
          "Eliminar el árbol siempre",
          "Reemplazar por terminales los nodos internos en nivel 4",
          "Cambiar solo el MSE",
          "Añadir dos niveles",
        ],
        1,
        "Con raíz en nivel cero, los nodos del nivel 4 no pueden conservar hijos. Convertirlos en terminales limita todas las rutas a cuatro aristas.",
        "Reparación",
      ),
      c(
        "Rechazar y repetir ante exceso de altura requiere…",
        [
          "Un límite de reintentos y salida válida si no se consigue",
          "Reintentar sin límite necesariamente",
          "Aceptar el inválido después",
          "Borrar los padres",
        ],
        0,
        "Un bucle sin límite puede bloquearse. Con intentos acotados, se puede conservar el padre válido si ninguna propuesta satisface las restricciones.",
        "Rechazo",
      ),
      c(
        "¿Por qué copiar árboles antes de cruzar o mutar?",
        [
          "Para aumentar siempre MSE",
          "Para evitar modificar padres o élites por referencias compartidas",
          "Para convertirlos en cadenas binarias",
          "Para eliminar operadores unarios",
        ],
        1,
        "Si dos individuos comparten nodos mutables, cambiar un hijo puede alterar también al padre o la élite. Copias inmutables evitan esa corrupción.",
        "Inmutabilidad",
      ),
      c(
        "Regeneración de rama significa…",
        [
          "Invertir dos hijos solamente",
          "Reemplazar un subárbol por otro generado, respetando presupuesto de altura",
          "Cambiar únicamente el peso de selección",
          "Añadir siempre una raíz nueva",
        ],
        1,
        "Se selecciona una rama y se sustituye por otra estructura. El presupuesto restante depende de la profundidad del punto de inserción.",
        "Regeneración",
      ),
    ],
    8: () => [
      o(
        "Ordena las operaciones de una generación tras crear población.",
        [
          "Cruzar y mutar",
          "Evaluar población",
          "Seleccionar padres",
          "Reparar descendientes y evaluarlos",
          "Copiar élites y construir siguiente población",
        ],
        "2,3,1,4,5",
        "Primero se necesitan errores para seleccionar. Luego se crean hijos, se validan/reparan y se evalúan. Élites y descendientes forman la siguiente población.",
        "Ciclo",
      ),
      c(
        "¿Qué diferencia archivo histórico y elitismo generacional?",
        [
          "Ninguna",
          "El archivo registra mejores; elitismo los copia a la población siguiente",
          "El archivo siempre se cruza",
          "Elitismo no conserva individuos",
        ],
        1,
        "Guardar un mejor histórico para consultar no garantiza su presencia en la siguiente población. Elitismo sí inserta copias de los mejores.",
        "Elitismo",
      ),
      n(
        `Población de ${k * 4}, con ${k} élites. ¿Cuántas plazas quedan para descendientes?`,
        k * 3,
        `El tamaño total se mantiene: ${k * 4}−${k}=${k * 3}. Las élites ocupan plazas, no se agregan por encima del límite.`,
        "Reemplazo",
      ),
      c(
        "Sin elitismo, el mejor MSE de la población…",
        [
          "Nunca puede empeorar",
          "Puede empeorar entre generaciones aunque el archivo histórico mejore o se mantenga",
          "Siempre es cero",
          "Es igual al promedio",
        ],
        1,
        "Selección y variación pueden perder al mejor individuo. El archivo registra el mejor pasado, pero no garantiza conservarlo en la población actual.",
        "Histórico y población",
      ),
      c(
        "¿Qué condición de parada es defendible?",
        [
          "Solo una expresión igual a la oculta",
          "Presupuesto máximo o error objetivo declarado, con control de estancamiento",
          "Un botón que inventa una solución",
          "MSE menor que cero",
        ],
        1,
        "La búsqueda necesita límites de tiempo o generaciones y objetivos verificables. Puede detenerse sin encontrar error cero ni la expresión original.",
        "Parada",
      ),
      c(
        "¿Qué error tiene este fragmento si se pretende elitismo?",
        [
          "El mejor se guarda fuera, pero no se copia a nueva población",
          "Seleccionar padres está prohibido",
          "No hay error",
          "El archivo debe contener datos CSV",
        ],
        0,
        "La asignación a historico solo registra una solución. Para elitismo se debe insertar una copia del mejor en nueva antes de completar plazas con hijos.",
        "Código evolutivo",
        "historico = min(poblacion, key=lambda i: i.mse)\nnueva = generar_hijos(poblacion, N)\npoblacion = nueva",
      ),
      c(
        "El mejor MSE baja y el promedio sube. ¿Es posible?",
        [
          "No, es contradicción",
          "Sí, un buen individuo puede coexistir con muchos descendientes malos",
          "Solo si MSE negativo",
          "Significa R²=1",
        ],
        1,
        "El mínimo describe a un individuo; el promedio describe toda la población. Una mejora del mejor no obliga a mejorar el promedio.",
        "Estadísticas",
      ),
      c(
        "¿Qué información puede recibir el buscador para evitar una solución oculta?",
        [
          "La fórmula objetivo como plantilla exacta",
          "Pares x,y, biblioteca y configuración; sin acceso a la fórmula generadora",
          "Solo la curva ya resuelta",
          "La respuesta del examen",
        ],
        1,
        "La regresión simbólica busca a partir de observaciones y su espacio de expresiones. Inyectar la fórmula conocida como candidato sesga y falsea el descubrimiento.",
        "Laboratorio",
      ),
      c(
        "Verdadero o falso: la población evaluada puede reutilizar el error del padre después de mutarlo.",
        [
          "Verdadero, comparten genotipo",
          "Falso: cambiar expresión exige volver a evaluarla en los datos",
          "Verdadero si Pm<1",
          "Falso porque MSE no es numérico",
        ],
        1,
        "Una mutación cambia las predicciones y potencialmente el MSE. Solo las copias idénticas y bajo el mismo conjunto de datos pueden reutilizar evaluación.",
        "Evaluación de hijos",
      ),
      c(
        "¿Cuál interpretación de una ejecución con semilla fija es correcta?",
        [
          "Garantiza óptimo global",
          "Permite reproducir decisiones pseudoaleatorias bajo misma implementación y datos",
          "Elimina la necesidad de validar",
          "Garantiza recuperar coseno",
        ],
        1,
        "Una semilla controla el generador pseudoaleatorio. Ayuda a reproducir y depurar; no garantiza calidad, unicidad ni generalización.",
        "Reproducibilidad",
      ),
    ],
  };
  const draft =
    index >= 10
      ? advancedDraft(unit, index - 10, variant)
      : units[unit]()[index];
  if (draft.type === "choice" || draft.type === "order") {
    const rng = seeded(variant + unit * 1009 + index * 71);
    const entries = draft.options!.map((text, i) => ({ text, original: i }));
    for (let j = entries.length - 1; j > 0; j--) {
      const t = Math.floor(rng() * (j + 1));
      [entries[j], entries[t]] = [entries[t], entries[j]];
    }
    draft.options = entries.map((e) => e.text);
    draft.answer =
      draft.type === "choice"
        ? String(entries.findIndex((e) => e.original === Number(draft.answer)))
        : draft.answer
            .split(",")
            .map(
              (v) => entries.findIndex((e) => e.original === Number(v) - 1) + 1,
            )
            .join(",");
  }
  return {
    ...draft,
    id: `u${unit}-q${index}-v${variant}`,
    revision: 1,
    unit,
    original: index,
  };
}
export const bank: Question[] = Array.from({ length: 8 }, (_, u) =>
  Array.from({ length: 10 + advancedCounts[u] }, (_, i) =>
    makeQuestion(u + 1, i),
  ),
).flat();
