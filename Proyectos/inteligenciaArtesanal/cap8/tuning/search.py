"""Exhaustive search and two elitist DEAP searches using the same fitness."""
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import random
from time import perf_counter
import numpy as np
from deap import tools
from .spaces import GridSpace, DirectSpace, SearchConfig, make_toolbox
from .evaluation import WineEvaluator, versions, compatibility_info

METHODS=('grid','genetic-grid','genetic-direct')


@dataclass
class SearchResult:
    method: str
    config: dict
    space: dict
    cv: dict
    best_params: dict
    best_accuracy: float
    elapsed_seconds: float
    fitness_requests: int
    evaluations: list
    history: list
    baseline: dict
    grid_guarantee: bool
    versions: dict
    compatibility: dict
    created_at: str

    def to_dict(self):
        return asdict(self)


@contextmanager
def seeded_random(seed):
    # DEAP uses the Python random module. Preserve the caller's RNG state.
    state=random.getstate()
    random.seed(seed)
    try:
        yield
    finally:
        random.setstate(state)


def run_search(method, config=None, space=None, callback=None):
    config=(config or SearchConfig()).validate()
    if method not in METHODS:
        raise ValueError(f'Método desconocido: {method}')
    space=space or (DirectSpace() if method=='genetic-direct' else GridSpace())
    if (method=='genetic-direct') != isinstance(space,DirectSpace):
        raise ValueError('El espacio no corresponde al método elegido.')
    emit=callback or (lambda kind,data:None)
    evaluator=WineEvaluator(config.folds,config.seed)
    # Separate cache and timer: baseline does not warm up a search's cache.
    emit('status',{'message':'Evaluando AdaBoost por defecto como referencia'})
    baseline=WineEvaluator(config.folds,config.seed).evaluate({'n_estimators':50,'learning_rate':1.})
    emit('start',{'method':method,'total':space.size if isinstance(space,GridSpace) and method=='grid' else config.generations+1})
    history=[]
    start=perf_counter()
    with seeded_random(config.seed):
        if method=='grid':
            best=None
            for index,params in enumerate(space.combinations(),1):
                row=evaluator.evaluate(params)
                if best is None or row['accuracy']>best['accuracy']:
                    best=row
                emit('evaluation',{'index':index,'total':space.size,**row})
        else:
            toolbox=make_toolbox(space,config)
            toolbox.register('evaluate',lambda ind:(evaluator.evaluate(space.decode(ind))['accuracy'],))
            population=toolbox.population(n=config.population)
            hof=tools.HallOfFame(1)
            for generation in range(config.generations+1):
                if generation:
                    # Elites are cloned and never passed through variation operators.
                    elites=list(map(toolbox.clone,tools.selBest(population,config.elite)))
                    offspring=list(map(toolbox.clone,toolbox.select(population,config.population-config.elite)))
                    for a,b in zip(offspring[::2],offspring[1::2]):
                        if random.random()<config.crossover:
                            toolbox.mate(a,b)
                            del a.fitness.values,b.fitness.values
                    for individual in offspring:
                        if random.random()<config.mutation:
                            toolbox.mutate(individual)
                            del individual.fitness.values
                    population=elites+offspring
                invalid=[ind for ind in population if not ind.fitness.valid]
                before=len(evaluator.evaluations)
                for individual in invalid:
                    individual.fitness.values=toolbox.evaluate(individual)
                hof.update(population)
                fitness=np.array([ind.fitness.values[0] for ind in population])
                stats={'generation':generation,'population':len(population),'evaluated':len(invalid),
                       'unique_evaluations':len(evaluator.evaluations)-before,
                       'best':float(fitness.max()),'mean':float(fitness.mean()),
                       'worst':float(fitness.min()),'std':float(fitness.std()),
                       'best_params':space.decode(hof[0])}
                history.append(stats)
                emit('generation',stats)
            best={'accuracy':hof[0].fitness.values[0],**space.decode(hof[0])}
    elapsed=perf_counter()-start
    result=SearchResult(method=method,config=config.to_dict(),space=space.to_dict(),
        cv=evaluator.cv_metadata,best_params={k:best[k] for k in ('n_estimators','learning_rate')},
        best_accuracy=best['accuracy'],elapsed_seconds=elapsed,fitness_requests=evaluator.requests,
        evaluations=evaluator.evaluations,history=history,baseline=baseline,
        grid_guarantee=method=='grid',versions=versions(),compatibility=compatibility_info(),
        created_at=datetime.now(timezone.utc).isoformat())
    emit('finished',{'method':method,'accuracy':result.best_accuracy})
    return result


def compare_methods(config=None,grid=None,direct=None,callback=None):
    config=config or SearchConfig()
    return [run_search(method,config,direct if method=='genetic-direct' else grid,callback)
            for method in METHODS]
