import json
from io import StringIO
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from rich.console import Console
from tuning.spaces import SearchConfig, GridSpace, DirectSpace
from tuning.search import run_search
from tuning.persistence import export_results, load_results
from tuning.charts import export_plots
from tuning.cli import main


@pytest.fixture(scope='module')
def results():
    config=SearchConfig(population=4,generations=1,folds=2)
    return [run_search('grid',config,GridSpace({'n_estimators':[2,3],'learning_rate':[.1]})),
            run_search('genetic-direct',config,DirectSpace({'n_estimators':[1,4],'learning_rate':[.01,1]}))]


def test_json_csv_roundtrip_and_plots(tmp_path,results):
    files=export_results(results,tmp_path)
    loaded=load_results(tmp_path/'results.json')
    assert [r.to_dict() for r in loaded]==[r.to_dict() for r in results]
    summary=pd.read_csv(tmp_path/'summary.csv')
    assert len(summary)==2
    np.testing.assert_allclose(summary['best_accuracy'],[r.best_accuracy for r in results])
    evaluations=pd.read_csv(tmp_path/'evaluations.csv')
    assert len(evaluations)==sum(len(r.evaluations) for r in results)
    assert 'fold_scores' in evaluations
    history=pd.read_csv(tmp_path/'history.csv')
    assert len(history)==2
    plots=export_plots(results,tmp_path)
    assert len(plots)==2
    for file in plots:
        assert file.read_bytes().startswith(b'\x89PNG') and file.stat().st_size>10000


@pytest.mark.parametrize('payload',[
    {},{'schema_version':99,'results':[]}, {'schema_version':1,'results':[]},
    {'schema_version':1,'results':[{'method':'grid'}]},
])
def test_reject_invalid_results(tmp_path,payload):
    file=tmp_path/'bad.json';file.write_text(json.dumps(payload))
    with pytest.raises(ValueError):load_results(file)


def test_cli_noninteractive_and_invalid_arguments(tmp_path):
    grid=tmp_path/'grid.json';grid.write_text('{"n_estimators":[2,3],"learning_rate":[0.1]}')
    run=subprocess.run([sys.executable,'main.py','--method','compare','--grid',str(grid),
        '--population','4','--generations','1','--folds','2','--output',str(tmp_path/'out'),'--quiet'],
        capture_output=True,text=True,timeout=40)
    assert run.returncode==0,run.stderr+run.stdout
    assert 'Mejor resultado observado' in run.stdout
    assert len(load_results(tmp_path/'out'/'results.json'))==3
    invalid=subprocess.run([sys.executable,'main.py','--method','genetic-grid','--mutation','nan'],
        capture_output=True,text=True,timeout=15)
    assert invalid.returncode==2
    assert 'Traceback' not in invalid.stderr+invalid.stdout


def test_menu_dataset_stats_export_and_exit(tmp_path,results,monkeypatch):
    source=tmp_path/'source';export_results(results,source)
    answers=iter(['1','6','7',str(tmp_path/'export'),'8'])
    monkeypatch.setattr('tuning.cli.Prompt.ask',lambda *a,**k:next(answers))
    output=StringIO()
    assert main(['--input',str(source/'results.json')],console=Console(file=output,width=100))==0
    assert 'Wine' in output.getvalue()
    assert (tmp_path/'export'/'results.json').exists()


def test_cli_eof_and_missing_grid_are_clean(monkeypatch):
    def eof(*a,**k):raise EOFError
    monkeypatch.setattr('tuning.cli.Prompt.ask',eof)
    assert main([],console=Console(file=StringIO()))==0
    assert main(['--method','grid','--grid','/missing.json'],console=Console(file=StringIO()))==2


@pytest.mark.parametrize('corruption',['winner_params','winner_accuracy','fold_mean','split_hash','history','counter'])
def test_import_rejects_inconsistent_results(tmp_path,results,corruption):
    export_results(results,tmp_path)
    path=tmp_path/'results.json';payload=json.loads(path.read_text())
    row=payload['results'][0]
    if corruption=='winner_params':row['best_params']['n_estimators']=999999
    elif corruption=='winner_accuracy':row['best_accuracy']=1.
    elif corruption=='fold_mean':row['evaluations'][0]['fold_scores']=[0.,0.]
    elif corruption=='split_hash':row['cv']['split_hash']='incorrect'
    elif corruption=='counter':row['fitness_requests']=-1
    else:payload['results'][1]['history'][0]['best']=1.
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):load_results(path)


def test_plot_does_not_claim_shared_cv_for_different_folds(tmp_path,results,monkeypatch):
    from dataclasses import replace
    from matplotlib.figure import Figure
    titles=[]
    original=Figure.suptitle
    def capture(self,text,*args,**kwargs):
        titles.append(text)
        return original(self,text,*args,**kwargs)
    monkeypatch.setattr(Figure,'suptitle',capture)
    other=replace(results[1],cv={**results[1].cv,'split_hash':'different'})
    export_plots([results[0],other],tmp_path)
    assert any('PARTICIONES DIFERENTES' in title for title in titles)
    assert not any('MISMAS PARTICIONES' in title for title in titles)


def test_interrupted_execution_does_not_export(tmp_path,monkeypatch):
    def interrupt(*args,**kwargs):raise KeyboardInterrupt
    monkeypatch.setattr('tuning.cli.run_search',interrupt)
    assert main(['--method','genetic-grid','--output',str(tmp_path/'out')],
                console=Console(file=StringIO()))==130
    assert not (tmp_path/'out'/'results.json').exists()


def test_all_elite_history_survives_json_roundtrip(tmp_path):
    result=run_search('genetic-grid',SearchConfig(population=7,elite=7,generations=2,folds=2),
        GridSpace({'n_estimators':[2],'learning_rate':[.1]}))
    export_results([result],tmp_path)
    assert load_results(tmp_path/'results.json')[0].best_params==result.best_params


def test_singleton_population_mean_roundoff_does_not_break_reload(tmp_path):
    result=run_search('genetic-grid',SearchConfig(population=20,generations=0,folds=2),
        GridSpace({'n_estimators':[1],'learning_rate':[.1]}))
    export_results([result],tmp_path)
    assert load_results(tmp_path/'results.json')[0].best_accuracy==result.best_accuracy
