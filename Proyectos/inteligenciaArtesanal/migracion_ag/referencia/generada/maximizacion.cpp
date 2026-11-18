
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
using namespace std;
// individuo
typedef vector < bool > TGenes;
typedef struct{
    TGenes genes;       // cadena de bits (genotipo)
    double x = 0;           // fenotipo
    double aptitud = 0;     // funcion de evaluacion
    double puntuacion = 0;  // punt. relativa:fitness/sumfitness
    double punt_acu = 0;    // puntuacion acumulada para sorteos
    bool elite = false;         // indicativo de pertenecer a la elite
}TIndividuo;
// población
typedef vector <TIndividuo> TPoblacion;
TPoblacion poblacion_inicial(int tam_pob, int lcrom, double x_min, double x_max);
TIndividuo genera_indiv(int lcrom, double x_min, double x_max);
void seleccion(TPoblacion& pob, int tam_pob);
double adaptacion(TIndividuo& individuo, int lcrom, double x_min, double x_max);
double decod(TGenes genes, int lcrom, double x_min, double x_max);
int bin_dec(TGenes genes, int lcrom);
void reproduccion(TPoblacion& pob, int tam_pob, int lcrom,
                  double prob_cruce, double x_min, double x_max);
void cruce(TIndividuo padre1, TIndividuo padre2, TIndividuo& hijo1,
           TIndividuo& hijo2,int lcrom, int punto_cruce, double x_min, double x_max);
void mutacion(TPoblacion& pob, int tam_pob, int lcrom,
              double prob_mut,double x_min, double x_max);
void evaluacion(TPoblacion& pob, int tam_pob, int& pos_mejor, double& sumfitness);
/* funcion: poblacion_inicial
   Genera la población inicial aleatoriamente */
TPoblacion poblacion_inicial(int tam_pob, int lcrom, double x_min, double x_max)
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
/* funcion: genera_indiv
   Genera un individuo de la población inicial */
// PDF 3, libro 299
TIndividuo genera_indiv(int lcrom, double x_min, double x_max)
{
    int i;
    TIndividuo indiv;
    int gen;
    indiv.genes.clear();
    for(i=0; i < lcrom; i++){
        if (rand() < RAND_MAX / 2 )
            gen = 0;
        else
            gen = 1;
        indiv.genes.push_back(gen);
    }
    indiv.aptitud = adaptacion(indiv, lcrom, x_min, x_max);
    return indiv;
}
/* funcion: seleccion
   Selecciona un unico individuo por el metodo de la ruleta */
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
            // PDF 4, libro 300
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
/* funcion: adaptacion
   Evalua la calidad de un individuo */
double adaptacion(TIndividuo& individuo, int lcrom, double x_min, double x_max)
{
    double x; // fenotipo
    double f; // valor de la función a optimizar
    // PDF 4, libro 301
    x = decod(individuo.genes, lcrom, x_min, x_max);
    individuo.x = x;
    // AQUÍ se especifica la función a optimizar
    f = 20+exp((double)1)-20*exp((double)(-0.2*fabs(x)))-
        exp((double)(cos(2*M_PI*x)));
    return f;
}
/* funcion: decod
   Decodifica el genotipo de un individuo */
double decod(TGenes genes, int lcrom, double x_min, double x_max)
{
    double x;
    x=(float)bin_dec(genes, lcrom)/(pow((double)2,(double)lcrom) - 1);
    x = x_min + (x_max - x_min) * x;
    return x;
}
/* funcion: bin_dec
   Convierte de binario a decimal */
int bin_dec(TGenes genes, int lcrom)
{
    int i, d=0, pot=1;
    for(i=0; i < lcrom; i++){
        d = d + pot*genes[i];
        pot = pot * 2;
    }
    return d;
}
/* funcion: reproduccion
   Selecciona los individuos a reproducirse y aplica el operador de cruce */
// PDF 5, libro 302
void reproduccion(TPoblacion& pob, int tam_pob, int lcrom,
                  double prob_cruce, double x_min, double x_max)
{
    int* sel_cruce; //seleccionados para reproducirse
    int num_sel_cruce=0; //num de individuos seleccionados a cruzar
    double prob;
    int punto_cruce;
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
    punto_cruce = (int)((double)rand() * (lcrom+1) / (RAND_MAX + 1.0)) + 1;
    if(num_sel_cruce) punto_cruce = min(punto_cruce, lcrom);
    for (i=0; i < num_sel_cruce; i=i+2){
        cruce(pob[sel_cruce[i]], pob[sel_cruce[i+1]], hijo1, hijo2,
              lcrom, punto_cruce, x_min, x_max);
        // los nuevos individuos sustituyen a sus progenitores
        // respetando la élite
        if ((hijo1.aptitud<adaptacion(pob[sel_cruce[i]],lcrom,x_min,
            x_max)) || (!pob[sel_cruce[i]].elite)){ //ELITISMO
            pob[sel_cruce[i]] = hijo1;
        }
        if ((hijo2.aptitud <
             adaptacion(pob[sel_cruce[i+1]], lcrom, x_min,x_max))
             || (!pob[sel_cruce[i+1]].elite)){
            pob[sel_cruce[i+1]] = hijo2;
        }
    }
    delete [] sel_cruce;
}
/* funcion: cruce
   Aplica el operador de cruce */
// PDF 5, libro 303
void cruce(TIndividuo padre1, TIndividuo padre2, TIndividuo& hijo1,
           TIndividuo& hijo2, int lcrom, int punto_cruce, double x_min, double x_max)
{
    int i;
    hijo1.genes.clear();
    hijo2.genes.clear();
    // primera parte del intercambio: 1 a 1 y 2 a 2
    for(i=0; i < punto_cruce; i++){
        hijo1.genes.push_back(padre1.genes[i]);
        hijo2.genes.push_back(padre2.genes[i]);
    }
    // segunda parte: 1 a 2 y 2 a 1
    for(i=punto_cruce; i < lcrom; i++){
        hijo1.genes.push_back(padre2.genes[i]);
        hijo2.genes.push_back(padre1.genes[i]);
    }
    // se evalúan
    hijo1.aptitud = adaptacion(hijo1, lcrom, x_min, x_max);
    hijo2.aptitud = adaptacion(hijo2, lcrom, x_min, x_max);
}
/* funcion: mutacion
   Aplica el operador de mutacion a la Poblacion */
void mutacion(TPoblacion& pob, int tam_pob, int lcrom, double prob_mut,
              double x_min, double x_max)
{
    bool mutado;
    int i,j;
    float prob;
    for (i=0; i < tam_pob; i++){
        mutado = false;
        for (j=0; j < lcrom; j++){
            // se genera un número aleatorio en [0 1)
            prob = (rand()/(RAND_MAX+1.0));
            // se mutan aquellos genes con prob < que prob_mut
            if ((prob < prob_mut) && (!pob[i].elite)){ //ELITISMO
                pob[i].genes[j] = !(bool)(pob[i].genes[j]);
                mutado = true;
            }
            if (mutado)
                pob[i].aptitud = adaptacion(pob[i], lcrom, x_min,x_max);
        }
    }
}
/* funcion: evaluacion
   Calcula y actualiza as estadisticas de la poblacion */
// PDF 6, libro 304
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

// DRIVER AÑADIDO: emite cada fase; main del libro no se ejecuta.
void emitir(const char* stage,TPoblacion& pob,int pos,double sum,double cmax){
    cout << stage << " " << pos << " " << sum << " " << cmax << " " << cursor_azar << "\n";
    for(auto ind:pob){
        cout << int(ind.elite) << " " << ind.aptitud << " " << ind.aptitud
             << " " << ind.puntuacion << " " << ind.punt_acu;
        cout << " " << ind.x;
        for(bool b:ind.genes) cout << " " << int(b);
        cout << "\n";
    }
}
int main(int argc,char** argv){
    int value;
    while(cin >> value) azar.push_back(value);
    cout << setprecision(17);
    const int tam_pob = 50;
    int lcrom=5; double x_min=0,x_max=32;
    double cmax=0, sumaptitud=0;
    int pos_mejor=0;
    TPoblacion pob=poblacion_inicial(tam_pob,lcrom,x_min,x_max);
    
    evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
    emitir("inicial",pob,pos_mejor,sumaptitud,cmax);
    for(int gen=0;gen<3;gen++){
        seleccion(pob,tam_pob);
        emitir("seleccion",pob,pos_mejor,sumaptitud,cmax);
        reproduccion(pob,tam_pob,lcrom,0.8,x_min,x_max);
        emitir("reproduccion",pob,pos_mejor,sumaptitud,cmax);
        mutacion(pob,tam_pob,lcrom,0.15,x_min,x_max);
        emitir("mutacion",pob,pos_mejor,sumaptitud,cmax);
        
        evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
        emitir("evaluacion",pob,pos_mejor,sumaptitud,cmax);
    }
}
