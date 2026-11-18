// PDF 10, libro 313. Solo se publican estos tipos; falta bool elite.
typedef vector < bool > TGenes; // cadena de bits (genotipo)
typedef vector< TGenes > Tvec_genes; // vector de genotipos de cada variable
typedef vector< float > Tvec_var; // vector de fenotipos de cada variable
typedef vector< int > Tvec_int; // vector para las longitudes de los genes
typedef struct{
    Tvec_genes vec_genes;
    Tvec_var vec_x; // fenotipo
    double aptitud_bruta; // función de evaluación
    double aptitud; // aptitud transformada
    double puntuacion; // punt. relativa : fitness/sumfitness
    double punt_acu; // puntuación acumulada para sorteos
}TIndividuo;
