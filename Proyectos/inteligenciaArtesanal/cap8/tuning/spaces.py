"""Validated search spaces and DEAP operators; no model training here."""
from dataclasses import dataclass, asdict
import math
import random
from numbers import Real, Integral
import numpy as np
from deap import base, tools
from sklearn.model_selection import ParameterGrid

KEYS = ('n_estimators', 'learning_rate')


def finite_number(value):
    try:
        return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def validate_params(params):
    if set(params) != set(KEYS):
        raise ValueError('Solo se admiten n_estimators y learning_rate; SAMME es fijo.')
    n, rate = params['n_estimators'], params['learning_rate']
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError('n_estimators debe ser un entero positivo.')
    if not finite_number(rate) or rate <= 0:
        raise ValueError('learning_rate debe ser finito y positivo.')


@dataclass(frozen=True)
class SearchConfig:
    population: int = 20
    generations: int = 5
    mutation: float = .3
    crossover: float = .8
    seed: int = 42
    elite: int = 1
    folds: int = 5
    tournament: int = 2
    eta: float = 20.

    def validate(self):
        for name, low, high in [('population',2,10000), ('generations',0,100000),
                                ('seed',0,2**32-1), ('elite',1,self.population),
                                ('folds',2,48), ('tournament',1,self.population)]:
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high:
                raise ValueError(f'{name}: entero entre {low} y {high}.')
        for name in ('mutation','crossover'):
            if not finite_number(getattr(self,name)) or not 0<=getattr(self,name)<=1:
                raise ValueError(f'{name}: probabilidad finita entre 0 y 1.')
        if not finite_number(self.eta) or self.eta<=0:
            raise ValueError('eta debe ser finito y positivo.')
        return self

    def to_dict(self):
        return asdict(self)


class FitnessMax(base.Fitness):
    weights=(1.,)


class Individual(list):
    def __init__(self, values=()):
        super().__init__(values)
        self.fitness=FitnessMax()


class GridSpace:
    kind='grid'

    def __init__(self, grid=None):
        if grid is None:
            grid={'n_estimators':list(range(10,101,10)),
                  'learning_rate':np.logspace(-2,0,10).tolist()}
        if not isinstance(grid,dict) or set(grid)!=set(KEYS):
            raise ValueError('La cuadrícula requiere n_estimators y learning_rate únicamente.')
        self.grid={}
        for key in KEYS:
            values=grid[key]
            if not isinstance(values,(list,tuple)) or not values:
                raise ValueError(f'{key}: lista de valores no vacía requerida.')
            # Repeated values are not distinct configurations.
            for value in values:
                if not finite_number(value):
                    raise ValueError(f'{key}: cada valor debe ser numérico y finito.')
            unique=list(dict.fromkeys(values))
            for value in unique:
                validate_params({'n_estimators':value if key=='n_estimators' else 1,
                                 'learning_rate':value if key=='learning_rate' else 1.})
            self.grid[key]=[int(v) if key=='n_estimators' else float(v) for v in unique]
        self.low=[0,0]
        self.high=[len(self.grid[k])-1 for k in KEYS]
        self.size=math.prod(len(v) for v in self.grid.values())

    def create(self):
        return Individual(random.randint(0,high) for high in self.high)

    def decode(self, genes):
        if len(genes)!=len(KEYS) or any(isinstance(v,bool) or not isinstance(v,Integral)
                or not 0<=v<=high for v,high in zip(genes,self.high)):
            raise ValueError('Cromosoma discreto inválido: se requieren índices de la cuadrícula.')
        return {key:self.grid[key][int(index)] for key,index in zip(KEYS,genes)}

    def combinations(self):
        return ParameterGrid(self.grid)

    def to_dict(self):
        return {'kind':self.kind,'grid':self.grid,'size':self.size}


class DirectSpace:
    kind='direct'

    def __init__(self, bounds=None):
        if bounds is None:
            bounds={'n_estimators':[1,100], 'learning_rate':[.01,1.]}
        if not isinstance(bounds,dict) or set(bounds)!=set(KEYS):
            raise ValueError('Los rangos requieren n_estimators y learning_rate.')
        self.bounds={}
        for key in KEYS:
            interval=bounds[key]
            if not isinstance(interval,(list,tuple)) or len(interval)!=2:
                raise ValueError(f'{key}: se requiere [mínimo, máximo].')
            low,high=interval
            if not finite_number(low) or not finite_number(high) or low>=high:
                raise ValueError(f'{key}: límites finitos y mínimo < máximo requeridos.')
            if key=='n_estimators' and (low!=int(low) or high!=int(high) or low<1):
                raise ValueError('Los límites de n_estimators deben ser enteros positivos.')
            if key=='learning_rate' and low<=0:
                raise ValueError('learning_rate debe ser positivo.')
            self.bounds[key]=[float(low),float(high)]
        self.low=[self.bounds[k][0] for k in KEYS]
        self.high=[self.bounds[k][1] for k in KEYS]

    def create(self):
        return Individual(random.uniform(low,high) for low,high in zip(self.low,self.high))

    def decode(self, genes):
        if len(genes)!=len(KEYS) or any(not finite_number(v) or not low<=v<=high
                for v,low,high in zip(genes,self.low,self.high)):
            raise ValueError('Cromosoma real fuera de límites o no finito.')
        # Python round uses ties-to-even; only the integer hyperparameter is rounded.
        return {'n_estimators':int(round(genes[0])), 'learning_rate':float(genes[1])}

    def to_dict(self):
        return {'kind':self.kind,'bounds':self.bounds}


def make_toolbox(space, config):
    config.validate()
    toolbox=base.Toolbox()
    toolbox.register('individual',space.create)
    toolbox.register('population',tools.initRepeat,list,toolbox.individual)
    toolbox.register('select',tools.selTournament,tournsize=config.tournament)
    if isinstance(space,GridSpace):
        toolbox.register('mate',tools.cxUniform,indpb=.5)
        toolbox.register('mutate',tools.mutUniformInt,low=space.low,up=space.high,indpb=1/len(KEYS))
    else:
        toolbox.register('mate',tools.cxSimulatedBinaryBounded,low=space.low,up=space.high,eta=config.eta)
        toolbox.register('mutate',tools.mutPolynomialBounded,low=space.low,up=space.high,
                         eta=config.eta,indpb=1/len(KEYS))
    return toolbox
