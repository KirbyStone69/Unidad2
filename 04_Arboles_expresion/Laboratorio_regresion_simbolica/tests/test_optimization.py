import random
import numpy as np
import pytest
from laboratorio.expressions import Node,constant

def test_affine_calibration_and_local_constants():
    from laboratorio.optimization import fit_affine,optimize_constants
    x=np.linspace(0,1,45); y=3.4+8.2*np.cos(5.6*x**3)
    shape=Node('cos',(Node('*',(constant(5),Node('cube',(Node('x'),)))),))
    initial=fit_affine(shape,x,y)
    result=optimize_constants(initial,x,y,max_calls=120)
    assert np.mean((y-result.tree.evaluate(x))**2)<1e-14
    assert 0<result.calls<=120
    assert shape.at((0,0)).value=='5'


def test_budget_and_cancellation():
    from laboratorio.optimization import optimize_constants,SearchCancelled
    x=np.linspace(-1,1,20)
    tree=Node('+',(constant(0),Node('*',(constant(1),Node('x')))))
    result=optimize_constants(tree,x,2*x+7,max_calls=2)
    assert result.calls<=2
    assert np.mean((2*x+7-result.tree.evaluate(x))**2)<=np.mean((2*x+7-tree.evaluate(x))**2)
    with pytest.raises(SearchCancelled): optimize_constants(tree,x,x,cancel=lambda:True)


def test_structural_library_respects_enabled_functions():
    from laboratorio.optimization import structural_seeds
    operators=('+','-','*','/','square')
    trees=list(structural_seeds(random.Random(42),operators,np.linspace(-2,2,20)))
    assert len(trees)>3
    assert all(n.at(p).value in operators or not n.at(p).children for n in trees for p in n.paths())
