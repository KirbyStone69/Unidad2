"""Hybrid genetic programming: structure evolution plus bounded constant fitting."""
from collections import OrderedDict
from dataclasses import dataclass
import random
import numpy as np
from .expressions import (Node,constant,repair,random_tree,simplify,ARITY,
                          DEFAULT_OPERATORS,NAMED)
from .optimization import fit_affine,optimize_constants,structural_seeds,check_cancel

OPS = DEFAULT_OPERATORS


def metrics(y,pred):
    y=np.asarray(y,dtype=float); pred=np.asarray(pred,dtype=float)
    with np.errstate(over='ignore',invalid='ignore'):
        mse=float(np.mean((y-pred)**2)); variance=float(np.var(y))
    if not np.isfinite(mse): return float('inf'),float('inf'),float('-inf')
    nmse=mse/max(variance,1e-12)
    return mse,nmse,1-nmse


@dataclass(frozen=True)
class Config:
    population: int = 100
    generations: int = 100
    max_depth: int = 6
    crossover: float = .8
    mutation: float = .35
    seed: int = 42
    operators: tuple = DEFAULT_OPERATORS
    max_nodes: int = 127
    local_search: int = 4
    optimizer_evaluations: int = 100
    complexity: float = 1e-5
    validation_fraction: float = .2
    target_nmse: float = 1e-8
    cache_size: int = 5000
    elite_count: int = 2
    population_samples: int = 5

    def validate(self):
        ranges={'population':(2,1000),'generations':(0,10000),'max_depth':(1,10),
                'max_nodes':(1,511),'local_search':(0,12),'optimizer_evaluations':(1,1000),
                'cache_size':(1,100000),'seed':(0,2**32-1),
                'elite_count':(1,self.population),'population_samples':(0,20)}
        for name,(low,high) in ranges.items():
            value=getattr(self,name)
            if not isinstance(value,int) or not low<=value<=high:
                raise ValueError(f'{name} debe ser entero entre {low} y {high}.')
        for name,low,high in [('crossover',0,1),('mutation',0,1),('complexity',0,1),
                              ('validation_fraction',0,.4),('target_nmse',0,1)]:
            value=getattr(self,name)
            if not np.isfinite(value) or not low<=value<=high:
                raise ValueError(f'{name} debe estar entre {low} y {high}.')
        if not self.operators or any(op not in ARITY for op in self.operators):
            raise ValueError('Selecciona funciones válidas para la búsqueda.')
        if not set(('+','*'))<=set(self.operators):
            raise ValueError('La gramática requiere suma y multiplicación para calibrar constantes.')


@dataclass(frozen=True)
class Candidate:
    tree: Node
    mse: float
    nmse: float
    r2: float


@dataclass(frozen=True)
class Snapshot:
    generation: int
    tree: Node
    mse: float
    nmse: float
    r2: float
    validation_nmse: float | None = None
    nodes: int = 1
    diversity: float = 1.
    stalled: int = 0
    evaluations: int = 0
    train_count: int = 0
    validation_count: int = 0
    elites: tuple = ()
    population_sample: tuple = ()
    population_size: int = 0


class Evolution:
    def __init__(self,x,y,config,cancel=None):
        config.validate(); self.config=config; self.cancel=cancel
        check_cancel(cancel)
        x=np.asarray(x,dtype=float).copy(); y=np.asarray(y,dtype=float).copy()
        if x.ndim!=1 or x.shape!=y.shape or len(x)<2 or not np.isfinite([x,y]).all():
            raise ValueError('Se requieren al menos dos pares numéricos finitos.')
        if np.max(np.abs(y))>1e6 or np.max(np.abs(x))>1e6:
            raise ValueError('Escala los datos: el rango numérico protegido es ±1e6.')
        # Isolated RNG for the split: held-out y cannot influence initialization.
        order=np.random.default_rng(config.seed).permutation(len(x))
        count=max(1,int(len(x)*config.validation_fraction)) if config.validation_fraction and len(x)>=10 else 0
        self.validation_indices=np.sort(order[:count])
        self.train_indices=np.sort(order[count:])
        self.x=x[self.train_indices]; self.y=y[self.train_indices]
        self.variance=max(float(np.var(self.y)),1e-12)
        self.validation_x=x[self.validation_indices]; self.validation_y=y[self.validation_indices]
        self.rng=random.Random(config.seed); self.generation=0; self.stalled=0
        self.cache=OrderedDict(); self.evaluations=0; self.local_evaluations=0
        self.best_tree=constant(float(np.mean(self.y))); self.best_mse=metrics(self.y,self.best_tree.evaluate(self.x))[0]
        self.population=[self.best_tree]
        for i in range(config.population-1):
            check_cancel(cancel)
            self.population.append(self._bounded(random_tree(self.rng,self.rng.randint(1,config.max_depth),i%2==0,config.operators)))
        self.library=list(structural_seeds(self.rng,config.operators,self.x)); self.seed_cursor=0
        self._rank()

    def _bounded(self,tree):
        return simplify(repair(tree,self.config.max_depth,self.config.max_nodes))

    def _valid(self,tree):
        return tree.height<=self.config.max_depth and tree.size<=self.config.max_nodes

    def _mse(self,tree):
        check_cancel(self.cancel)
        if tree in self.cache:
            self.cache.move_to_end(tree); return self.cache[tree]
        value=metrics(self.y,tree.evaluate(self.x))[0]
        self.evaluations+=1; self.cache[tree]=value
        if len(self.cache)>self.config.cache_size: self.cache.popitem(last=False)
        return value

    def _fitness(self,tree):
        return self._mse(tree)/self.variance+self.config.complexity*tree.size

    def _rank(self):
        candidate=min(self.population,key=lambda n:(self._mse(n),n.size))
        mse=self._mse(candidate)
        if mse<self.best_mse or (mse==self.best_mse and candidate.size<self.best_tree.size):
            self.best_tree=candidate; self.best_mse=mse
        self.population.sort(key=self._fitness)

    def _signature(self,tree):
        if tree.is_constant: return '#'
        return (tree.value,tuple(self._signature(c) for c in tree.children))

    def _elite_indices(self):
        champion=next((i for i,n in enumerate(self.population) if n==self.best_tree),0)
        return ([champion]+[i for i in range(len(self.population)) if i!=champion])[:self.config.elite_count]

    def snapshot(self):
        elite_indices=self._elite_indices(); elite_set=set(elite_indices)
        remaining=[i for i in range(len(self.population)) if i not in elite_set]
        count=min(self.config.population_samples,len(remaining))
        sampled=[remaining[i] for i in np.linspace(0,len(remaining)-1,count,dtype=int)] if count else []
        def candidate(index):
            node=self.population[index]; mse=self._mse(node); nmse=mse/self.variance
            return Candidate(node,mse,nmse,1-nmse)
        tree=self.best_tree
        validation=metrics(self.validation_y,tree.evaluate(self.validation_x))[1] if len(self.validation_x) else None
        return Snapshot(self.generation,tree,*metrics(self.y,tree.evaluate(self.x)),
                        validation,tree.size,len({self._signature(n) for n in self.population})/len(self.population),
                        self.stalled,self.evaluations+self.local_evaluations,len(self.x),len(self.validation_x),
                        tuple(candidate(i) for i in elite_indices),tuple(candidate(i) for i in sampled),len(self.population))

    @property
    def converged(self):
        if self.config.target_nmse<=0: return False
        return self.best_mse/self.variance<=self.config.target_nmse

    def _select(self):
        indices=self.rng.sample(range(len(self.population)),min(4,len(self.population)))
        return self.population[min(indices)]

    def _mutate(self,tree):
        rng=self.rng; paths=list(tree.paths()); path=rng.choice(paths); node=tree.at(path)
        kind=rng.random()
        constants=[p for p in paths if tree.at(p).is_constant and tree.at(p).value not in NAMED]
        if kind<.35 and constants:
            path=rng.choice(constants); value=float(tree.at(path).value)
            replacement=constant(value+rng.gauss(0,max(.2,abs(value)*.25)))
        elif kind<.55 and node.children:
            options=[op for op in self.config.operators if ARITY[op]==len(node.children)]
            replacement=Node(rng.choice(options),node.children)
        elif kind<.7 and node.children:
            replacement=rng.choice(node.children)
        else:
            replacement=random_tree(rng,min(3,max(0,self.config.max_depth-len(path))),operators=self.config.operators)
        return self._bounded(tree.replace(path,replacement))

    def _polish(self,tree):
        check_cancel(self.cancel)
        calibrated=fit_affine(tree,self.x,self.y)
        if self._valid(calibrated): tree=calibrated
        result=optimize_constants(tree,self.x,self.y,self.config.optimizer_evaluations,self.cancel)
        self.local_evaluations+=result.calls
        candidate=simplify(result.tree)
        return candidate if self._valid(candidate) and self._mse(candidate)<=self._mse(tree) else tree

    def step(self):
        check_cancel(self.cancel)
        cfg=self.config; rng=self.rng; previous=self.best_mse
        # Always preserve the raw-error champion, even when parsimony favors another.
        protected=[self.population[i] for i in self._elite_indices()]
        if cfg.elite_count==cfg.population:
            self.generation+=1; self.stalled+=1
            return self.snapshot()
        result=list(protected)
        seen=set(result); attempts=0
        immigrant_rate=.30 if self.stalled>=12 else .10
        while len(result)<cfg.population:
            check_cancel(self.cancel); attempts+=1
            if rng.random()<immigrant_rate:
                child=self._bounded(random_tree(rng,rng.randint(1,cfg.max_depth),operators=cfg.operators))
            else:
                child=self._select()
                if rng.random()<cfg.crossover:
                    donor=self._select()
                    child=child.replace(rng.choice(list(child.paths())),donor.at(rng.choice(list(donor.paths()))))
                if rng.random()<min(.9,cfg.mutation*(1.5 if self.stalled>=12 else 1)):
                    child=self._mutate(child)
                child=self._bounded(child)
            if child not in seen or attempts>cfg.population*5:
                result.append(child); seen.add(child)
        self.population=result; self._rank()
        # Spend at most local_search fits, split between new grammar proposals and elites.
        additions=[]; proposals=max(1,(cfg.local_search+1)//2) if cfg.local_search else 0
        for _ in range(proposals):
            for _attempt in range(len(self.library)):
                seed=self.library[self.seed_cursor%len(self.library)]; self.seed_cursor+=1
                if self._valid(seed):
                    additions.append(self._polish(seed)); break
        candidates=sorted(self.population,key=self._mse)
        for tree in candidates[:cfg.local_search-proposals]: additions.append(self._polish(tree))
        self.population+=additions; self._rank()
        chosen=list(protected)
        if self.best_tree not in chosen: chosen.append(self.best_tree)
        for node in self.population:
            if len(chosen)>=cfg.population: break
            if node not in chosen:
                chosen.append(node)
                if len(chosen)==cfg.population: break
        while len(chosen)<cfg.population: chosen.append(self.population[len(chosen)%len(self.population)])
        self.population=chosen; self._rank(); self.generation+=1
        self.stalled=0 if self.best_mse<previous-max(abs(previous)*1e-8,1e-16) else self.stalled+1
        return self.snapshot()
