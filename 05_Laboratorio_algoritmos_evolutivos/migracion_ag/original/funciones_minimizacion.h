// PDF 6, libro 304: el resto de la cabecera se hereda; solo el struct se imprime de nuevo.
// Transcripción revisada: PDF 2, libro 296-297. Errores del impreso conservados.
#include <stdlib.h>
#include <math.h>
#include <string>
#include <vector.h>
using namespace std;
// individuo
typedef vector < bool > TGenes;
typedef struct{
    TGenes genes;       // cadena de bits (genotipo)
    double x;           // fenotipo
    double aptitud;     // funcion de adaptacion
    double aptitud_bruta; // antes de transformarla
    double puntuacion;  // punt. relativa:fitness/sumfitness
    double punt_acu;    // puntuacion acumulada para sorteos
    bool elite;         // indicativo de pertenecer a la elite
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
