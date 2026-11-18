
// ADICIÓN DE PRUEBA: rand lee los mismos enteros suministrados a Python.
#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>
using namespace std;
#undef RAND_MAX
#define RAND_MAX 32767
static vector<int> azar;
static size_t cursor_azar = 0;
int libro_rand(){
    if(cursor_azar >= azar.size()) throw runtime_error("secuencia agotada");
    return azar[cursor_azar++];
}
#define rand libro_rand
// PDF 10, libro 313. Solo se publican estos tipos; falta bool elite.
typedef vector < bool > TGenes; // cadena de bits (genotipo)
typedef vector< TGenes > Tvec_genes; // vector de genotipos de cada variable
typedef vector< float > Tvec_var; // vector de fenotipos de cada variable
typedef vector< int > Tvec_int; // vector para las longitudes de los genes
typedef struct{
    Tvec_genes vec_genes;
    Tvec_var vec_x; // fenotipo
    double aptitud_bruta = 0; // función de evaluación
    double aptitud = 0; // aptitud transformada
    double puntuacion = 0; // punt. relativa : fitness/sumfitness
    double punt_acu = 0; // puntuación acumulada para sorteos
    bool elite = false; // R7
}TIndividuo;

int NUM_VAR = 3; // E1: dimensión elegida por el driver, no por el libro.
typedef vector<TIndividuo> TPoblacion;
float adaptacion(TIndividuo&, Tvec_int, Tvec_var, Tvec_var);
double decod(TGenes,int,double,double);
int bin_dec(TGenes,int);
void cruce(TIndividuo,TIndividuo,TIndividuo&,TIndividuo&,Tvec_int,Tvec_int,Tvec_var,Tvec_var);
TIndividuo genera_indiv(Tvec_int,Tvec_var,Tvec_var);
void revisar_adap_mini(TPoblacion& pob, int tam_pob, Tvec_int lcrom,
                       double& cmax, Tvec_var x_min, Tvec_var x_max)
{
    int i;
    cmax;
    cmax = pob[0].aptitud_bruta;
    for(i=1; i < tam_pob; i++){
        if (pob[i].aptitud_bruta > cmax)
            cmax = pob[i].aptitud_bruta;
    }
    cmax = cmax + cmax / 100;
    for(i=0; i < tam_pob; i++){
        pob[i].aptitud = cmax - pob[i].aptitud_bruta;
    }
}

TPoblacion poblacion_inicial(int tam_pob, Tvec_int lcrom, Tvec_var x_min, Tvec_var x_max)
{
    TPoblacion pob;
    TIndividuo indiv;
    int i;
    for(i=0; i < tam_pob; i++){
        indiv = genera_indiv(lcrom, x_min, x_max);
        pob.push_back(indiv);
    }
    return pob;
}

void seleccion(TPoblacion& pob, int tam_pob)
{
    int* sel_super; // seleccionados para sobrevivir
    float prob,f; // probabilidad de selección
    int pos_super; // posición del superviviente
    TPoblacion pob_aux; // población auxiliar
    int i,j;
    int TAM_ELITE = pob.size()* 2 /100;
    int* sel_elite;
    sel_super = new int[tam_pob];
    sel_elite = new int[TAM_ELITE];
    // se selecciona la elite
    for (i=0; i < TAM_ELITE; i++){
        sel_elite[i] = 0;
    }
    for (i=0; i < tam_pob; i++){
        pob[i].elite = false;
        j = 0;
        while ((j < TAM_ELITE) &&
               (pob[sel_elite[j]].aptitud >= pob[i].aptitud)){
            j++;
        }
        if (j < TAM_ELITE){
            // PDF 8, libro 309
            sel_elite[j] = i;
        }
    }
    for (i=0; i < TAM_ELITE; i++){
        pob[sel_elite[i]].elite = true;
    }
    // se seleccionan tam_pob individuos para reproducirse
    // se generan números aleatorios entre 0 y 1.
    // se seleccionan individuos de acuerdo con su punt. acumulada
    for (i=0; i < tam_pob; i++){
        if (pob[i].elite == true) //ELITISMO
            sel_super[i] = i;
        else{
            f = rand();
            prob = (f/(RAND_MAX+1.0));
            pos_super = 0;
            while ((pos_super < tam_pob)&&(prob>pob[pos_super].punt_acu))
                pos_super++;
            if (pos_super < tam_pob)
                sel_super[i] = pos_super;
            else
                sel_super[i] = pos_super-1;
        }
    }
    // se genera la población intermedia
    for (i=0; i < tam_pob; i++){
        pob_aux.push_back(pob[sel_super[i]]);
    }
    pob.clear();
    for (i=0; i < tam_pob; i++){
        pob.push_back(pob_aux[i]);
    }
    delete [] sel_super;
    delete [] sel_elite;
}

double decod(TGenes genes, int lcrom, double x_min, double x_max)
{
    double x;
    x=(float)bin_dec(genes, lcrom)/(pow((double)2,(double)lcrom) - 1);
    x = x_min + (x_max - x_min) * x;
    return x;
}

int bin_dec(TGenes genes, int lcrom)
{
    int i, d=0, pot=1;
    for(i=0; i < lcrom; i++){
        d = d + pot*genes[i];
        pot = pot * 2;
    }
    return d;
}

void reproduccion(TPoblacion& pob, int tam_pob, Tvec_int lcrom,
                  double prob_cruce, Tvec_var x_min, Tvec_var x_max)
{
    int* sel_cruce; //seleccionados para reproducirse
    int num_sel_cruce=0; //num de individuos seleccionados a cruzar
    double prob;
    Tvec_int punto_cruce;
    TIndividuo hijo1, hijo2;
    int i;
    sel_cruce = new int[tam_pob];
    // se eligen los individuos a cruzar
    for (i=0; i < tam_pob; i++){
        // se generan tam_pob números aleatorios a_i en [0 1)
        prob = (rand()/(RAND_MAX+1.0));
        // se eligen para el cruce los individuos de
        // las posiciones i con a_i < prob_cruce
        if (prob < prob_cruce){
            sel_cruce[num_sel_cruce] = i;
            num_sel_cruce++;
        }
    }
    // el número de seleccionados se hace par
    if ((num_sel_cruce % 2) == 1)
        num_sel_cruce--;
    // se cruzan los individuos elegidos en un punto al azar
    // E1: un punto por variable, una vez por reproducción.
    for(int j=0;j<NUM_VAR;j++){
        int punto=(int)((double)rand()*(lcrom[j]+1)/(RAND_MAX+1.0))+1;
        if(num_sel_cruce) punto=min(punto,lcrom[j]);
        punto_cruce.push_back(punto);
    }
    for (i=0; i < num_sel_cruce; i=i+2){
        cruce(pob[sel_cruce[i]], pob[sel_cruce[i+1]], hijo1, hijo2,
              lcrom, punto_cruce, x_min, x_max);
        // los nuevos individuos sustituyen a sus progenitores
        // respetando la élite
        if ((hijo1.aptitud_bruta<adaptacion(pob[sel_cruce[i]],lcrom,x_min,
            x_max)) || (!pob[sel_cruce[i]].elite)){ //ELITISMO
            pob[sel_cruce[i]] = hijo1;
        }
        if ((hijo2.aptitud_bruta <
             adaptacion(pob[sel_cruce[i+1]], lcrom, x_min,x_max))
             || (!pob[sel_cruce[i+1]].elite)){
            pob[sel_cruce[i+1]] = hijo2;
        }
    }
    delete [] sel_cruce;
}

void evaluacion(TPoblacion& pob, int tam_pob, int& pos_mejor, double& sumaptitud)
{
    float punt_acu = 0; // puntuación acumulada de los individuos
    float aptitud_mejor = 0; // mejor aptitud
    int i;
    sumaptitud = 0; // suma de las aptitud
    for (i=0; i < tam_pob; i++){
        sumaptitud = sumaptitud + pob[i].aptitud;
        if (pob[i].aptitud > aptitud_mejor){
            pos_mejor = i;
            aptitud_mejor = pob[i].aptitud;
        }
    }
    if(sumaptitud == 0) throw runtime_error("fitness nulo");
    for (i=0; i < tam_pob; i++){
        pob[i].puntuacion = pob[i].aptitud / sumaptitud;
        pob[i].punt_acu = pob[i].puntuacion + punt_acu;
        punt_acu = punt_acu + pob[i].puntuacion;
    }
}
// PDF 11-12, libro 314-316. No se publica main ni NUM_VAR.
// El texto indica que solo incluye las funciones afectadas.
/* funcion: genera_indiv
   Genera un individuo de la población inicial */
// R8 en la versión ejecutable: el impreso dice Tvec_int, no declarado.
TIndividuo genera_indiv(Tvec_int lcrom, Tvec_var x_min, Tvec_var x_max)
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

// DRIVER AÑADIDO: emite cada fase; main del libro no se ejecuta.
void emitir(const char* stage,TPoblacion& pob,int pos,double sum,double cmax){
    cout << stage << " " << pos << " " << sum << " " << cmax << " " << cursor_azar << "\n";
    for(auto ind:pob){
        cout << int(ind.elite) << " " << ind.aptitud << " " << ind.aptitud_bruta
             << " " << ind.puntuacion << " " << ind.punt_acu;
        for(float x : ind.vec_x) cout << " " << x;
        for(auto genes:ind.vec_genes) for(bool b:genes) cout << " " << int(b);
        cout << "\n";
    }
}
int main(int argc,char** argv){
    int value;
    while(cin >> value) azar.push_back(value);
    cout << setprecision(17);
    const int tam_pob = 50;
    Tvec_int lcrom={5,4,6}; Tvec_var x_min={0,0,0}, x_max={100,80,60};
    double cmax=0, sumaptitud=0;
    int pos_mejor=0;
    TPoblacion pob=poblacion_inicial(tam_pob,lcrom,x_min,x_max);
    revisar_adap_mini(pob,tam_pob,lcrom,cmax,x_min,x_max);
    evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
    emitir("inicial",pob,pos_mejor,sumaptitud,cmax);
    for(int gen=0;gen<3;gen++){
        seleccion(pob,tam_pob);
        emitir("seleccion",pob,pos_mejor,sumaptitud,cmax);
        reproduccion(pob,tam_pob,lcrom,0.8,x_min,x_max);
        emitir("reproduccion",pob,pos_mejor,sumaptitud,cmax);
        mutacion(pob,tam_pob,lcrom,0.15,x_min,x_max);
        emitir("mutacion",pob,pos_mejor,sumaptitud,cmax);
        revisar_adap_mini(pob,tam_pob,lcrom,cmax,x_min,x_max);
        evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
        emitir("evaluacion",pob,pos_mejor,sumaptitud,cmax);
    }
}
