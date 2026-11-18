import numpy as np
import pytest
from laboratorio.engine import Evolution,Config


def run_search(x,y,seed=42,**options):
    config=Config(population=70,generations=65,max_depth=6,seed=seed,**options)
    engine=Evolution(x,y,config)
    previous=engine.snapshot().mse
    for _ in range(config.generations):
        snapshot=engine.step()
        assert snapshot.mse<=previous+1e-12
        previous=snapshot.mse
        if engine.converged: break
    return engine

@pytest.mark.parametrize('seed',[7,42,91])
def test_cosine_cubic_discovery(seed):
    x=np.linspace(0,1,50); y=6.67+11*np.cos(7.23*x**3)
    engine=run_search(x,y,seed)
    s=engine.snapshot()
    assert s.nmse<1e-7, (s,str(s.tree))
    unseen=np.linspace(.003,.997,101)
    assert np.mean((s.tree.evaluate(unseen)-(6.67+11*np.cos(7.23*unseen**3)))**2)<1e-5
    assert s.validation_nmse<1e-6

@pytest.mark.parametrize('function',[lambda x:2.3+4.1*np.sin(3.6*x+.7),lambda x:1.2+2.4*np.exp(.8*x),lambda x:1.7-2.1*x+3.3*x*x,lambda x:1.4+2.2/(1+3.1*x*x)])
def test_other_families(function):
    x=np.linspace(-1,1,50)
    engine=run_search(x,function(x),13)
    assert engine.snapshot().nmse<1e-6, str(engine.snapshot().tree)


def test_limits_and_enabled_grammar():
    cfg=Config(population=30,max_depth=3,max_nodes=15,operators=('+','-','*','/'),local_search=1,validation_fraction=0)
    x=np.linspace(-1,1,20); e=Evolution(x,np.sin(x),cfg)
    for _ in range(8):
        e.step()
        assert len(e.population)==cfg.population
        assert all(n.height<=cfg.max_depth and n.size<=cfg.max_nodes for n in e.population)
        assert all(n.at(p).value in cfg.operators or not n.at(p).children for n in e.population for p in n.paths())
    assert 0<e.snapshot().diversity<=1
    assert e.snapshot().validation_nmse is None
    assert len(e.cache)<=cfg.cache_size


def test_validation_not_used_for_training_or_selection():
    x=np.linspace(-2,2,30); y=x*x
    cfg=Config(population=25,seed=3,local_search=1)
    a=Evolution(x,y,cfg)
    changed=y.copy(); changed[a.validation_indices]+=10000
    b=Evolution(x,changed,cfg)
    for _ in range(3): a.step(); b.step()
    assert a.snapshot().tree==b.snapshot().tree
    assert a.snapshot().mse==b.snapshot().mse
    assert a.snapshot().validation_nmse!=b.snapshot().validation_nmse


def test_deterministic_run_and_constant_data():
    x=np.linspace(-1,1,20); y=np.full_like(x,2.37)
    cfg=Config(population=20,seed=9,local_search=1)
    a=Evolution(x,y,cfg); b=Evolution(x,y,cfg)
    for _ in range(3): a.step(); b.step()
    assert a.snapshot()==b.snapshot()
    assert a.snapshot().mse<1e-20
    assert np.isfinite([a.snapshot().mse,a.snapshot().nmse,a.snapshot().r2]).all()

@pytest.mark.parametrize('options',[{'max_nodes':0},{'operators':('bad',)},{'validation_fraction':.8},{'target_nmse':-1},{'local_search':-1}])
def test_invalid_config(options):
    with pytest.raises(ValueError): Evolution(np.arange(10.),np.arange(10.),Config(**options))


def test_noisy_data_remains_an_approximation():
    x=np.linspace(0,1,50)
    noise=np.random.default_rng(309).normal(0,.12,len(x))
    y=2.8+4.6*np.cos(4.3*x**3)+noise
    cfg=Config(population=70,generations=20,seed=42)
    engine=Evolution(x,y,cfg)
    for _ in range(cfg.generations): engine.step()
    snapshot=engine.snapshot()
    assert snapshot.nmse<.02
    assert snapshot.validation_nmse<.05
    assert not engine.converged

@pytest.mark.parametrize('op,function',[('atan',lambda x:1.4+3.2*np.arctan(1.3*x)),('sigmoid',lambda x:.8+4.2/(1+np.exp(-1.7*x)))])
def test_discovery_with_extra_functions(op,function):
    operators=('+','-','*','/','square','cube',op)
    x=np.linspace(-2,2,60); y=function(x)
    engine=run_search(x,y,seed=42,operators=operators)
    snapshot=engine.snapshot()
    assert snapshot.nmse<1e-7,str(snapshot.tree)
    assert snapshot.validation_nmse<1e-6
    unseen=np.linspace(-1.95,1.95,91)
    assert np.mean((function(unseen)-snapshot.tree.evaluate(unseen))**2)<1e-5
