"""Versioned JSON and rectangular CSV exports; no pickle or executable input."""
import json
import math
from pathlib import Path
import tempfile
import pandas as pd
from .search import SearchResult, METHODS
from .spaces import SearchConfig, GridSpace, DirectSpace, validate_params
from .evaluation import WineEvaluator

SCHEMA_VERSION=1


def _atomic_text(path,text):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_results(results,directory):
    if not results:
        raise ValueError('No hay resultados para exportar.')
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    payload={'schema_version':SCHEMA_VERSION,'results':[result.to_dict() for result in results]}
    files=[directory/'results.json']
    _atomic_text(files[0],json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    summary=[];evaluations=[];history=[]
    for run_index,result in enumerate(results):
        summary.append({'run':run_index,'method':result.method,'best_accuracy':result.best_accuracy,
            **result.best_params,'seconds':result.elapsed_seconds,'baseline_accuracy':result.baseline['accuracy'],
            'fitness_requests':result.fitness_requests,'unique_evaluations':len(result.evaluations),
            'model_fits':len(result.evaluations)*result.config['folds'],
            'seed':result.config['seed'],'folds':result.config['folds'],'split_hash':result.cv['split_hash']})
        for row in result.evaluations:
            evaluations.append({'run':run_index,'method':result.method,**row,
                                'fold_scores':json.dumps(row['fold_scores'])})
        for row in result.history:
            history.append({'run':run_index,'method':result.method,**row,
                            'best_params':json.dumps(row['best_params'],sort_keys=True)})
    frames={'summary.csv':pd.DataFrame(summary),'evaluations.csv':pd.DataFrame(evaluations),
            'history.csv':pd.DataFrame(history,columns=['run','method','generation','population','evaluated',
                'unique_evaluations','best','mean','worst','std','best_params'])}
    for name,frame in frames.items():
        path=directory/name
        _atomic_text(path,frame.to_csv(index=False))
        files.append(path)
    return files


def _reject_constant(value):
    raise ValueError(f'Número JSON no finito: {value}')


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f'JSON inválido en {path}: {exc.msg}') from exc


def _accuracy(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
        raise ValueError('Accuracy fuera de [0,1] o no finita en resultados.')


def _positive_time(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('Tiempo inválido en resultados.')


def _validated_evaluation(row,folds):
    params={k:row[k] for k in ('n_estimators','learning_rate')}
    validate_params(params)
    _accuracy(row['accuracy'])
    scores=row['fold_scores']
    if not isinstance(scores,list) or len(scores)!=folds:
        raise ValueError('Número de folds inconsistente.')
    for score in scores:_accuracy(score)
    mean=sum(scores)/folds
    std=math.sqrt(sum((v-mean)**2 for v in scores)/folds)
    if not math.isclose(mean,row['accuracy'],abs_tol=1e-12) or not math.isclose(std,row['std'],abs_tol=1e-12):
        raise ValueError('Media o desviación inconsistentes con los scores por fold.')
    _positive_time(row['seconds'])
    return (params['n_estimators'],params['learning_rate'])


def _inside_space(params,space):
    validate_params(params)
    if isinstance(space,GridSpace):
        return all(params[k] in space.grid[k] for k in params)
    return all(space.bounds[k][0]<=v<=space.bounds[k][1] for k,v in params.items())


def load_results(path):
    payload=read_json(path)
    if not isinstance(payload,dict) or payload.get('schema_version')!=SCHEMA_VERSION or not isinstance(payload.get('results'),list) or not payload['results']:
        raise ValueError('Archivo de resultados vacío o versión no soportada.')
    results=[]
    try:
        for record in payload['results']:
            result=SearchResult(**record)
            if result.method not in METHODS:
                raise ValueError('Método desconocido en resultados.')
            config=SearchConfig(**result.config).validate()
            space=DirectSpace(result.space['bounds']) if result.method=='genetic-direct' else GridSpace(result.space['grid'])
            if result.space!=space.to_dict():
                raise ValueError('Metadatos de espacio inconsistentes.')
            if not _inside_space(result.best_params,space):
                raise ValueError('Ganador fuera del espacio de búsqueda.')
            _accuracy(result.best_accuracy)
            _validated_evaluation(result.baseline,config.folds)
            _positive_time(result.elapsed_seconds)
            if not isinstance(result.fitness_requests,int) or not result.evaluations or result.fitness_requests<len(result.evaluations):
                raise ValueError('Contadores o evaluaciones inválidos.')
            expected_cv=WineEvaluator(config.folds,config.seed).cv_metadata
            if result.cv!=expected_cv:
                raise ValueError('Configuración o hash de validación inconsistente.')
            observed={}
            for row in result.evaluations:
                key=_validated_evaluation(row,config.folds)
                if key in observed or not _inside_space(dict(zip(('n_estimators','learning_rate'),key)),space):
                    raise ValueError('Evaluación duplicada o fuera del espacio.')
                observed[key]=row['accuracy']
            winner=(result.best_params['n_estimators'],result.best_params['learning_rate'])
            if winner not in observed or not math.isclose(observed[winner],result.best_accuracy,abs_tol=1e-12) or not math.isclose(max(observed.values()),result.best_accuracy,abs_tol=1e-12):
                raise ValueError('El ganador no coincide con la mejor evaluación observada.')
            if result.grid_guarantee is not (result.method=='grid'):
                raise ValueError('Garantía de cuadrícula inconsistente.')
            if result.method=='grid':
                if result.history or len(observed)!=space.size or result.fitness_requests!=space.size:
                    raise ValueError('Búsqueda exhaustiva incompleta.')
            else:
                if len(result.history)!=config.generations+1:
                    raise ValueError('Historial generacional incompleto.')
                previous=-1.
                for generation,row in enumerate(result.history):
                    for key in ('best','mean','worst'):_accuracy(row[key])
                    if row['generation']!=generation or row['population']!=config.population:
                        raise ValueError('Generación o tamaño de población inconsistente.')
                    if not previous<=row['best'] or not row['worst']-1e-12<=row['mean']<=row['best']+1e-12:
                        raise ValueError('Estadísticas o elitismo inconsistentes.')
                    params=row['best_params']
                    validate_params(params)
                    key=(params['n_estimators'],params['learning_rate'])
                    if key not in observed or not math.isclose(observed[key],row['best'],abs_tol=1e-12):
                        raise ValueError('Ganador generacional inconsistente.')
                    previous=row['best']
                if not math.isclose(previous,result.best_accuracy,abs_tol=1e-12):
                    raise ValueError('El ganador final no coincide con el historial.')
                if sum(row['evaluated'] for row in result.history)!=result.fitness_requests or sum(row['unique_evaluations'] for row in result.history)!=len(observed):
                    raise ValueError('Contadores generacionales inconsistentes.')
            results.append(result)
    except (TypeError,KeyError,AttributeError,OverflowError) as exc:
        raise ValueError('Estructura de resultados inválida o incompleta.') from exc
    return results
