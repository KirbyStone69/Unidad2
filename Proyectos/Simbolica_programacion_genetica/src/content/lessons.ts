export interface Section {
  title: string;
  text: string;
  example: string;
  formula?: string;
  check: string;
  answer: string;
}
export interface Lesson {
  id: number;
  title: string;
  short: string;
  intro: string;
  duration: string;
  objectives: string[];
  sections: Section[];
  summary: string[];
}
export const lessons: Lesson[] = [
  {
    id: 1,
    title: "Heurísticas y problema inverso",
    short: "De los datos a una función",
    duration: "20 min",
    intro:
      "Sabemos programar una función y calcular su resultado. Ahora vamos al revés: vemos los resultados e intentamos descubrir una expresión que los explique.",
    objectives: [
      "Distinguir problema directo e inverso",
      "Reconocer qué busca la regresión simbólica",
      "Entender las posibilidades y límites de una heurística",
    ],
    sections: [
      {
        title: "Buscar sin recorrerlo todo",
        text: "Una heurística es una estrategia práctica para encontrar buenas soluciones con recursos limitados. Una búsqueda exacta pretende demostrar una respuesta correcta u óptima bajo sus condiciones; una heurística normalmente no ofrece esa garantía. Un algoritmo genético evoluciona una población mediante selección y variación.",
        example:
          "Si hay millones de expresiones, podemos evaluar algunas, conservar candidatos prometedores y crear otros. Encontrar una expresión buena no demuestra que sea la mejor de todas.",
        check:
          "¿El mejor de 100 candidatos es necesariamente el óptimo global?",
        answer:
          "No. Solo sabemos que fue el mejor de los candidatos evaluados.",
      },
      {
        title: "Directo e inverso",
        text: "En el problema directo conocemos la regla y calculamos salidas. En el inverso conocemos observaciones y buscamos una regla. Puede haber muchas reglas compatibles con los mismos datos.",
        example:
          "Directo: f(x)=x², x=3 → y=9. Inverso: (1,1), (2,4), (3,9) → x² es una candidata. Pero x²+a(x−1)(x−2)(x−3) coincide también en esos tres puntos.",
        formula: String.raw`f(3)=3^2=9`,
        check: "¿Tres puntos demuestran que la regla original era x²?",
        answer:
          "No: muestran compatibilidad en las muestras. Necesitamos más datos, validación y supuestos de dominio.",
      },
      {
        title: "De AG a programación genética",
        text: "En un AG clásico podemos usar cadenas binarias para codificar parámetros. En PG de árboles el individuo es una expresión o programa de estructura variable. Regresión simbólica aplica esta búsqueda para proponer funciones que ajustan datos, buscando estructura y constantes.",
        example:
          "Ajustar a y b en ax+b mantiene una forma fija. Comparar ax+b con sin(x), x² y log(x+2) explora estructuras diferentes.",
        check: "¿Optimizar solo a y b busca la estructura de la ecuación?",
        answer: "No. Optimiza parámetros de una estructura ya elegida.",
      },
      {
        title: "Data-Driven Modeling",
        text: "DDM construye modelos a partir de datos. Revisamos su calidad, separamos entrenamiento y validación, ajustamos y comprobamos predicciones. Una expresión interpretable puede sugerir conocimiento, pero no prueba causalidad por sí sola.",
        example:
          "Un árbol grande puede memorizar entrenamiento. Si falla en puntos reservados, su bajo error de entrenamiento no basta para defenderlo.",
        check: "¿Qué aporta un conjunto de validación?",
        answer:
          "Permite evaluar el modelo con observaciones no usadas para ajustarlo y detectar indicios de sobreajuste.",
      },
    ],
    summary: [
      "PG evoluciona expresiones; regresión simbólica busca funciones a partir de datos.",
      "Una heurística no garantiza óptimo global.",
      "Ajustar muestras no equivale a descubrir una ley única.",
    ],
  },
  {
    id: 2,
    title: "Árboles de expresión",
    short: "La anatomía de una fórmula",
    duration: "25 min",
    intro:
      "Una fórmula también puede ser un árbol. Cada operación conecta sus argumentos y las hojas guardan variables o constantes.",
    objectives: [
      "Identificar raíz, nodos y aristas",
      "Medir tamaño y altura por separado",
      "Construir expresiones respetando aridad",
    ],
    sections: [
      {
        title: "Raíz, hojas y aridad",
        text: "La raíz es el nodo superior. Una arista conecta padre e hijo. Las hojas no tienen hijos: son terminales. Los nodos internos son operadores. Aridad es el número de argumentos: + requiere dos, sqrt requiere uno.",
        example:
          "En +(x,2), + es raíz e interno; x y 2 son hojas. Hay tres nodos y dos aristas.",
        check: "¿sin(x) necesita dos hijos por ser parte de un árbol binario?",
        answer:
          "No. Un árbol binario permite como máximo dos hijos. sin es unario y necesita uno.",
      },
      {
        title: "Una expresión completa",
        text: "La operación exterior determina la raíz. Descomponemos cada argumento hasta llegar a terminales. El árbol es el genotipo codificado; la función expresada y su comportamiento constituyen el fenotipo.",
        example:
          "sqrt(2*x²+5*x−3): raíz sqrt, debajo −, con izquierda +(2*x²,5*x) y derecha 3. La potencia tiene hijos x y 2.",
        formula: String.raw`\sqrt{2x^2+5x-3}`,
        check: "¿Cuál es el operador raíz de esta fórmula?",
        answer: "sqrt, porque se aplica al resultado de todo el radicando.",
      },
      {
        title: "Tamaño no es altura",
        text: "Tamaño cuenta todos los nodos. Altura cuenta aristas de la ruta más larga desde la raíz a una hoja. La raíz está en nivel cero, así que una hoja sola tiene altura cero.",
        example:
          "+(x,*(2,x)) tiene cinco nodos, cuatro aristas y altura dos. Una cadena de altura dos tendría solo tres nodos.",
        formula: String.raw`N_{max}=\sum_{i=0}^{h}2^i=2^{h+1}-1`,
        check: "¿Todo árbol binario de altura 2 tiene 7 nodos?",
        answer:
          "No. Siete es el máximo; un árbol no completo puede contener menos.",
      },
      {
        title: "Validez estructural y matemática",
        text: "Un árbol puede tener aridad correcta y fallar al evaluarse. El editor verifica la estructura; el evaluador comprueba además el dominio para cada entrada.",
        example:
          "sqrt(−1) es estructuralmente correcto pero no tiene valor real. *(x) es estructuralmente incorrecto porque falta un argumento.",
        check: "¿La aridad correcta garantiza un MSE finito?",
        answer:
          "No. Puede haber división por cero, dominios no reales o desbordamiento en alguna muestra.",
      },
    ],
    summary: [
      "Terminales: cero hijos; operadores: tantos hijos como su aridad.",
      "Altura se mide en aristas; tamaño cuenta nodos.",
      "El máximo binario es una cota, no una igualdad universal.",
    ],
  },
  {
    id: 3,
    title: "Recorridos y evaluación",
    short: "Lee y ejecuta un árbol",
    duration: "25 min",
    intro:
      "El mismo árbol puede recorrerse en distintos órdenes. Para evaluar necesitamos que cada operador reciba antes el valor de sus hijos.",
    objectives: [
      "Aplicar preorder, inorder y postorder",
      "Evaluar expresiones paso a paso",
      "Detectar errores de orden de operandos",
    ],
    sections: [
      {
        title: "Tres órdenes",
        text: "Preorder: raíz, izquierda, derecha. Inorder: izquierda, raíz, derecha. Postorder: izquierda, derecha, raíz. En nodos unarios recorremos su único hijo en la posición correspondiente.",
        example:
          "Para +(x,*(2,3)): pre = + x * 2 3; in = x + 2 * 3; post = x 2 3 * +.",
        check: "¿En qué orden aparece la raíz al final?",
        answer: "En postorder: antes se recorren todos sus descendientes.",
      },
      {
        title: "La agrupación importa",
        text: "Un inorder sin paréntesis no siempre identifica la estructura de la expresión. Para escribir notación infija fiel debemos conservar agrupación y precedencia.",
        example:
          "+(x,*(2,3)) y *(+(x,2),3) pueden dar los mismos tokens inorder x + 2 * 3, aunque sus resultados difieren.",
        check:
          "¿Basta una secuencia inorder sin paréntesis para reconstruir siempre el árbol?",
        answer:
          "No. Puede ser ambigua; se necesita información adicional de estructura.",
      },
      {
        title: "Evaluar de abajo hacia arriba",
        text: "Postorder visita los operandos antes de su operador. Podemos usar una pila: apilar terminales; al encontrar un operador, extraer sus argumentos, calcular y apilar el resultado.",
        example:
          "Con x=4 en (x+2)*(x−3): x+2=6; x−3=1; 6*1=6. En resta se extrae primero el derecho y luego el izquierdo, pero se calcula izquierdo−derecho.",
        formula: String.raw`(4+2)(4-3)=6\cdot1=6`,
        check: "En la pila [8,3], ¿qué resultado deja el operador −?",
        answer: "5. Se extrae derecho=3 e izquierdo=8 y se calcula 8−3.",
      },
      {
        title: "El recorrido no corrige el dominio",
        text: "El evaluador debe detener o penalizar un candidato cuando una operación no está definida en reales. Cambiar de recorrido no soluciona la restricción.",
        example:
          "sqrt(x−3) para x=2: primero 2−3=−1; después sqrt(−1) falla en reales.",
        check: "¿Se puede omitir esa muestra para bajar MSE?",
        answer:
          "No silenciosamente. Eso cambiaría el conjunto de evaluación y favorecería injustamente al candidato.",
      },
    ],
    summary: [
      "Preorder empieza por raíz; postorder termina por raíz.",
      "Postorder facilita evaluación con dependencias resueltas.",
      "Resta, división y potencia dependen del orden de argumentos.",
    ],
  },
  {
    id: 4,
    title: "Operaciones y generación",
    short: "Define el espacio de búsqueda",
    duration: "25 min",
    intro:
      "La biblioteca determina qué funciones puede construir el algoritmo. Debemos registrar aridades, dominios y límites de crecimiento.",
    objectives: [
      "Reconocer dominios de once operadores",
      "Generar árboles con altura acotada",
      "Distinguir operadores ordinarios y protegidos",
    ],
    sections: [
      {
        title: "Biblioteca de primitivas",
        text: "Suma, resta, multiplicación, división, módulo y potencia son binarias. Raíz, logaritmo natural, seno, coseno y tangente son unarias. Las constantes y x son terminales.",
        example:
          "+(sin(x),2) es válido: + tiene dos hijos y sin tiene uno. sin(x,2) es inválido.",
        check: "¿Cuántos hijos necesita potencia?",
        answer: "Dos: base y exponente.",
      },
      {
        title: "Dominios reales",
        text: "División y módulo requieren divisor distinto de cero. sqrt requiere argumento ≥0; log requiere argumento >0. Potencias pueden no ser reales; tan tiene polos en π/2+kπ. También rechazamos resultados no finitos. Los ángulos se expresan en radianes. En este motor, % calcula resto con signo del dividendo (puede diferir del % de Python para negativos); se adopta la convención 0^0=1.",
        example:
          "log(1)=0; log(0) no está definido. sqrt(0)=0; sqrt(−1) no es real. (−1)^0.5 tampoco es real.",
        check: "¿sqrt(0) y log(0) tienen la misma restricción?",
        answer: "No. sqrt admite cero; log no.",
      },
      {
        title: "Generar una estructura aleatoria",
        text: "Elegimos terminal u operador. Si elegimos operador, generamos tantos hijos como su aridad. En la profundidad máxima debemos terminar con terminales. Full expande operadores hasta el límite; grow permite terminar antes.",
        example:
          "Máximo h=2: raíz + en nivel 0, sin y * en nivel 1, solo terminales en nivel 2. La altura real puede ser menor usando grow.",
        check: "¿Qué debemos colocar en nivel h?",
        answer:
          "Un terminal. Un operador con hijos excedería la altura máxima.",
      },
      {
        title: "Semántica protegida",
        text: "Algunas implementaciones definen valores especiales fuera del dominio para mantener clausura. Eso cambia la operación y debe declararse. Este laboratorio usa semántica ordinaria y penaliza candidatos inválidos.",
        example:
          "División protegida que devuelve 1 al dividir por cero no es idéntica a la división ordinaria. No debemos interpretar su árbol como una fracción convencional sin aclaración.",
        check: "¿Un candidato inválido debe recibir error cero?",
        answer:
          "No. Se penaliza; error cero significaría ajuste perfecto y lo favorecería.",
      },
    ],
    summary: [
      "La biblioteca limita el espacio de funciones posibles.",
      "Aridad correcta no evita errores de dominio.",
      "En profundidad máxima se generan hojas.",
    ],
  },
  {
    id: 5,
    title: "CSV, MSE, NMSE y R²",
    short: "Mide el ajuste con precisión",
    duration: "35 min",
    intro:
      "Tenemos valores reales y predicciones. Construiremos cada métrica a partir de residuos para entender qué mide y cuándo no está definida.",
    objectives: [
      "Calcular residuos y sumas",
      "Interpretar MSE, NMSE y R²",
      "Tratar denominadores cero sin inventar resultados",
    ],
    sections: [
      {
        title: "De una fila al error total",
        text: "y es la observación real y ŷ es la predicción. El residuo es y−ŷ. Su cuadrado evita cancelaciones de signos y penaliza errores grandes. SSE suma los errores cuadrados.",
        example:
          "y=[1,2,3], ŷ=[1,1,2]: residuos [0,1,1], cuadrados [0,1,1]. SSE=2 y n=3.",
        formula: String.raw`MSE=\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2`,
        check: "¿El promedio de residuos equivale al MSE?",
        answer:
          "No. Los residuos pueden cancelarse; MSE promedia residuos cuadrados.",
      },
      {
        title: "MSE y NMSE",
        text: "MSE tiene unidades de y al cuadrado. Ideal cero; menor es mejor. El NMSE de este curso divide SSE por energía Σy²; no por varianza. Ambas métricas pueden superar uno.",
        example:
          "En el ejemplo anterior, MSE=2/3 y Σy²=1+4+9=14. NMSE=2/14=1/7. Si todos los y son cero, este NMSE no está definido.",
        formula: String.raw`NMSE=\frac{\sum_i(y_i-\hat y_i)^2}{\sum_i y_i^2}`,
        check: "¿NMSE está siempre entre 0 y 1?",
        answer: "No. Puede superar 1 si SSE es mayor que Σy².",
      },
      {
        title: "Comparar con la media",
        text: "ȳ es el promedio de valores reales. SST suma sus desviaciones cuadradas. R² compara SSE con SST. Ideal 1 y cuanto mayor, mejor. Puede ser negativo cuando el modelo es peor que predecir ȳ.",
        example: "y=[1,3], ȳ=2, SST=2. Si ŷ=[4,4], SSE=9+1=10; R²=1−10/2=−4.",
        formula: String.raw`R^2=1-\frac{\sum_i(y_i-\hat y_i)^2}{\sum_i(y_i-\bar y)^2}`,
        check: "¿Qué ocurre con y=[2,2]?",
        answer:
          "SST=0: la fórmula de R² queda indefinida, incluso si las predicciones son perfectas.",
      },
      {
        title: "Un buen ajuste no demuestra identidad",
        text: "R²=1 con SST positivo implica SSE=0 en las muestras. No garantiza recuperar la expresión original, ni validez fuera del dominio observado. CSV debe contener pares numéricos finitos y una importación verificable.",
        example:
          "Dos expresiones diferentes pueden coincidir en todas las filas del CSV y divergir entre ellas. Reservar datos y analizar complejidad ayuda a comparar modelos.",
        check:
          "¿Es correcto eliminar sin avisar las filas que una expresión no puede evaluar?",
        answer:
          "No. Las candidatas deben compararse sobre el mismo conjunto de muestras.",
      },
    ],
    summary: [
      "MSE=SSE/n; NMSE=SSE/Σy² según la convención del curso.",
      "R²=1−SSE/SST y puede ser negativo.",
      "Denominador cero significa métrica indefinida.",
    ],
  },
  {
    id: 6,
    title: "Población y selección",
    short: "Da oportunidades a los mejores",
    duration: "30 min",
    intro:
      "Tenemos dos árboles con MSE 0.2 y 0.8. Como minimizamos el error, el primero es mejor. Veamos cómo darle más oportunidades de reproducción.",
    objectives: [
      "Evaluar poblaciones de funciones",
      "Aplicar torneo, ruleta y SUS",
      "Transformar error en aptitud",
    ],
    sections: [
      {
        title: "Una población de programas",
        text: "El individuo ya no es necesariamente una cadena binaria: es un árbol que produce una función. Podemos generar 100 árboles y calcular el MSE de cada uno en los mismos datos.",
        example:
          "A=x², B=x+1 y C=sin(x) producen predicciones distintas. Su posición en la población no determina su calidad; la evaluación sí.",
        check: "¿Podemos reutilizar el MSE después de cambiar una rama?",
        answer: "No. La función cambia y debe volver a evaluarse.",
      },
      {
        title: "Torneo binario",
        text: "Se eligen dos participantes y gana quien tenga menor MSE. Repetimos para obtener los padres necesarios. Hay azar al elegir participantes, no al comparar sus errores, salvo empates.",
        example:
          "A:0.2 frente a B:0.8 → gana A. Si el mejor global no participa en un torneo concreto, otro individuo puede ganar ese torneo.",
        check: "¿El torneo siempre devuelve al mejor de toda la población?",
        answer: "No. Devuelve al mejor entre sus participantes.",
      },
      {
        title: "Ruleta: transformar primero",
        text: "Un peso de reproducción debe aumentar cuando el candidato es mejor. Usar MSE directamente haría lo contrario. Para errores finitos no negativos usamos w=1/(1+MSE) y después normalizamos.",
        example:
          "MSE=[0,3] → w=[1,0.25] → suma=1.25 → p=[0.8,0.2]. El individuo perfecto tiene gran oportunidad, pero no selección garantizada.",
        formula: String.raw`w_i=\frac{1}{1+MSE_i},\qquad p_i=\frac{w_i}{\sum_jw_j}`,
        check: "¿w_i ya es una probabilidad?",
        answer:
          "No necesariamente. Debe dividirse por la suma de pesos de toda la población.",
      },
      {
        title: "Muestreo estocástico universal",
        text: "SUS usa un único desplazamiento aleatorio y varios punteros equiespaciados sobre la distribución acumulada. La distancia es 1/m para m selecciones; reduce variación en los conteos respecto a sorteos independientes.",
        example:
          "Para cuatro selecciones y desplazamiento 0.05, punteros 0.05,0.30,0.55,0.80. Cada uno selecciona el intervalo acumulado donde cae.",
        check:
          "¿SUS exige cuatro números aleatorios independientes para cuatro selecciones?",
        answer: "No. Usa un desplazamiento y separaciones fijas.",
      },
    ],
    summary: [
      "Error se minimiza; aptitud de selección se maximiza.",
      "Torneo compara participantes, ruleta usa probabilidades.",
      "SUS usa un origen aleatorio y punteros equiespaciados.",
    ],
  },
  {
    id: 7,
    title: "Cruce, mutación y reparación",
    short: "Transforma árboles sin romperlos",
    duration: "40 min",
    intro:
      "Los padres aportan fragmentos de programas. Al intercambiar o modificar ramas podemos explorar funciones nuevas, manteniendo estructura y límites explícitos.",
    objectives: [
      "Realizar cruce por aristas",
      "Distinguir cuatro mutaciones",
      "Aplicar Pm y reparar altura",
    ],
    sections: [
      {
        title: "Cruce de subárboles",
        text: "Elegimos una arista en cada padre y separamos el subárbol que cuelga de ella. Intercambiamos esas ramas, conservando el resto de cada contexto. El cruce de este curso no corta por encima de la raíz.",
        example:
          "P1=+(x,2), P2=*(3,4). Cortamos hacia 2 y 3. Hijos: +(x,3) y *(2,4). No se alteran los padres originales.",
        check: "¿Se intercambia siempre una sola hoja?",
        answer:
          "No. Un subárbol puede ser una hoja o contener muchos operadores y terminales.",
      },
      {
        title: "Cuatro mutaciones",
        text: "Terminal cambia una hoja. Operador cambia una operación, preferentemente con igual aridad. Switching intercambia hijos izquierdo y derecho. Regeneración elimina una rama y genera otra.",
        example:
          "Terminal: 3→3.2 o x. Operador: +→−. Switching: x−3→3−x. Regeneración: (x+2)→sin(x*x).",
        check: "¿Switching cambia siempre el valor de la función?",
        answer:
          "No. Intercambiar argumentos de + o * conserva su valor por conmutatividad; en − o / puede cambiarlo.",
      },
      {
        title: "Cambiar aridad y decidir si mutar",
        text: "Primero sorteamos si ocurre mutación con Pm. Solo si ocurre elegimos su tipo mediante pesos normalizados. Cambiar binario a unario exige eliminar un hijo elegido; el cambio inverso exige generar otro.",
        example:
          "Pm=0.2 y tipo switching con peso relativo 1/4: probabilidad total 0.2×0.25=0.05. Renombrar +(x,2) como sin sin eliminar un hijo sería inválido.",
        formula: String.raw`P(\text{tipo }j)=P_m\,P(j\mid\text{mutación})`,
        check: "¿La ruleta del tipo reemplaza el sorteo de Pm?",
        answer: "No. Son dos decisiones diferentes.",
      },
      {
        title: "Reparación de altura",
        text: "Cruce y regeneración pueden superar altura máxima. Por poda convertimos nodos internos del nivel límite en terminales. Alternativamente rechazamos y repetimos con límite de intentos; si falla, conservamos un padre válido.",
        example:
          "Máximo h=2: cualquier nodo interno en profundidad 2 se convierte en x; así no tiene hijos en profundidad 3. La reparación cambia la expresión, por eso se reevalúa.",
        check: "¿Reducir el MSE guardado repara un árbol demasiado alto?",
        answer:
          "No. La restricción es estructural y requiere cambiar el árbol o rechazarlo.",
      },
    ],
    summary: [
      "Cruce intercambia subárboles entre dos individuos.",
      "Mutación puede modificar contenido, operación, orden o rama.",
      "Reparar exige volver a evaluar; un historial no justifica un árbol inválido.",
    ],
  },
  {
    id: 8,
    title: "Ciclo evolutivo completo",
    short: "De una generación a la siguiente",
    duration: "30 min",
    intro:
      "Unimos las piezas: generar, evaluar, seleccionar, variar y reemplazar. Ahora podemos seguir ocho individuos y observar qué sucede en cada generación.",
    objectives: [
      "Ordenar las fases del ciclo",
      "Distinguir elitismo y archivo histórico",
      "Interpretar progreso sin prometer convergencia",
    ],
    sections: [
      {
        title: "El ciclo",
        text: "Generamos la población y evaluamos sus árboles. Elegimos padres, cruzamos ramas, sorteamos mutación, reparamos cuando haga falta y evaluamos hijos. Copiamos élites y completamos el tamaño previsto de la siguiente población.",
        example:
          "Con N=8 y una élite, conservamos el mejor padre y creamos siete descendientes válidos. Luego repetimos el proceso sobre esa población nueva.",
        check: "¿Podemos seleccionar por MSE antes de evaluar?",
        answer:
          "No de forma informada. Primero necesitamos el error de cada candidato.",
      },
      {
        title: "Élite no es archivo",
        text: "Elitismo generacional copia individuos excelentes a la población siguiente. Un archivo histórico solo registra mejores soluciones observadas, aunque ya no estén en la población. Son mecanismos distintos.",
        example:
          "Guardar mejor_historico en una variable no protege al individuo del reemplazo. Debemos insertar una copia en nueva_poblacion para tener elitismo.",
        check: "Sin élites, ¿puede empeorar el mejor de la población?",
        answer:
          "Sí. El archivo histórico puede conservar la mejor solución pasada mientras la población actual empeora.",
      },
      {
        title: "Leer las curvas",
        text: "El mejor MSE es un mínimo; el promedio resume todos los individuos. Pueden moverse en direcciones distintas. Bajo datos fijos, evaluación determinista y elitismo, el mejor error no debe empeorar entre generaciones.",
        example:
          "Población antes [1,2,3], después [0.5,10,10]: mejora el mejor, pero el promedio empeora. Candidatos inválidos se cuentan aparte del promedio finito.",
        check:
          "¿Una curva que mejora prueba que encontramos la ecuación original?",
        answer:
          "No. Prueba mejora de la métrica en esos datos y bajo ese presupuesto.",
      },
      {
        title: "Parada y reproducibilidad",
        text: "Se detiene por presupuesto, error objetivo o estancamiento declarado. Una semilla permite repetir decisiones pseudoaleatorias con mismos datos y configuración. No es garantía de óptimo ni de generalización.",
        example:
          "En el laboratorio usamos puntos del CSV como única señal de ajuste. La fórmula generadora no entra en el buscador ni se añade como solución oculta.",
        check: "¿Es un fallo terminar con MSE positivo?",
        answer:
          "No necesariamente. La búsqueda es heurística y su presupuesto es limitado; debemos reportar el resultado real.",
      },
    ],
    summary: [
      "La evaluación conecta todas las fases.",
      "Elitismo inserta copias; archivo solo recuerda.",
      "La búsqueda puede terminar sin recuperar una expresión exacta.",
    ],
  },
];
