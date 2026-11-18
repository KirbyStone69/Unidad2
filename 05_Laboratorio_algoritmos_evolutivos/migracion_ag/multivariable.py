"""PDF 10-12, libro 313-316: variante multivariable de minimización.

Solo TIndividuo, genera_indiv, adaptacion, cruce y mutacion están publicados.
E1: main, población inicial y reproducción son enlaces explícitos a la base
mínima, con vectores por variable. NUM_VAR se obtiene del CLI (no publicado).
Selección, transformación, decodificación y evaluación se heredan sin cambio
algorítmico. R7: elite se añade porque mutacion lo utiliza pero el struct lo omite.
R8: se interpreta Tvac_int de genera_indiv como Tvec_int declarado.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import math

import compatibilidad as cpp
from compatibilidad import configurar_azar, float32, rand

TGenes = list[bool]
Tvec_genes = list[TGenes]
Tvec_var = list[float]
Tvec_int = list[int]
NUM_VAR = 0  # E1: el PDF no define su valor; main lo fija desde los vectores.


@dataclass
class TIndividuo:
    vec_genes: Tvec_genes = field(default_factory=list)
    vec_x: Tvec_var = field(default_factory=list)
    aptitud_bruta: float = 0.0
    aptitud: float = 0.0
    puntuacion: float = 0.0
    punt_acu: float = 0.0
    elite: bool = False  # R7: falta en el struct; usado en mutacion.


TPoblacion = list[TIndividuo]


def main():
    # E1: este main no aparece en el PDF.
    global NUM_VAR
    args = cpp.argumentos(multivariable=True)
    x_min = [float32(float(x)) for x in args.x_min.split(',')]
    x_max = [float32(float(x)) for x in args.x_max.split(',')]
    NUM_VAR = len(x_min)
    if len(x_max) != NUM_VAR:
        raise ValueError('Los vectores de límites deben tener igual longitud')
    TOL = [float(x) for x in args.TOL.split(',')]
    if len(TOL) == 1:
        TOL = TOL * NUM_VAR
    if len(TOL) != NUM_VAR:
        raise ValueError('TOL debe ser escalar o tener un valor por variable')
    lcrom = [cpp.longitud(x_min[i], x_max[i], TOL[i]) for i in range(NUM_VAR)]
    tam_pob, num_gen = args.tam_pob, args.num_gen
    prob_cruce, prob_mut = args.prob_cruce, float32(args.prob_mut)
    pob = poblacion_inicial(tam_pob, lcrom, x_min, x_max)
    cmax = 0.0
    cmax = revisar_adap_mini(pob, tam_pob, lcrom, cmax, x_min, x_max)
    pos_mejor, sumaptitud = evaluacion(pob, tam_pob)
    cpp.iniciar_panel('multivariable', args, pob[pos_mejor])
    for generacion in range(num_gen):
        cpp.nueva_generacion(generacion + 1)
        seleccion(pob, tam_pob)
        reproduccion(pob, tam_pob, lcrom, prob_cruce, x_min, x_max)
        mutacion(pob, tam_pob, lcrom, prob_mut, x_min, x_max)
        cmax = revisar_adap_mini(pob, tam_pob, lcrom, cmax, x_min, x_max)
        pos_mejor, sumaptitud = evaluacion(pob, tam_pob, pos_mejor, sumaptitud)
        cpp.actualizar_panel(pob[pos_mejor])
    cpp.terminar_panel(pob[pos_mejor])
    xs = ', '.join(format(x, '.6g') for x in pob[pos_mejor].vec_x)
    resultado = f'Aptitud del mejor({pos_mejor}) = {pob[pos_mejor].aptitud_bruta:.6g} en [{xs}]'
    print(resultado)
    cpp.guardar_resultado('multivariable', args, lcrom, pos_mejor, pob[pos_mejor], resultado)
    cpp.informar_incidencias()
    return pob, pos_mejor, sumaptitud


def revisar_adap_mini(pob, tam_pob, lcrom, cmax, x_min, x_max):
    # x_min y x_max eran float; no se usan en el cuerpo, igual que lcrom.
    cmax = pob[0].aptitud_bruta
    for i in range(1, tam_pob):
        # R5: el impreso compara aptitud, pero asigna aptitud_bruta.
        if pob[i].aptitud_bruta > cmax:
            cmax = pob[i].aptitud_bruta
    cmax = cmax + cmax / 100
    for i in range(tam_pob):
        pob[i].aptitud = cmax - pob[i].aptitud_bruta
    return cmax  # parámetro double& de salida.


def poblacion_inicial(tam_pob, lcrom, x_min, x_max):
    pob = []
    for i in range(tam_pob):
        indiv = genera_indiv(lcrom, x_min, x_max)
        pob.append(deepcopy(indiv))  # push_back copia los valores.
    return pob


def genera_indiv(lcrom, x_min, x_max):
    indiv = TIndividuo()
    indiv.vec_genes.clear()
    for i in range(NUM_VAR):
        genes = []
        for j in range(lcrom[i]):
            f = float32(rand())
            if f < cpp.RAND_MAX // 2:
                gen = 0
            else:
                gen = 1
            genes.append(bool(gen))
        indiv.vec_genes.append(genes.copy())
    indiv.aptitud_bruta = adaptacion(indiv, lcrom, x_min, x_max)
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
    x = []
    x.clear()
    individuo.vec_x.clear()
    for i in range(NUM_VAR):
        individuo.vec_x.append(float32(decod(individuo.vec_genes[i], lcrom[i],
                                            float32(x_min[i]), float32(x_max[i]))))
    x = individuo.vec_x.copy()
    f = float32(0)
    for i in range(NUM_VAR):
        # Sobrecargas float de <math.h> con using namespace std (C++17).
        raiz = cpp.raiz32(float32(abs(x[i])))
        seno = cpp.seno32(raiz)
        producto = float32(x[i] * seno)
        f = float32(f - producto)
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
    # E1: vector de puntos para llamar al cruce publicado; se calcula una
    # sola vez por reproducción, igual que el punto escalar en la base.
    punto_cruce = []
    for j in range(NUM_VAR):
        punto = int(rand() * (lcrom[j] + 1) / (cpp.RAND_MAX + 1.0)) + 1
        if num_sel_cruce:
            punto = cpp.punto_seguro(punto, lcrom[j])
        punto_cruce.append(punto)
    # R6: comparar aptitud_bruta; el cruce no asigna aptitud transformada.
    for i in range(0, num_sel_cruce, 2):
        cruce(pob[sel_cruce[i]], pob[sel_cruce[i+1]], hijo1, hijo2,
              lcrom, punto_cruce, x_min, x_max)
        if (hijo1.aptitud_bruta < adaptacion(pob[sel_cruce[i]], lcrom, x_min, x_max)
                or not pob[sel_cruce[i]].elite):
            pob[sel_cruce[i]] = deepcopy(hijo1)
        if (hijo2.aptitud_bruta < adaptacion(pob[sel_cruce[i+1]], lcrom, x_min, x_max)
                or not pob[sel_cruce[i+1]].elite):
            pob[sel_cruce[i+1]] = deepcopy(hijo2)


def cruce(padre1, padre2, hijo1, hijo2, lcrom, punto_cruce, x_min, x_max):
    padre1, padre2 = deepcopy(padre1), deepcopy(padre2)
    hijo1.vec_genes.clear()
    hijo2.vec_genes.clear()
    for j in range(NUM_VAR):
        genes_hijo1, genes_hijo2 = [], []
        punto = cpp.punto_seguro(punto_cruce[j], lcrom[j])
        for i in range(punto):
            genes_hijo1.append(padre1.vec_genes[j][i])
            genes_hijo2.append(padre2.vec_genes[j][i])
        for i in range(punto, lcrom[j]):
            genes_hijo1.append(padre2.vec_genes[j][i])
            genes_hijo2.append(padre1.vec_genes[j][i])
        hijo1.vec_genes.append(genes_hijo1.copy())
        hijo2.vec_genes.append(genes_hijo2.copy())
    hijo1.aptitud_bruta = adaptacion(hijo1, lcrom, x_min, x_max)
    hijo2.aptitud_bruta = adaptacion(hijo2, lcrom, x_min, x_max)
    cpp.registrar_cruce(padre1, padre2, hijo1, hijo2, punto_cruce)


def mutacion(pob, tam_pob, lcrom, prob_mut, x_min, x_max):
    prob_mut = float32(prob_mut)  # El parámetro multivariable es float.
    for i in range(tam_pob):
        mutado = False
        for k in range(NUM_VAR):
            for j in range(lcrom[k]):
                f = float32(rand())
                prob = float32(f / (cpp.RAND_MAX + 1.0))
                if prob < prob_mut and not pob[i].elite:
                    pob[i].vec_genes[k][j] = not bool(pob[i].vec_genes[k][j])
                    cpp.registrar_mutacion(pob[i], k, j)
                    mutado = True
        # Fuera de k y de j: así aparece en la página 316.
        if mutado:
            pob[i].aptitud_bruta = adaptacion(pob[i], lcrom, x_min, x_max)


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
