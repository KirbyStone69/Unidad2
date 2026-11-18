"""Budgeted local search and data-independent structural proposals for GP."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares
from .expressions import Node,constant,apply_operator,NAMED,LIMIT

class SearchCancelled(Exception):
    """Cooperative cancellation, including inside SciPy finite differences."""

class _BudgetReached(Exception):
    pass

@dataclass(frozen=True)
class OptimizationResult:
    tree: Node
    calls: int


def check_cancel(cancel):
    if cancel is not None and cancel(): raise SearchCancelled()


def fit_affine(tree,x,y):
    """Fit output offset/scale by linear least squares; keep the original if worse."""
    values=tree.evaluate(x)
    design=np.column_stack((np.ones_like(values),values))
    try:
        offset,scale=np.linalg.lstsq(design,y,rcond=None)[0]
    except np.linalg.LinAlgError:
        return tree
    candidate=Node('+',(constant(np.clip(offset,-LIMIT,LIMIT)),
                        Node('*',(constant(np.clip(scale,-LIMIT,LIMIT)),tree))))
    return candidate if np.mean((y-candidate.evaluate(x))**2)<=np.mean((y-values)**2) else tree


def optimize_constants(tree,x,y,max_calls=100,cancel=None):
    """Count every residual evaluation, including Jacobian finite differences.

    Only numeric terminals are fitted. Named pi/e remain fixed. The best evaluated
    vector is returned even when the evaluation budget expires mid-Jacobian.
    """
    check_cancel(cancel)
    paths=[p for p in tree.paths() if tree.at(p).is_constant and tree.at(p).value not in NAMED][:10]
    if not paths or max_calls<=0: return OptimizationResult(tree,0)
    indices={path:i for i,path in enumerate(paths)}
    x=np.asarray(x,dtype=float); y=np.asarray(y,dtype=float)
    def compile_node(node,path=()):
        if path in indices:
            index=indices[path]
            return lambda params:np.full_like(x,params[index])
        if not node.children:
            values=node.evaluate(x)
            return lambda params:values
        children=[compile_node(c,path+(i,)) for i,c in enumerate(node.children)]
        return lambda params:apply_operator(node.value,[child(params) for child in children])
    evaluate=compile_node(tree)
    initial=np.array([float(tree.at(p).value) for p in paths])
    bound=min(LIMIT,max(1000.,float(np.max(np.abs(initial)))*2,float(np.max(np.abs(y)))*10))
    initial=np.clip(initial,-bound+1e-9,bound-1e-9)
    best=initial.copy(); best_error=float(np.mean((y-tree.evaluate(x))**2)); calls=0
    yscale=max(float(np.std(y)),1.)
    def residual(params):
        nonlocal calls,best,best_error
        check_cancel(cancel)
        if calls>=max_calls: raise _BudgetReached()
        calls+=1
        difference=evaluate(params)-y
        error=float(np.mean(difference**2))
        if error<best_error: best_error=error; best=params.copy()
        return difference/yscale
    try:
        least_squares(residual,initial,bounds=(-bound,bound),max_nfev=max_calls,
                      x_scale='jac',ftol=1e-10,xtol=1e-10,gtol=1e-10)
    except (_BudgetReached,ValueError,np.linalg.LinAlgError,FloatingPointError):
        pass
    result=tree
    for path,value in zip(paths,best): result=result.replace(path,constant(value))
    # Bound clipping and simplification cannot silently worsen the candidate.
    if np.mean((y-result.evaluate(x))**2)>np.mean((y-tree.evaluate(x))**2): result=tree
    return OptimizationResult(result,calls)


def structural_seeds(rng,operators,x):
    """Generic grammar curriculum, not inferred labels or a known target formula.

    Powers, polynomial sums, elementary functions and frequency/phase proposals
    complement random subtrees. All returned structures still undergo GP selection.
    Only the magnitude of x determines the initial argument scale; y is not used.
    """
    ops=set(operators); variable=Node('x')
    bases=[variable]
    if 'square' in ops: bases.append(Node('square',(variable,)))
    elif '*' in ops: bases.append(Node('*',(variable,variable)))
    if 'cube' in ops: bases.append(Node('cube',(variable,)))
    elif '*' in ops: bases.append(Node('*',(variable,Node('*',(variable,variable)))))
    if 'square' in ops: bases.append(Node('square',(Node('square',(variable,)),)))
    yield from bases
    if {'+','*'}<=ops:
        for degree in range(2,len(bases)+1):
            tree=constant(0)
            for basis in bases[:degree]: tree=Node('+',(tree,Node('*',(constant(1),basis))))
            yield tree
    if '*' not in ops: return
    # Every family gets an early proposal before the longer frequency curriculum.
    scale=max(float(np.max(np.abs(x))),1e-3)
    if {'/','+'}<=ops:
        for base in bases:
            yield Node('/',(constant(1),Node('+',(constant(1),Node('*',(constant(1/scale),base))))))
    # Interleave families/powers across frequencies instead of exhausting one family.
    scale=max(float(np.max(np.abs(x))),1e-3)
    for frequency in (1.,4.,8.,16.,.5,2.,24.):
        proposals=[]
        for base in bases:
            base_scale=max(float(np.max(np.abs(base.evaluate(x)))),1e-3)
            for op in ('sin','cos','exp','log','sqrt','tanh','abs','atan','sigmoid','neg'):
                if op not in ops: continue
                if op not in ('sin','cos') and frequency!=1.: continue
                argument=Node('*',(constant(frequency/base_scale),base))
                proposals.append(Node(op,(argument,)))
                if op in ('sin','cos') and '+' in ops:
                    proposals.append(Node(op,(Node('+',(argument,constant(rng.uniform(-np.pi,np.pi)))),)))
        rng.shuffle(proposals)
        yield from proposals

