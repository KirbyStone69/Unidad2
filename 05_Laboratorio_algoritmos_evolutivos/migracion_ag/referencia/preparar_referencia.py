"""Crea referencias C++ desde la transcripción, con reparaciones rastreables.
No modifica original/. El driver y los enlaces multivariable son añadidos.
Se ejecuta solo para las pruebas diferenciales; no para usar los algoritmos.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'original'


def funciones_sin_main(text):
    # main termina justo antes del primer comentario de función.
    start = text.index('/* funcion: poblacion_inicial')
    if 'void revisar_adap_mini(' in text:
        start = text.index('/* PDF 7, libro 306-307:')
    return text[start:]


def extraer_funcion(text, firma):
    start = text.index(firma)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end] + '\n'


def reparaciones(text, mini):
    # R2: asegurar el límite antes de evaluar el acceso.
    text = text.replace('((prob>pob[pos_super].punt_acu)&&(pos_super < tam_pob))',
                        '((pos_super < tam_pob)&&(prob>pob[pos_super].punt_acu))')
    # R1: sin overflow intermedio; si punto=lcrom+1 se usa el extremo.
    text = text.replace('rand() * (lcrom+1)', '(double)rand() * (lcrom+1)')
    punto = 'punto_cruce = (int)((double)rand() * (lcrom+1) / (RAND_MAX + 1.0)) + 1;'
    text = text.replace(punto, punto + '\n    if(num_sel_cruce) punto_cruce = min(punto_cruce, lcrom);')
    # R4: el test no usa suma nula, pero la referencia tiene la misma guarda.
    text = text.replace('    for (i=0; i < tam_pob; i++){\n        pob[i].puntuacion',
                        '    if(sumaptitud == 0) throw runtime_error("fitness nulo");\n    for (i=0; i < tam_pob; i++){\n        pob[i].puntuacion')
    if mini:
        # R5/R6: misma corrección que en Python; no se cambia la fórmula.
        text = text.replace('if (pob[i].aptitud > cmax)', 'if (pob[i].aptitud_bruta > cmax)')
        text = text.replace('hijo1.aptitud<adaptacion', 'hijo1.aptitud_bruta<adaptacion')
        text = text.replace('hijo2.aptitud <', 'hijo2.aptitud_bruta <')
    return text


PREAMBLE = r'''
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
'''


def cabecera(mini):
    file = 'funciones_minimizacion.h' if mini else 'funciones.h'
    h = (ORIGINAL / file).read_text()
    h = h[h.index('using namespace std;'):]
    # R3: inicialización explícita de los miembros escalares.
    for name in ('x','aptitud','aptitud_bruta','puntuacion','punt_acu'):
        h = h.replace(f'double {name};', f'double {name} = 0;')
    return h.replace('bool elite;', 'bool elite = false;')


def construir(out):
    out.mkdir(parents=True, exist_ok=True)
    for mode in ('maximizacion','minimizacion','multivariable'):
        mini = mode != 'maximizacion'
        base_name = 'minimizacion' if mini else 'maximizacion'
        base = funciones_sin_main((ORIGINAL / f'{base_name}.cpp').read_text())
        base = reparaciones(base, mini)
        if mode == 'multivariable':
            h, base = construir_multivariable(base)
        else:
            h = cabecera(mini)
        driver = controlador(mode)
        (out / f'{mode}.cpp').write_text(PREAMBLE + h + base + driver)


def construir_multivariable(base):
    # E1: recuperar funciones heredadas y adaptar exclusivamente tipos/enlaces.
    h = (ORIGINAL / 'multivariable.h').read_text()
    for name in ('aptitud','aptitud_bruta','puntuacion','punt_acu'):
        h = h.replace(f'double {name};', f'double {name} = 0;')
    h = h.replace('}TIndividuo;', '    bool elite = false; // R7\n}TIndividuo;')
    h += '''
int NUM_VAR = 3; // E1: dimensión elegida por el driver, no por el libro.
typedef vector<TIndividuo> TPoblacion;
float adaptacion(TIndividuo&, Tvec_int, Tvec_var, Tvec_var);
double decod(TGenes,int,double,double);
int bin_dec(TGenes,int);
void cruce(TIndividuo,TIndividuo,TIndividuo&,TIndividuo&,Tvec_int,Tvec_int,Tvec_var,Tvec_var);
TIndividuo genera_indiv(Tvec_int,Tvec_var,Tvec_var);
'''
    inherited=[]
    for signature in ('void revisar_adap_mini(', 'TPoblacion poblacion_inicial(',
                      'void seleccion(', 'double decod(', 'int bin_dec(',
                      'void reproduccion(', 'void evaluacion('):
        f = extraer_funcion(base,signature)
        if signature in ('void revisar_adap_mini(', 'TPoblacion poblacion_inicial(', 'void reproduccion('):
            f=f.replace('int lcrom','Tvec_int lcrom').replace('double x_min, double x_max',
                'Tvec_var x_min, Tvec_var x_max').replace('float x_min, float x_max',
                'Tvec_var x_min, Tvec_var x_max')
        if signature == 'void reproduccion(':
            f=f.replace('int punto_cruce;', 'Tvec_int punto_cruce;')
            expr='punto_cruce = (int)((double)rand() * (lcrom+1) / (RAND_MAX + 1.0)) + 1;\n    if(num_sel_cruce) punto_cruce = min(punto_cruce, lcrom);'
            f=f.replace(expr, '''// E1: un punto por variable, una vez por reproducción.
    for(int j=0;j<NUM_VAR;j++){
        int punto=(int)((double)rand()*(lcrom[j]+1)/(RAND_MAX+1.0))+1;
        if(num_sel_cruce) punto=min(punto,lcrom[j]);
        punto_cruce.push_back(punto);
    }''')
        inherited.append(f)
    snippets = (ORIGINAL / 'multivariable_fragmentos.cpp').read_text()
    snippets = snippets.replace('Tvac_int', 'Tvec_int')  # R8: errata de tipo.
    return h, '\n'.join(inherited) + snippets


def controlador(mode):
    mini=mode != 'maximizacion'
    multi=mode == 'multivariable'
    params = ('Tvec_int lcrom={5,4,6}; Tvec_var x_min={0,0,0}, x_max={100,80,60};'
              if multi else 'int lcrom=5; double x_min=0,x_max=32;')
    xs = ('for(float x : ind.vec_x) cout << " " << x;'
          if multi else 'cout << " " << ind.x;')
    genes = ('for(auto genes:ind.vec_genes) for(bool b:genes) cout << " " << int(b);'
             if multi else 'for(bool b:ind.genes) cout << " " << int(b);')
    raw = 'ind.aptitud_bruta' if mini else 'ind.aptitud'
    transform = 'revisar_adap_mini(pob,tam_pob,lcrom,cmax,x_min,x_max);' if mini else ''
    return f'''
// DRIVER AÑADIDO: emite cada fase; main del libro no se ejecuta.
void emitir(const char* stage,TPoblacion& pob,int pos,double sum,double cmax){{
    cout << stage << " " << pos << " " << sum << " " << cmax << " " << cursor_azar << "\\n";
    for(auto ind:pob){{
        cout << int(ind.elite) << " " << ind.aptitud << " " << {raw}
             << " " << ind.puntuacion << " " << ind.punt_acu;
        {xs}
        {genes}
        cout << "\\n";
    }}
}}
int main(int argc,char** argv){{
    int value;
    while(cin >> value) azar.push_back(value);
    cout << setprecision(17);
    const int tam_pob = 50;
    {params}
    double cmax=0, sumaptitud=0;
    int pos_mejor=0;
    TPoblacion pob=poblacion_inicial(tam_pob,lcrom,x_min,x_max);
    {transform}
    evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
    emitir("inicial",pob,pos_mejor,sumaptitud,cmax);
    for(int gen=0;gen<3;gen++){{
        seleccion(pob,tam_pob);
        emitir("seleccion",pob,pos_mejor,sumaptitud,cmax);
        reproduccion(pob,tam_pob,lcrom,0.8,x_min,x_max);
        emitir("reproduccion",pob,pos_mejor,sumaptitud,cmax);
        mutacion(pob,tam_pob,lcrom,0.15,x_min,x_max);
        emitir("mutacion",pob,pos_mejor,sumaptitud,cmax);
        {transform}
        evaluacion(pob,tam_pob,pos_mejor,sumaptitud);
        emitir("evaluacion",pob,pos_mejor,sumaptitud,cmax);
    }}
}}
'''


if __name__ == '__main__':
    construir(Path(__file__).resolve().parent / 'generada')
