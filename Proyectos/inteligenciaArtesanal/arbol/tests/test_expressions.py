import random
import numpy as np
import pytest
from laboratorio.engine import Node, random_tree, repair

@pytest.mark.parametrize('op,expected',[('sin',np.sin),('cos',np.cos),('square',np.square),('cube',lambda x:x**3),('exp',np.exp),('log',lambda x:np.log(np.maximum(np.abs(x),1e-12))),('sqrt',lambda x:np.sqrt(np.abs(x))),('tanh',np.tanh),('abs',np.abs)])
def test_unary_functions(op,expected):
    x=np.array([-.5,0,.7])
    node=Node(op,(Node('x'),))
    np.testing.assert_allclose(node.evaluate(x),expected(x))
    assert op in str(node) or op in ('square','cube')

@pytest.mark.parametrize('op',['+','sin','cos','exp','log','sqrt','square','cube','/'])
def test_extreme_values_remain_finite(op):
    children=(Node('x'),Node('0')) if op in ('+','/') else (Node('x'),)
    assert np.isfinite(Node(op,children).evaluate(np.array([-1e100,0,1e100]))).all()

@pytest.mark.parametrize('value,children',[('cos',()),('+',(Node('x'),)),('unknown',(Node('x'),)),('nan',()),('inf',())])
def test_invalid_expressions_rejected(value,children):
    with pytest.raises(ValueError): Node(value,children)


def test_decimal_constants_and_named_constants():
    for text,value in [('7.23',7.23),('pi',np.pi),('e',np.e)]:
        np.testing.assert_allclose(Node(text).evaluate(np.zeros(3)),value)


def test_unary_tree_repair_and_generation():
    from laboratorio.expressions import simplify
    tree=Node('cos',(Node('*',(Node('7.23'),Node('cube',(Node('x'),)))),))
    assert tree.size==5 and tree.height==3
    assert repair(tree,2).height<=2
    assert simplify(Node('+',(Node('x'),Node('0'))))==Node('x')
    assert simplify(Node('*',(Node('2'),Node('3'))))==Node('6')
    rng=random.Random(5)
    trees=[random_tree(rng,4,operators=('+','cos')) for _ in range(40)]
    assert any(n.value=='cos' for t in trees for n in [t.at(p) for p in t.paths()])
    assert all(t.at(p).value not in ('sin','exp') for t in trees for p in t.paths())


def test_export_keeps_full_precision_and_numpy_function_names():
    tree=Node('cos',(Node('*',(Node('7.23456789123456'),Node('cube',(Node('x'),)))),))
    source=tree.to_python()
    assert '7.23456789123456' in source
    assert 'np.cos' in source and '** 3' in source
    assert Node('pi').to_python()=='np.pi'

@pytest.mark.parametrize('op',['+','-','*','/','sin','cos','exp','log','sqrt','square','cube','abs','tanh'])
def test_export_preserves_protected_evaluation(op):
    children=(Node('x'),Node('0')) if op in ('+','-','*','/') else (Node('x'),)
    tree=Node(op,children); x=np.array([-1e100,-1.,0.,1.,1e100])
    # Only test our generated expression, never arbitrary user input.
    exported=eval(tree.to_python(),{'np':np,'x':x,'__builtins__':{}})
    np.testing.assert_allclose(exported,tree.evaluate(x),rtol=1e-12,atol=1e-12)

@pytest.mark.parametrize('op,expected',[('atan',np.arctan),('sigmoid',lambda x:np.exp(-np.logaddexp(0.,-x))),('neg',np.negative)])
def test_additional_functions_and_export(op,expected):
    x=np.array([-1e6,-2.,0.,3.,1e6]);tree=Node(op,(Node('x'),))
    np.testing.assert_allclose(tree.evaluate(x),expected(x))
    exported=eval(tree.to_python(),{'np':np,'x':x,'__builtins__':{}})
    np.testing.assert_allclose(exported,expected(x))
    assert np.isfinite(tree.evaluate(np.array([-np.inf,np.nan,np.inf]))).all()
