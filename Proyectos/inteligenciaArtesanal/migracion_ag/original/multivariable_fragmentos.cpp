// PDF 11-12, libro 314-316. No se publica main ni NUM_VAR.
// El texto indica que solo incluye las funciones afectadas.
/* funcion: genera_indiv
   Genera un individuo de la población inicial */
// R8 en la versión ejecutable: el impreso dice Tvac_int, no declarado.
TIndividuo genera_indiv(Tvac_int lcrom, Tvec_var x_min, Tvec_var x_max)
{
    int i,j;
    TIndividuo indiv;
    TGenes genes;
    int gen;
    float f;
    indiv.vec_genes.clear();
    /* se generan los genotipos para cada variable */
    for(i=0; i< NUM_VAR; i++){
        genes.clear();
        for(j=0; j < lcrom[i]; j++){
            f = rand();
            if (f < RAND_MAX / 2 )
                gen = 0;
            else
                gen = 1;
            genes.push_back(gen);
        }
        indiv.vec_genes.push_back(genes);
    }
    indiv.aptitud_bruta = adaptacion(indiv, lcrom, x_min, x_max);
    return indiv;
}
/* funcion: adaptacion
   Evalua la calidad de un individuo */
float adaptacion(TIndividuo& individuo, Tvec_int lcrom, Tvec_var x_min, Tvec_var x_max)
{
    int i;
    Tvec_var x; // vector de fenotipos
    // PDF 11, libro 315
    float f; // valor de la función a optimizar
    x.clear();
    individuo.vec_x.clear();
    for(i=0; i < NUM_VAR; i++){
        individuo.vec_x.push_back(
            decod(individuo.vec_genes[i], lcrom[i], x_min[i], x_max[i]));
    }
    x = individuo.vec_x;
    f = 0;
    for(i=0; i < NUM_VAR; i++){
        f = f - x[i] * sin(sqrt(fabs(x[i])));
    }
    return f;
}
/* funcion: cruce
   Aplica el operador de cruce */
void cruce(TIndividuo padre1, TIndividuo padre2, TIndividuo& hijo1,
           TIndividuo& hijo2,Tvec_int lcrom, Tvec_int punto_cruce,
           Tvec_var x_min, Tvec_var x_max)
{
    int i,j;
    TGenes genes_hijo1, genes_hijo2;
    hijo1.vec_genes.clear();
    hijo2.vec_genes.clear();
    for(j=0; j < NUM_VAR; j++){
        // primera parte del intercambio: 1 a 1 y 2 a 2
        genes_hijo1.clear();
        genes_hijo2.clear();
        for(i=0; i < punto_cruce[j]; i++){
            genes_hijo1.push_back(padre1.vec_genes[j][i]);
            genes_hijo2.push_back(padre2.vec_genes[j][i]);
        }
        // segunda parte: 1 a 2 y 2 a 1
        for(i=punto_cruce[j]; i < lcrom[j]; i++){
            genes_hijo1.push_back(padre2.vec_genes[j][i]);
            genes_hijo2.push_back(padre1.vec_genes[j][i]);
        }
        hijo1.vec_genes.push_back(genes_hijo1);
        hijo2.vec_genes.push_back(genes_hijo2);
    }
    // se evalúan
    hijo1.aptitud_bruta = adaptacion(hijo1, lcrom, x_min, x_max);
    hijo2.aptitud_bruta = adaptacion(hijo2, lcrom, x_min, x_max);
}
/* funcion: mutacion
   Aplica el operador de mutacion a la Poblacion */
// PDF 12, libro 316
void mutacion(TPoblacion& pob, int tam_pob, Tvec_int lcrom,
              float prob_mut, Tvec_var x_min, Tvec_var x_max )
{
    bool mutado;
    int i,j,k;
    float prob,f;
    for (i=0; i < tam_pob; i++){
        mutado = false;
        for(k=0; k <NUM_VAR; k++){
            for (j=0; j < lcrom[k]; j++){
                // se genera un número aleatorio en [0 1)
                f = rand();
                prob = (f/(RAND_MAX+1.0));
                // se mutan aquellos genes con prob < que prob_mut
                if ((prob < prob_mut) && (!pob[i].elite)){
                    pob[i].vec_genes[k][j] = !(bool)(pob[i].vec_genes[k][j]);
                    mutado = true;
                }
            }
        }
        if (mutado)
            pob[i].aptitud_bruta = adaptacion(pob[i], lcrom, x_min,x_max);
    }
}
