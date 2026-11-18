"""PDF 2-6, libro 296-304: maximización.

Orden de funciones y bucles del C++ conservado. R1/R2/R3 corresponden al
REPORTE.md. La comparación < en reproducción es literal, aunque contradice
la intención de proteger la mejor aptitud en maximización.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import math

import compatibilidad as cpp
from compatibilidad import configurar_azar, float32, rand

TGenes = list[bool]


@dataclass
class TIndividuo:
    genes: TGenes = field(default_factory=list)
    x: float = 0.0
    aptitud: float = 0.0
    puntuacion: float = 0.0
    punt_acu: float = 0.0
    elite: bool = False  # R3: inicialización explícita; C++ lo deja indefinido.


TPoblacion = list[TIndividuo]


def main(argv=None, observar=None, observar_evaluacion=None):
    # argv permite ejecutar el mismo algoritmo desde grafica.py.
    args = cpp.argumentos(argv=argv)
    with cpp.observar_evaluaciones(observar_evaluacion):
        x_min, x_max, TOL = args.x_min, args.x_max, args.TOL
        tam_pob, num_gen = args.tam_pob, args.num_gen
        prob_cruce, prob_mut = args.prob_cruce, args.prob_mut
        lcrom = cpp.longitud(x_min, x_max, TOL)
        pob = poblacion_inicial(tam_pob, lcrom, x_min, x_max)
        pos_mejor, sumaptitud = evaluacion(pob, tam_pob)
        cpp.iniciar_panel('maximizacion', args, pob[pos_mejor])
        if observar is not None:
            observar(0, 'Inicialización', pob, pos_mejor)
        for generacion in range(num_gen):
            cpp.nueva_generacion(generacion + 1)
            seleccion(pob, tam_pob)
            if observar is not None:
                observar(generacion + 1, 'Selección', pob, None)
            reproduccion(pob, tam_pob, lcrom, prob_cruce, x_min, x_max)
            if observar is not None:
                observar(generacion + 1, 'Cruce', pob, None)
            mutacion(pob, tam_pob, lcrom, prob_mut, x_min, x_max)
            if observar is not None:
                observar(generacion + 1, 'Mutación', pob, None)
            pos_mejor, sumaptitud = evaluacion(pob, tam_pob, pos_mejor, sumaptitud)
            cpp.actualizar_panel(pob[pos_mejor])
            if observar is not None:
                observar(generacion + 1, 'Evaluación', pob, pos_mejor)
        cpp.terminar_panel(pob[pos_mejor])
        resultado = f'Aptitud del mejor({pos_mejor}) = {pob[pos_mejor].aptitud:.6g} en {pob[pos_mejor].x:.6g}'
        print(resultado)
        cpp.guardar_resultado('maximizacion', args, lcrom, pos_mejor, pob[pos_mejor], resultado)
        cpp.informar_incidencias()
        return pob, pos_mejor, sumaptitud


def poblacion_inicial(tam_pob, lcrom, x_min, x_max):
    pob = []
    for i in range(tam_pob):
        indiv = genera_indiv(lcrom, x_min, x_max)
        pob.append(deepcopy(indiv))  # push_back copia los valores.
    return pob


def genera_indiv(lcrom, x_min, x_max):
    indiv = TIndividuo()
    indiv.genes.clear()
    for i in range(lcrom):
        if rand() < cpp.RAND_MAX // 2:
            gen = 0
        else:
            gen = 1
        indiv.genes.append(bool(gen))
    indiv.aptitud = adaptacion(indiv, lcrom, x_min, x_max)
    return indiv


def seleccion(pob, tam_pob):
    sel_super = [0] * tam_pob
    pob_aux = []
    TAM_ELITE = len(pob) * 2 // 100
    sel_elite = [0] * TAM_ELITE
    for i in range(TAM_ELITE):
        sel_elite[i] = 0
    for i in range(tam_pob):
        pob[i].elite = False
        j = 0
        while j < TAM_ELITE and pob[sel_elite[j]].aptitud >= pob[i].aptitud:
            j += 1
        if j < TAM_ELITE:
            sel_elite[j] = i
    for i in range(TAM_ELITE):
        pob[sel_elite[i]].elite = True
    for i in range(tam_pob):
        if pob[i].elite is True:
            sel_super[i] = i
        else:
            f = float32(rand())
            prob = float32(f / (cpp.RAND_MAX + 1.0))
            pos_super = 0
            # R2: comprobar el límite antes de indexar permite el fallback del libro.
            while pos_super < tam_pob and prob > pob[pos_super].punt_acu:
                pos_super += 1
            if pos_super < tam_pob:
                sel_super[i] = pos_super
            else:
                sel_super[i] = pos_super - 1
    for i in range(tam_pob):
        pob_aux.append(deepcopy(pob[sel_super[i]]))
    pob.clear()
    for i in range(tam_pob):
        pob.append(deepcopy(pob_aux[i]))
    # delete[] es responsabilidad del recolector de Python.


def adaptacion(individuo, lcrom, x_min, x_max):
    x = decod(individuo.genes, lcrom, x_min, x_max)
    individuo.x = x
    f = 20 + math.exp(1.0) - 20 * math.exp(-0.2 * abs(x)) - math.exp(math.cos(2 * math.pi * x))
    cpp.registrar_evaluacion(x, f)
    return f


def decod(genes, lcrom, x_min, x_max):
    x = float32(bin_dec(genes, lcrom)) / (math.pow(2.0, float(lcrom)) - 1)
    x = x_min + (x_max - x_min) * x
    return x


def bin_dec(genes, lcrom):
    d, pot = 0, 1
    for i in range(lcrom):
        d = d + pot * genes[i]
        pot = pot * 2
    return d


def reproduccion(pob, tam_pob, lcrom, prob_cruce, x_min, x_max):
    sel_cruce = [0] * tam_pob
    num_sel_cruce = 0
    hijo1, hijo2 = TIndividuo(), TIndividuo()
    for i in range(tam_pob):
        prob = rand() / (cpp.RAND_MAX + 1.0)
        if prob < prob_cruce:
            sel_cruce[num_sel_cruce] = i
            num_sel_cruce += 1
    if num_sel_cruce % 2 == 1:
        num_sel_cruce -= 1
    punto_cruce = int(rand() * (lcrom + 1) / (cpp.RAND_MAX + 1.0)) + 1
    # R1 solo se aplica si hay parejas; el impreso sortea aun sin parejas.
    if num_sel_cruce:
        punto_cruce = cpp.punto_seguro(punto_cruce, lcrom)
    for i in range(0, num_sel_cruce, 2):
        cruce(pob[sel_cruce[i]], pob[sel_cruce[i+1]], hijo1, hijo2,
              lcrom, punto_cruce, x_min, x_max)
        if (hijo1.aptitud < adaptacion(pob[sel_cruce[i]], lcrom, x_min, x_max)
                or not pob[sel_cruce[i]].elite):
            pob[sel_cruce[i]] = deepcopy(hijo1)
        if (hijo2.aptitud < adaptacion(pob[sel_cruce[i+1]], lcrom, x_min, x_max)
                or not pob[sel_cruce[i+1]].elite):
            pob[sel_cruce[i+1]] = deepcopy(hijo2)


def cruce(padre1, padre2, hijo1, hijo2, lcrom, punto_cruce, x_min, x_max):
    # Equivalente a padres por valor; permite alias de padre/hijo como en C++.
    padre1, padre2 = deepcopy(padre1), deepcopy(padre2)
    punto_cruce = cpp.punto_seguro(punto_cruce, lcrom)
    hijo1.genes.clear()
    hijo2.genes.clear()
    for i in range(punto_cruce):
        hijo1.genes.append(padre1.genes[i])
        hijo2.genes.append(padre2.genes[i])
    for i in range(punto_cruce, lcrom):
        hijo1.genes.append(padre2.genes[i])
        hijo2.genes.append(padre1.genes[i])
    hijo1.aptitud = adaptacion(hijo1, lcrom, x_min, x_max)
    hijo2.aptitud = adaptacion(hijo2, lcrom, x_min, x_max)
    cpp.registrar_cruce(padre1, padre2, hijo1, hijo2, punto_cruce)


def mutacion(pob, tam_pob, lcrom, prob_mut, x_min, x_max):
    for i in range(tam_pob):
        mutado = False
        for j in range(lcrom):
            prob = float32(rand() / (cpp.RAND_MAX + 1.0))
            if prob < prob_mut and not pob[i].elite:
                pob[i].genes[j] = not bool(pob[i].genes[j])
                cpp.registrar_mutacion(pob[i], 0, j)
                mutado = True
            # Dentro de j, exactamente como en las páginas 303 y 312.
            if mutado:
                pob[i].aptitud = adaptacion(pob[i], lcrom, x_min, x_max)


def evaluacion(pob, tam_pob, pos_mejor=0, sumaptitud=0.0):
    punt_acu = float32(0)
    aptitud_mejor = float32(0)
    sumaptitud = 0.0
    for i in range(tam_pob):
        sumaptitud = sumaptitud + pob[i].aptitud
        if pob[i].aptitud > aptitud_mejor:
            pos_mejor = i
            aptitud_mejor = float32(pob[i].aptitud)
    # R4: detener el caso 0/0; no se reemplaza por selección uniforme.
    if sumaptitud == 0 or not math.isfinite(sumaptitud):
        raise ValueError('Suma de aptitudes nula/no finita: ruleta indefinida en el original')
    for i in range(tam_pob):
        pob[i].puntuacion = pob[i].aptitud / sumaptitud
        pob[i].punt_acu = pob[i].puntuacion + punt_acu
        punt_acu = float32(punt_acu + pob[i].puntuacion)
    return pos_mejor, sumaptitud  # sustituye las dos referencias de salida.


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        raise SystemExit(str(error))
