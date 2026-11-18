"""Adaptación detallada del apéndice B de «Algoritmos evolutivos: un enfoque práctico».

Conserva las estructuras, flujo y operadores del C++ de las páginas 296-316:
población, cromosomas binarios (bit menos significativo primero), genotipo,
fenotipo, aptitud, aptitud_bruta, puntuacion, punt_acu, elite, ruleta,
cruce, mutación y evaluación.

Solo usa math y random de la biblioteca estándar; no usa paquetes de AG.

Uso:
    python3 algoritmo_genetico_completo.py max
    python3 algoritmo_genetico_completo.py min
    python3 algoritmo_genetico_completo.py varias
    python3 algoritmo_genetico_completo.py max 0 32 0.0001 500 1000 0.4 0.001
    python3 algoritmo_genetico_completo.py min -250 250 0.001 100 200 0.4 0.001

Los parámetros siguen el orden del libro: x_min x_max TOL tam_pob num_gen
prob_cruce prob_mut. Para 'varias', se usan rangos y precisiones por variable.
"""
import math
import random
import sys


# La versión original usa vectores de bool, double, float e int. Aquí, listas.
# El número de variables de la función multivariable es configurable.
NUM_VAR = 3


class TIndividuo:
    """Equivale a struct TIndividuo del C++."""
    def __init__(self):
        self.genes = []             # Vector binario para una variable
        self.vec_genes = []         # Vector de vectores binarios para n variables
        self.x = None               # Fenotipo de una variable
        self.vec_x = []             # Vector de fenotipos de n variables
        self.aptitud = 0.0         # Adaptación para la ruleta
        self.aptitud_bruta = 0.0   # Función original (modo mínimo / varias)
        self.puntuacion = 0.0      # Probabilidad relativa
        self.punt_acu = 0.0        # Probabilidad acumulada
        self.elite = False         # Pertenencia al 2 % de élite


def copiar_indiv(origen):
    """En C++ vector<TIndividuo> copia el individuo por valor; emulamos eso."""
    nuevo = TIndividuo()
    nuevo.genes = origen.genes[:]
    nuevo.vec_genes = [genes[:] for genes in origen.vec_genes]
    nuevo.x = origen.x
    nuevo.vec_x = origen.vec_x[:]
    nuevo.aptitud = origen.aptitud
    nuevo.aptitud_bruta = origen.aptitud_bruta
    nuevo.puntuacion = origen.puntuacion
    nuevo.punt_acu = origen.punt_acu
    nuevo.elite = origen.elite
    return nuevo


# ---------------------------------------------------------------
# Decodificación: las cadenas binarias se guardan en orden LSB.
# ---------------------------------------------------------------
def bin_dec(genes, lcrom):
    d = 0
    pot = 1
    for i in range(lcrom):
        d = d + pot * int(genes[i])
        pot = pot * 2
    return d


def decod(genes, lcrom, x_min, x_max):
    # x = xmin + valor_binario * (xmax - xmin) / (2**lcrom - 1)
    return x_min + (bin_dec(genes, lcrom) / (2 ** lcrom - 1)) * (x_max - x_min)


def longitud_cromosoma(x_min, x_max, tol):
    if x_max <= x_min or tol <= 0:
        raise ValueError('Se requiere x_max > x_min y TOL > 0')
    return max(1, math.ceil(math.log2(1 + (x_max - x_min) / tol)))


# ---------------------------------------------------------------
# Adaptación: las funciones EXACTAS que aparecen en el libro.
# ---------------------------------------------------------------
def adaptacion(individuo, lcrom, x_min, x_max, modo):
    if modo == 'varias':
        individuo.vec_x = []
        for i in range(len(lcrom)):
            individuo.vec_x.append(decod(individuo.vec_genes[i], lcrom[i], x_min[i], x_max[i]))
        f = 0.0
        for x in individuo.vec_x:
            f = f - x * math.sin(math.sqrt(abs(x)))
        return f

    x = decod(individuo.genes, lcrom, x_min, x_max)
    individuo.x = x
    if modo == 'max':
        # Libro, p. 301: f(x) = 20 + exp(1) - 20*exp(-0.2*abs(x)) - exp(cos(2*pi*x))
        return 20 + math.exp(1) - 20 * math.exp(-0.2 * abs(x)) - math.exp(math.cos(2 * math.pi * x))
    if modo == 'min':
        # Libro, p. 309: f(x) = -abs(x*sin(sqrt(abs(x))))
        return -(abs(x * math.sin(math.sqrt(abs(x)))))
    raise ValueError('Modo desconocido')


# ---------------------------------------------------------------
# Generación inicial (poblacion_inicial y genera_indiv en C++).
# ---------------------------------------------------------------
def genera_indiv(lcrom, x_min, x_max, modo):
    indiv = TIndividuo()
    if modo == 'varias':
        for longitud in lcrom:
            genes = []
            for _ in range(longitud):
                genes.append(0 if random.random() < 0.5 else 1)
            indiv.vec_genes.append(genes)
    else:
        for _ in range(lcrom):
            indiv.genes.append(0 if random.random() < 0.5 else 1)
    resultado = adaptacion(indiv, lcrom, x_min, x_max, modo)
    if modo == 'max':
        indiv.aptitud = resultado
    else:
        indiv.aptitud_bruta = resultado
    return indiv


def poblacion_inicial(tam_pob, lcrom, x_min, x_max, modo):
    pob = []
    for _ in range(tam_pob):
        pob.append(genera_indiv(lcrom, x_min, x_max, modo))
    return pob


# ---------------------------------------------------------------
# Transformación de aptitud para minimizar (revisar_adap_mini).
# Libro, p. 306-307: cmax = max(aptitud_bruta) * 1.01
# y aptitud = cmax - aptitud_bruta.
# ---------------------------------------------------------------
def revisar_adap_mini(pob):
    cmax = pob[0].aptitud_bruta
    for individuo in pob[1:]:
        if individuo.aptitud_bruta > cmax:
            cmax = individuo.aptitud_bruta
    cmax = cmax + cmax / 100
    for individuo in pob:
        individuo.aptitud = cmax - individuo.aptitud_bruta

    # La transformación del libro tiene un problema cuando cmax < 0:
    # algunas aptitudes pueden ser negativas. La ruleta requiere pesos
    # no negativos: desplazamos toda la población sin alterar su orden.
    inferior = min(indiv.aptitud for indiv in pob)
    if inferior <= 0:
        for indiv in pob:
            indiv.aptitud = indiv.aptitud - inferior + 1e-12


# ---------------------------------------------------------------
# Evaluación: mejor individuo, suma, puntuación y puntuación acumulada.
# ---------------------------------------------------------------
def evaluacion(pob):
    tam_pob = len(pob)
    sumaptitud = 0.0
    pos_mejor = 0
    aptitud_mejor = pob[0].aptitud
    for i in range(tam_pob):
        sumaptitud += pob[i].aptitud
        if pob[i].aptitud > aptitud_mejor:
            pos_mejor = i
            aptitud_mejor = pob[i].aptitud

    punt_acu = 0.0
    for i in range(tam_pob):
        pob[i].puntuacion = pob[i].aptitud / sumaptitud if sumaptitud > 0 else 1 / tam_pob
        pob[i].punt_acu = pob[i].puntuacion + punt_acu
        punt_acu += pob[i].puntuacion
    pob[-1].punt_acu = 1.0  # Evita fallos por redondeo de coma flotante
    return pos_mejor, sumaptitud


# ---------------------------------------------------------------
# Selección por ruleta + elitismo de 2 %.
# ---------------------------------------------------------------
def seleccion(pob):
    tam_pob = len(pob)
    tam_elite = tam_pob * 2 // 100
    sel_elite = []
    for i in range(tam_pob):
        pob[i].elite = False
        posicion = 0
        while posicion < len(sel_elite) and pob[sel_elite[posicion]].aptitud >= pob[i].aptitud:
            posicion += 1
        if posicion < tam_elite:
            sel_elite.insert(posicion, i)
            if len(sel_elite) > tam_elite:
                sel_elite.pop()
    for indice in sel_elite:
        pob[indice].elite = True

    sel_super = []
    for i in range(tam_pob):
        if pob[i].elite:
            sel_super.append(i)
        else:
            prob = random.random()
            pos_super = 0
            while pos_super < tam_pob - 1 and prob > pob[pos_super].punt_acu:
                pos_super += 1
            sel_super.append(pos_super)

    # Copias independientes, como push_back en std::vector de structs.
    pob_aux = []
    for indice in sel_super:
        pob_aux.append(copiar_indiv(pob[indice]))
    pob[:] = pob_aux


# ---------------------------------------------------------------
# Cruce de un punto (cruce) y reproducción (reproduccion).
# ---------------------------------------------------------------
def cruce(padre1, padre2, lcrom, punto_cruce, x_min, x_max, modo):
    hijo1 = TIndividuo()
    hijo2 = TIndividuo()
    if modo == 'varias':
        for j in range(len(lcrom)):
            corte = punto_cruce[j]
            hijo1.vec_genes.append(padre1.vec_genes[j][:corte] + padre2.vec_genes[j][corte:])
            hijo2.vec_genes.append(padre2.vec_genes[j][:corte] + padre1.vec_genes[j][corte:])
    else:
        hijo1.genes = padre1.genes[:punto_cruce] + padre2.genes[punto_cruce:]
        hijo2.genes = padre2.genes[:punto_cruce] + padre1.genes[punto_cruce:]

    f1 = adaptacion(hijo1, lcrom, x_min, x_max, modo)
    f2 = adaptacion(hijo2, lcrom, x_min, x_max, modo)
    if modo == 'max':
        hijo1.aptitud = f1
        hijo2.aptitud = f2
    else:
        hijo1.aptitud_bruta = f1
        hijo2.aptitud_bruta = f2
    return hijo1, hijo2


def reproduccion(pob, lcrom, prob_cruce, x_min, x_max, modo):
    sel_cruce = []
    for i in range(len(pob)):
        if random.random() < prob_cruce:
            sel_cruce.append(i)
    if len(sel_cruce) % 2 == 1:
        sel_cruce.pop()

    for i in range(0, len(sel_cruce), 2):
        pos1 = sel_cruce[i]
        pos2 = sel_cruce[i + 1]
        if modo == 'varias':
            puntos = [random.randrange(1, longitud + 2) for longitud in lcrom]
        else:
            # El C++ sortea valores en [1, lcrom+1]. El último da copia idéntica.
            puntos = random.randrange(1, lcrom + 2)
        hijo1, hijo2 = cruce(pob[pos1], pob[pos2], lcrom, puntos, x_min, x_max, modo)

        # El libro reemplaza al padre si mejora O si no forma parte de la élite.
        # En minimización se compara aptitud bruta (menor = mejor).
        for posicion, hijo in ((pos1, hijo1), (pos2, hijo2)):
            if modo == 'max':
                mejora = hijo.aptitud > pob[posicion].aptitud
            else:
                mejora = hijo.aptitud_bruta < pob[posicion].aptitud_bruta
            if mejora or not pob[posicion].elite:
                pob[posicion] = hijo


# ---------------------------------------------------------------
# Mutación bit a bit, salvo los individuos de la élite.
# ---------------------------------------------------------------
def mutacion(pob, lcrom, prob_mut, x_min, x_max, modo):
    for indiv in pob:
        mutado = False
        if modo == 'varias':
            for j in range(len(lcrom)):
                for k in range(lcrom[j]):
                    if random.random() < prob_mut and not indiv.elite:
                        indiv.vec_genes[j][k] = 1 - indiv.vec_genes[j][k]
                        mutado = True
        else:
            for j in range(lcrom):
                if random.random() < prob_mut and not indiv.elite:
                    indiv.genes[j] = 1 - indiv.genes[j]
                    mutado = True
        if mutado:
            valor = adaptacion(indiv, lcrom, x_min, x_max, modo)
            if modo == 'max':
                indiv.aptitud = valor
            else:
                indiv.aptitud_bruta = valor


# ---------------------------------------------------------------
# Bucle principal siguiendo el orden de llamadas del libro.
# ---------------------------------------------------------------
def ejecutar(modo, x_min, x_max, tol, tam_pob, num_gen, prob_cruce, prob_mut, semilla=None):
    if semilla is not None:
        random.seed(semilla)
    if tam_pob < 2 or num_gen < 0:
        raise ValueError('Se requieren al menos 2 individuos y generaciones >= 0')
    if not (0 <= prob_cruce <= 1 and 0 <= prob_mut <= 1):
        raise ValueError('Las probabilidades deben estar entre 0 y 1')
    if modo == 'varias':
        lcrom = []
        for i in range(len(x_min)):
            lcrom.append(longitud_cromosoma(x_min[i], x_max[i], tol[i]))
    else:
        lcrom = longitud_cromosoma(x_min, x_max, tol)

    pob = poblacion_inicial(tam_pob, lcrom, x_min, x_max, modo)
    if modo != 'max':
        revisar_adap_mini(pob)
    pos_mejor, sumaptitud = evaluacion(pob)
    historial = []

    for generacion in range(num_gen):
        seleccion(pob)
        reproduccion(pob, lcrom, prob_cruce, x_min, x_max, modo)
        mutacion(pob, lcrom, prob_mut, x_min, x_max, modo)
        if modo != 'max':
            revisar_adap_mini(pob)
        pos_mejor, sumaptitud = evaluacion(pob)
        mejor = pob[pos_mejor]
        valor = mejor.aptitud if modo == 'max' else mejor.aptitud_bruta
        historial.append(valor)
        print(f'Generación {generacion + 1:4d} | Mejor ({pos_mejor:3d}): {valor:12.6f} | x = {mejor.vec_x if modo == "varias" else mejor.x}')

    return pob, pos_mejor, historial


def main():
    modo = sys.argv[1].lower() if len(sys.argv) > 1 else 'max'
    if modo not in ('max', 'min', 'varias'):
        raise SystemExit('Elige max, min o varias')

    if modo == 'max':
        # Ejemplo exacto de la página 296
        valores = (0.0, 32.0, 0.0001, 500, 1000, 0.4, 0.001)
    elif modo == 'min':
        valores = (-250.0, 250.0, 0.001, 100, 200, 0.4, 0.001)
    else:
        # Cada variable tiene su propia cadena binaria.
        valores = ([0.0] * NUM_VAR, [100.0] * NUM_VAR, [0.001] * NUM_VAR, 100, 200, 0.4, 0.001)

    if len(sys.argv) > 2:
        if modo == 'varias':
            raise SystemExit('Para varias variables, ajusta sus rangos en main()')
        if len(sys.argv) != 9:
            raise SystemExit('Uso: script.py max xmin xmax TOL tam_pob num_gen prob_cruce prob_mut')
        valores = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]),
                   int(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]))

    print('Modo:', modo)
    print('Parámetros:', valores)
    pob, pos_mejor, historial = ejecutar(modo, *valores)
    mejor = pob[pos_mejor]
    print('\nMEJOR INDIVIDUO DE LA ÚLTIMA GENERACIÓN')
    print('Genotipo:', mejor.vec_genes if modo == 'varias' else mejor.genes)
    print('Fenotipo:', mejor.vec_x if modo == 'varias' else mejor.x)
    print('Aptitud:', mejor.aptitud)
    if modo != 'max':
        print('Aptitud bruta (función objetivo):', mejor.aptitud_bruta)
    print('Puntuación relativa:', mejor.puntuacion)
    print('Puntuación acumulada:', mejor.punt_acu)
    print('Élite:', mejor.elite)


if __name__ == '__main__':
    main()
