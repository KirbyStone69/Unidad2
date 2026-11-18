"""Spanish Rich CLI: interactive laboratory or reproducible batch commands."""
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.theme import Theme
from .evaluation import dataset_info,compatibility_info
from .spaces import SearchConfig,GridSpace,DirectSpace
from .search import run_search,compare_methods,METHODS
from .persistence import export_results,load_results,read_json
from .charts import export_plots,LABELS

THEME=Theme({'title':'bold #39FF88','main':'#E4FBEA','secondary':'#8BAF99',
             'warning':'#FFB84D','error':'#FF5577','winner':'bold #B83240',
             'panel':'#E4FBEA on #10241A'})


def parser():
    p=argparse.ArgumentParser(description='Hyperparameter Lab · capítulo 8 · Wine + AdaBoost',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--method',choices=[*METHODS,'compare','info','stats'],help='Sin este argumento se abre el menú.')
    p.add_argument('--population',type=int,default=20)
    p.add_argument('--generations',type=int,default=5)
    p.add_argument('--mutation',type=float,default=.3,help='Probabilidad de mutar un individuo; por gen: 1/2.')
    p.add_argument('--crossover',type=float,default=.8)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--elite',type=int,default=1)
    p.add_argument('--folds',type=int,default=5)
    p.add_argument('--tournament',type=int,default=2)
    p.add_argument('--eta',type=float,default=20.)
    p.add_argument('--grid',type=Path,help='JSON con listas n_estimators y learning_rate.')
    p.add_argument('--bounds',type=Path,help='JSON con rangos [mínimo,máximo] para el AG directo.')
    p.add_argument('--output',type=Path,default=Path('results'),help='Directorio de exportación (archivos con nombres fijos).')
    p.add_argument('--input',type=Path,help='Cargar results.json para visualizar o exportar sin reentrenar.')
    p.add_argument('--plots',action='store_true',help='Exportar también evolution.png y comparison.png.')
    p.add_argument('--quiet',action='store_true',help='Ocultar detalle por configuración y generación.')
    return p


def banner(console):
    console.print(Panel('[bold #39FF88]HYPERPARAMETER / GENETIC LAB[/]\n'
        '[#8BAF99]CAPÍTULO 08 · WINE + ADABOOST · EXPLORAR / AJUSTAR / COMPARAR[/]',
        border_style='#193528',style='panel',padding=(1,2)))
    info=compatibility_info()
    console.print(f'scikit-learn {info["sklearn"]} · SAMME fijo · fitness = accuracy CV promedio',style='secondary')
    console.print('Adaptación moderna: sin SAMME.R ni sklearn-deap antiguo.',style='secondary')


def show_dataset(console):
    info=dataset_info()
    table=Table(title='01 / CONJUNTO WINE',border_style='#193528',header_style='title')
    table.add_column('Propiedad');table.add_column('Valor',style='main')
    for name,value in [('Observaciones',info['samples']),('Características',info['features']),
                       ('Clases',info['classes']),('Características químicas',', '.join(info['feature_names']))]:
        table.add_row(name,str(value))
    console.print(table)
    console.print('Hiperparámetros: n_estimators y learning_rate se fijan antes de fit().\n'
        'Parámetros aprendidos: divisiones de los árboles, estimadores y sus pesos se ajustan durante fit().',style='secondary')


def show_results(console,results):
    if not results:
        console.print('Aún no hay resultados. Ejecuta una búsqueda primero.',style='warning');return
    table=Table(title='Mejor resultado observado',border_style='#193528',header_style='title')
    for name in ('Método','Accuracy CV','Base CV','Segundos','CV únicas','Fits','Mejores hiperparámetros'):
        table.add_column(name)
    for result in results:
        table.add_row(LABELS[result.method],f'{result.best_accuracy:.6f}',f'{result.baseline["accuracy"]:.6f}',
            f'{result.elapsed_seconds:.3f}',str(len(result.evaluations)),str(len(result.evaluations)*result.config['folds']),
            f'n_estimators={result.best_params["n_estimators"]}, learning_rate={result.best_params["learning_rate"]:.9g}')
    console.print(table)
    # Keep complete values readable even on an 80-column terminal.
    for result in results:
        console.print(f'{LABELS[result.method]} → n_estimators={result.best_params["n_estimators"]}, '
                      f'learning_rate={result.best_params["learning_rate"]:.17g}',style='main')
    hashes={r.cv['split_hash'] for r in results}
    if len(hashes)>1:
        console.print('Estos resultados usan distintas particiones: no constituyen una comparación controlada.',style='warning')
    console.print('Tiempo: búsqueda con sus mensajes; baseline aparte. Fits: CV únicas × folds; no incluyen baseline.',style='secondary')
    console.print('CV usada para selección, sin test independiente. Los AG no garantizan un óptimo global ni ser más rápidos.\n'
        'Grid exhaustivo garantiza el mejor score de su cuadrícula finita, no de todos los valores posibles.',style='warning')


def show_statistics(console,results):
    if not results:
        show_results(console,results);return
    for result in results:
        if result.history:
            table=Table(title=f'06 / {LABELS[result.method]}',border_style='#193528',header_style='title')
            for name in ('Gen.','Evaluados','CV nuevas','Mejor','Promedio','Peor','Desv. estándar'):
                table.add_column(name,justify='right')
            for row in result.history:
                table.add_row(str(row['generation']),str(row['evaluated']),str(row['unique_evaluations']),
                    *(f'{row[k]:.6f}' for k in ('best','mean','worst','std')))
            console.print(table)
        console.print(f'{LABELS[result.method]}: solicitudes fitness={result.fitness_requests}, '
            f'CV únicas={len(result.evaluations)}, caché={result.fitness_requests-len(result.evaluations)}',style='secondary')
        console.print(f'Folds SHA256: {result.cv["split_hash"]}',style='secondary')
    show_results(console,results)


class SearchDisplay:
    def __init__(self,console,quiet=False):
        self.console=console;self.quiet=quiet;self.task=None
        self.progress=Progress(TextColumn('[#39FF88]{task.description}'),
            BarColumn(complete_style='#268954',finished_style='#39FF88'),
            TextColumn('{task.completed:.0f}/{task.total:.0f}'),TimeElapsedColumn(),
            console=console,disable=quiet or not console.is_terminal)

    def __enter__(self):
        self.progress.start();return self

    def __exit__(self,*args):
        self.progress.stop()

    def __call__(self,kind,data):
        if kind=='start':
            if self.task is not None:self.progress.remove_task(self.task)
            self.task=self.progress.add_task(LABELS[data['method']],total=data['total'])
            if data['method']=='grid':
                self.console.print(f'Grid exhaustivo: {data["total"]} combinaciones. Cada una requiere entrenar un modelo por fold; '
                    'el coste crece como el producto de los tamaños de las listas.',style='secondary')
            elif not self.quiet:
                self.console.print('Gen. | Evaluados | CV nuevas | Mejor | Promedio | Peor | Desv.',style='title')
        elif kind=='evaluation':
            if not self.quiet:
                self.console.print(f'{data["index"]}/{data["total"]}  n_estimators={data["n_estimators"]}  '
                    f'learning_rate={data["learning_rate"]:.9g}  accuracy={data["accuracy"]:.6f}',style='main')
            self.progress.advance(self.task)
        elif kind=='generation':
            if not self.quiet:
                self.console.print(f'{data["generation"]:4d} | {data["evaluated"]:9d} | {data["unique_evaluations"]:9d} | '
                    +' | '.join(f'{data[key]:.6f}' for key in ('best','mean','worst','std')),style='main')
            self.progress.advance(self.task)


def execute(console,method,config,grid,direct,quiet):
    console.print(f'Población={config.population} · generaciones={config.generations} · '
        f'mutación={config.mutation:g} · cruce={config.crossover:g} · élites={config.elite} · '
        f'folds={config.folds} · semilla={config.seed}',style='secondary')
    if config.elite==config.population and method!='grid':
        console.print('Toda la población es élite: no habrá variación entre generaciones.',style='warning')
    with SearchDisplay(console,quiet) as display:
        results=compare_methods(config,grid,direct,display) if method=='compare' else [
            run_search(method,config,direct if method=='genetic-direct' else grid,display)]
    show_results(console,results)
    return results


def save(console,results,directory,plots):
    if not results:
        console.print('Aún no hay resultados para exportar.',style='warning');return
    files=export_results(results,directory)
    if plots:files.extend(export_plots(results,directory))
    for path in files:console.print(f'Guardado: {path}',style='secondary')


def menu(console,args,config,grid,direct,results):
    options=['Consultar información del conjunto Wine','Ejecutar Grid Search exhaustivo',
        'Ejecutar Grid Search genético','Ejecutar algoritmo genético directo','Comparar los tres métodos',
        'Visualizar estadísticas','Exportar resultados','Salir']
    while True:
        console.print(Panel('\n'.join(f'[bold #39FF88]{i}.[/] {text}' for i,text in enumerate(options,1)),
                            title='LAB / CONTROL',border_style='#193528',style='panel'))
        try:
            choice=Prompt.ask('Opción',choices=[str(i) for i in range(1,9)],console=console)
        except EOFError:return 0
        try:
            if choice=='8':return 0
            if choice=='1':show_dataset(console)
            elif choice in ('2','3','4','5'):
                method={'2':'grid','3':'genetic-grid','4':'genetic-direct','5':'compare'}[choice]
                results=execute(console,method,config,grid,direct,args.quiet)
            elif choice=='6':
                show_statistics(console,results)
                if args.plots and results:
                    for path in export_plots(results,args.output):console.print(f'Gráfica: {path}',style='secondary')
            elif choice=='7':
                if not results:show_results(console,results);continue
                directory=Prompt.ask('Directorio de exportación',default=str(args.output),console=console)
                save(console,results,directory,args.plots)
        except (ValueError,OSError) as exc:console.print(f'Error: {exc}',style='error',markup=False)
        except EOFError:return 0


def _main(argv=None,console=None):
    args=parser().parse_args(argv)
    console=console or Console(theme=THEME)
    try:
        config=SearchConfig(**{key:getattr(args,key) for key in SearchConfig.__dataclass_fields__}).validate()
        grid=GridSpace(read_json(args.grid) if args.grid else None)
        direct=DirectSpace(read_json(args.bounds) if args.bounds else None)
        results=load_results(args.input) if args.input else []
        banner(console)
        if args.method=='info':show_dataset(console);return 0
        if args.method=='stats':
            if not results:raise ValueError('--method stats requiere --input results.json.')
            show_statistics(console,results)
            if args.plots:save(console,results,args.output,True)
            return 0
        if args.method:
            results=execute(console,args.method,config,grid,direct,args.quiet)
            save(console,results,args.output,args.plots)
            return 0
        return menu(console,args,config,grid,direct,results)
    except KeyboardInterrupt:
        console.print('\nInterrumpido: no se exporta una búsqueda incompleta como resultado final.',style='warning')
        return 130
    except (ValueError,OSError) as exc:
        console.print(f'Error: {exc}',style='error',markup=False)
        return 2


def main(argv=None,console=None):
    console=console or Console()
    with console.use_theme(THEME):
        return _main(argv,console)
