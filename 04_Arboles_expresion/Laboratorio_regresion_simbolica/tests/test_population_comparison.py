import numpy as np
import pytest
from laboratorio.engine import Config,Evolution,Snapshot

@pytest.mark.parametrize('count',[1,3,12])
def test_elites_are_real_members_and_survive_generation(count):
    cfg=Config(population=12,elite_count=count,population_samples=4,local_search=0,target_nmse=0)
    x=np.linspace(-1,1,20);e=Evolution(x,np.cos(x),cfg)
    snapshot=e.snapshot();protected=[candidate.tree for candidate in snapshot.elites]
    assert len(protected)==count
    assert all(tree in e.population for tree in protected)
    e.step()
    for tree in set(protected): assert e.population.count(tree)>=protected.count(tree)
    assert len(e.population)==12
    if count==12: assert sorted(map(str,e.population))==sorted(map(str,protected))


def test_snapshot_comparison_is_immutable_and_does_not_consume_rng():
    cfg=Config(population=20,elite_count=3,population_samples=5,local_search=1)
    x=np.linspace(-1,1,20);e=Evolution(x,np.sin(x),cfg)
    before=e.rng.getstate();snapshot=e.snapshot()
    assert e.rng.getstate()==before
    assert isinstance(snapshot.elites,tuple) and isinstance(snapshot.population_sample,tuple)
    assert len(snapshot.elites)==3 and len(snapshot.population_sample)==5
    assert snapshot.population_size==20
    for candidate in snapshot.elites+snapshot.population_sample:
        assert candidate.tree in e.population
        assert candidate.mse==pytest.approx(np.mean((e.y-candidate.tree.evaluate(e.x))**2))
    original=snapshot.elites
    e.step()
    assert snapshot.elites==original

@pytest.mark.parametrize('options',[{'elite_count':0},{'elite_count':21},{'population_samples':-1},{'population_samples':21}])
def test_invalid_comparison_config(options):
    with pytest.raises(ValueError): Config(population=20,**options).validate()
