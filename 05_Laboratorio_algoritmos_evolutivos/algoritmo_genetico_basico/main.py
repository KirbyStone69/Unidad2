import numpy as np
import random as rdm
import pandas as pd

xmin = -10
xmax =  10
precicion = float(0.001) 
num_poblacion = 8  
probabilidad_cruce = 0.8
probabilidad_mutacion = 0.01
generaciones_maximas = 100

poblacion = []
nueva_poblacion = [] 
l = int(np.ceil( np.log2(1 + ((xmax - xmin)/precicion)) ))

for i in range(num_poblacion):
    individuo = bin( rdm.randint(0, (2**l)-1) )[2:].zfill(15)
    poblacion.append({
        "genotipo": individuo,
        "fenotipo": None,
        "apti" : None
    })

def evaluacion(poblacion):
    for individuo in poblacion:
        #Sacamos el feotipo
        bin_num = int( individuo["genotipo"], 2)
        fenotipo = float(xmin + ((bin_num*(xmax-xmin))/ (2**l-1)))
        individuo["fenotipo"] = fenotipo
        #sacar el aptitud con una funcion simple
        apti = 100 - fenotipo**2 
        individuo["apti"] = apti

def ruleta_rusa(poblacion):
    padres = []
    #sumamos todas las apties 
    f_sigma = sum(individuo["apti"] for individuo in poblacion)
    p_i = []
    q_i = [0]
    #obtenemos probabilidad y probabilidad acumulada 
    for individuo in poblacion:
        p = individuo["apti"] / f_sigma 
        p_i.append( p )
        q_i.append(q_i[-1] + p)
    #print(pd.DataFrame({"Pi": p_i, "qi": q_i[1:]}))
    for j in range(2):
        a = rdm.random()
        for i in range(len(poblacion)):
            if q_i[i] < a and a <= q_i[i+1]:
                padres.append(poblacion[i])
                break
    return padres

def reproduccion(padres):
    k = rdm.randint(1, (l - 1)) 
    a = rdm.random()

    if a < probabilidad_cruce:
        h1 = padres[0]["genotipo"][:k] + padres[1]["genotipo"][k:]
        h2 = padres[1]["genotipo"][:k] + padres[0]["genotipo"][k:]
    else:
        h1 = padres[0]["genotipo"]
        h2 = padres[1]["genotipo"]

    hijos = [h1,h2]
    return hijos

def mutacion(hijos):
    hijos_mutados = []
    for hijo in hijos:
        bits = list(hijo)
        for i in range(len(bits)):
            a = rdm.random()
            if a < probabilidad_mutacion:
                if bits[i] == "0":
                    bits[i] = "1"
                else:
                    bits[i] = "0"
        hijos_mutados.append("".join(bits))
    return hijos_mutados
#LA TIERRA PROMETIDA
if __name__ == '__main__':
    evaluacion(poblacion)
    print("Poblacion aleatoria")
    print(pd.DataFrame(poblacion))

    for i in range(4):
        #ruleta
        padres = ruleta_rusa(poblacion)
        #reproduccion
        hijos = reproduccion(padres)
        #mutacion
        hijos_mutados = mutacion(hijos)
        #evaluacion
        for individuo in hijos_mutados:
            nueva_poblacion.append({
                "genotipo": individuo,
                "fenotipo": None,
                "apti" : None
            })
    evaluacion(nueva_poblacion)
    print("nueva poblacion")
    print(pd.DataFrame(nueva_poblacion))