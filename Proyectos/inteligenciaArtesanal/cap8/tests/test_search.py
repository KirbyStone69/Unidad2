import random
import numpy as np
import pytest
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import cross_val_score
from tuning.spaces import GridSpace, DirectSpace, SearchConfig
from tuning.evaluation import WineEvaluator, dataset_info
from tuning.search import run_search, compare_methods

SMALL_GRID={'n_estimators':[2,4], 'learning_rate':[.2,1.]}


def test_fitness_is_mean_of_real_cross_validation_and_cached():
    evaluator=WineEvaluator(folds=3,seed=19)
    params={'n_estimators':4,'learning_rate':.2}
    actual=evaluator.evaluate(params)
    expected=cross_val_score(AdaBoostClassifier(**params,random_state=19),
        evaluator.x,evaluator.y,cv=evaluator.splits,scoring='accuracy',error_score='raise',n_jobs=1)
    np.testing.assert_array_equal(actual['fold_scores'],expected)
    assert actual['accuracy']==float(expected.mean())
    assert evaluator.evaluate(params)['accuracy']==actual['accuracy']
    assert evaluator.requests==2 and len(evaluator.evaluations)==1
    assert evaluator.cv_metadata['split_hash']==WineEvaluator(3,19).cv_metadata['split_hash']
    assert dataset_info()['samples']==178 and dataset_info()['features']==13


def test_exhaustive_visits_every_configuration_and_reports_best():
    config=SearchConfig(folds=3,population=6,generations=2)
    events=[]
    result=run_search('grid',config,GridSpace(SMALL_GRID),callback=lambda kind,data:events.append((kind,data)))
    assert len(result.evaluations)==4 and result.fitness_requests==4
    assert result.best_accuracy==max(row['accuracy'] for row in result.evaluations)
    assert result.best_params in list(GridSpace(SMALL_GRID).combinations())
    assert len([e for e in events if e[0]=='evaluation'])==4
    assert result.grid_guarantee is True
    assert result.elapsed_seconds>0


@pytest.mark.parametrize('method,space',[
    ('genetic-grid',GridSpace(SMALL_GRID)),
    ('genetic-direct',DirectSpace({'n_estimators':[1,5],'learning_rate':[.01,1]})),
])
def test_elitism_reproducibility_and_local_rng(method,space):
    config=SearchConfig(folds=2,population=8,generations=4,mutation=1.,crossover=1.,seed=7,elite=2)
    state=random.getstate()
    first=run_search(method,config,space)
    assert random.getstate()==state
    second=run_search(method,config,space)
    assert first.best_params==second.best_params
    assert first.best_accuracy==second.best_accuracy
    assert [r['best'] for r in first.history]==[r['best'] for r in second.history]
    assert len(first.history)==5
    assert np.all(np.diff([r['best'] for r in first.history])>=0)
    assert first.history[-1]['best']==first.best_accuracy
    assert all(row['population']==8 for row in first.history)
    assert first.grid_guarantee is False


def test_all_elite_preserves_every_individual_without_new_evaluation():
    result=run_search('genetic-grid',SearchConfig(population=4,elite=4,generations=3,folds=2),GridSpace(SMALL_GRID))
    assert all(row['evaluated']==0 for row in result.history[1:])
    assert len(set(row['mean'] for row in result.history))==1


def test_comparison_shares_folds_but_not_caches():
    results=compare_methods(SearchConfig(population=4,generations=1,folds=2),
        GridSpace(SMALL_GRID),DirectSpace({'n_estimators':[1,5],'learning_rate':[.01,1]}))
    assert len(results)==3
    assert len({r.cv['split_hash'] for r in results})==1
    assert all(r.evaluations and r.baseline['accuracy']>0 for r in results)
    assert results[1].history[0]['unique_evaluations']>=1


def test_bad_method_and_space_fail_before_training():
    with pytest.raises(ValueError):run_search('unknown',SearchConfig())
    with pytest.raises(ValueError):run_search('grid',SearchConfig(),DirectSpace())


def test_exhaustive_matches_independent_grid_search_cv():
    from sklearn.model_selection import GridSearchCV
    evaluator=WineEvaluator(3,42)
    reference=GridSearchCV(AdaBoostClassifier(random_state=42),SMALL_GRID,
        cv=evaluator.splits,scoring='accuracy',error_score='raise',n_jobs=1)
    reference.fit(evaluator.x,evaluator.y)
    result=run_search('grid',SearchConfig(folds=3),GridSpace(SMALL_GRID))
    assert result.best_params==reference.best_params_
    assert result.best_accuracy==reference.best_score_


def test_zero_generations_and_singleton_grid():
    result=run_search('genetic-grid',SearchConfig(population=4,generations=0,folds=2),
        GridSpace({'n_estimators':[2],'learning_rate':[.1]}))
    assert len(result.history)==1
    assert result.fitness_requests==4 and len(result.evaluations)==1
    assert result.history[0]['best']==result.history[0]['worst']
