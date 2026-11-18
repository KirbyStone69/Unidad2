"""Fixed stratified folds and memoized accuracy evaluation on bundled Wine data."""
import hashlib
import inspect
import platform
from time import perf_counter
from importlib.metadata import version
import numpy as np
from sklearn.datasets import load_wine
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from .spaces import SearchConfig, validate_params


def versions():
    return {'python':platform.python_version(), **{name:version(name) for name in
            ('numpy','pandas','scikit-learn','deap','rich','matplotlib')}}


def compatibility_info():
    return {'sklearn':version('scikit-learn'),
            'signature':str(inspect.signature(AdaBoostClassifier)),
            'algorithm':'SAMME',
            'algorithm_argument_available':'algorithm' in AdaBoostClassifier().get_params(),
            'adaptation':'No se pasa algorithm ni se busca SAMME.R. Dos hiperparámetros numéricos; sklearn-deap sustituido por DEAP.'}


def dataset_info():
    data=load_wine()
    labels,counts=np.unique(data.target,return_counts=True)
    return {'name':'Wine','samples':len(data.target),'features':len(data.feature_names),
            'feature_names':list(data.feature_names),
            'classes':{str(data.target_names[i]):int(n) for i,n in zip(labels,counts)}}


class WineEvaluator:
    def __init__(self,folds=5,seed=42):
        SearchConfig(folds=folds,seed=seed).validate()
        data=load_wine()
        self.x,self.y=data.data,data.target
        self.seed=seed
        self.splits=list(StratifiedKFold(n_splits=folds,shuffle=True,random_state=seed).split(self.x,self.y))
        digest=hashlib.sha256()
        for train,test in self.splits:
            digest.update(np.asarray(train,dtype='<i8').tobytes())
            digest.update(b'|')
            digest.update(np.asarray(test,dtype='<i8').tobytes())
        self.cv_metadata={'strategy':'StratifiedKFold','folds':folds,'shuffle':True,
                          'seed':seed,'split_hash':digest.hexdigest(), 'scoring':'accuracy',
                          'selection_only':True,'independent_test':False}
        self.cache={}
        self.evaluations=[]
        self.requests=0

    def evaluate(self, params):
        validate_params(params)
        self.requests+=1
        key=(int(params['n_estimators']),float(params['learning_rate']))
        if key not in self.cache:
            start=perf_counter()
            scores=cross_val_score(AdaBoostClassifier(n_estimators=key[0],learning_rate=key[1],random_state=self.seed),
                self.x,self.y,cv=self.splits,scoring='accuracy',n_jobs=1,error_score='raise')
            row={'n_estimators':key[0],'learning_rate':key[1],
                 'accuracy':float(np.mean(scores)),'std':float(np.std(scores)),
                 'fold_scores':scores.tolist(),'seconds':perf_counter()-start}
            if not np.isfinite(scores).all():
                raise ValueError('La validación produjo accuracy no finita.')
            self.cache[key]=row
            self.evaluations.append(row)
        return self.cache[key].copy()
