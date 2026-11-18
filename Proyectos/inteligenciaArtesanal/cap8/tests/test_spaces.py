import random
import math
import pytest
from tuning.spaces import GridSpace, DirectSpace, SearchConfig, make_toolbox


def test_default_grid_matches_modern_book_space():
    space=GridSpace()
    assert space.size==100
    assert space.decode([0,0])=={'n_estimators':10,'learning_rate':.01}
    assert space.decode([9,9])=={'n_estimators':100,'learning_rate':1.0}
    with pytest.raises(ValueError): space.decode([10,0])


def test_real_conversion_rounds_integer_only():
    space=DirectSpace()
    assert space.decode([69.4,.628])=={'n_estimators':69,'learning_rate':.628}
    assert space.decode([1.,.01])['n_estimators']==1
    assert space.decode([100.,1.])['n_estimators']==100
    for genes in ([0,.1],[101,.1],[20,float('nan')],[50,2],[1]):
        with pytest.raises(ValueError): space.decode(genes)


@pytest.mark.parametrize('space',[GridSpace(),DirectSpace()])
def test_creation_crossover_mutation_remain_valid(space):
    state=random.getstate(); random.seed(42)
    try:
        toolbox=make_toolbox(space,SearchConfig())
        for _ in range(250):
            a,b=toolbox.individual(),toolbox.individual()
            assert not a.fitness.valid
            toolbox.mate(a,b); toolbox.mutate(a); toolbox.mutate(b)
            for individual in (a,b):
                params=space.decode(individual)
                assert params['n_estimators']>=1
                assert math.isfinite(params['learning_rate'])
    finally: random.setstate(state)


@pytest.mark.parametrize('kwargs',[
    {'population':1},{'generations':-1},{'mutation':float('nan')},
    {'crossover':1.1},{'elite':21},{'elite':0},{'folds':1},{'folds':49},
    {'seed':-1},{'tournament':0},{'eta':0},{'population':True},
])
def test_config_validation(kwargs):
    with pytest.raises(ValueError): SearchConfig(**kwargs).validate()


@pytest.mark.parametrize('grid',[
    {},{'n_estimators':[],'learning_rate':[.1]},
    {'n_estimators':[1.5],'learning_rate':[.1]},
    {'n_estimators':[10],'learning_rate':[0]},
    {'n_estimators':[10],'learning_rate':[float('inf')]},
    {'n_estimators':[10],'learning_rate':[.1],'algorithm':['SAMME.R']},
])
def test_invalid_grids(grid):
    with pytest.raises(ValueError): GridSpace(grid)


@pytest.mark.parametrize('bounds',[
    {'n_estimators':[100,1],'learning_rate':[.01,1]},
    {'n_estimators':[1,100],'learning_rate':[0,1]},
    {'n_estimators':[1.2,100],'learning_rate':[.01,1]},
    {'n_estimators':[1,1],'learning_rate':[.01,1]},
])
def test_invalid_direct_bounds(bounds):
    with pytest.raises(ValueError): DirectSpace(bounds)


def test_nested_grid_value_is_a_validation_error():
    with pytest.raises(ValueError):
        GridSpace({'n_estimators':[[2]],'learning_rate':[.1]})
