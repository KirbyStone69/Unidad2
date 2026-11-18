import random
import numpy as np
import pytest
from laboratorio.expressions import ARITY,Node,repair,random_tree

@pytest.mark.parametrize('depth',[1,3,6,10])
@pytest.mark.parametrize('budget',[1,3,15,31])
def test_repair_invariants_across_random_grammars(depth,budget):
    rng=random.Random(depth*100+budget)
    for _ in range(12):
        tree=random_tree(rng,6,full=True,operators=tuple(ARITY))
        original=str(tree)
        fixed=repair(tree,depth,budget)
        assert fixed.height<=depth and fixed.size<=budget
        assert str(tree)==original
        assert repair(fixed,depth,budget)==fixed
        assert np.isfinite(fixed.evaluate(np.linspace(-10,10,61))).all()
        assert all(len(fixed.at(p).children)==ARITY[fixed.at(p).value] for p in fixed.paths() if fixed.at(p).children)

@pytest.mark.parametrize('op',[op for op,arity in ARITY.items() if arity==1])
def test_repair_each_unary_family(op):
    tree=Node(op,(Node('+',(Node('x'),Node('2.5'))),))
    fixed=repair(tree,1,3)
    assert fixed==Node(op,(Node('x'),))
    assert np.isfinite(fixed.evaluate(np.array([-1e100,0,1e100]))).all()
