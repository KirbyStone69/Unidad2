"""Run: .venv/bin/python -m benchmarks.search [--output docs/benchmark.json]."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import time
import numpy as np
from laboratorio.engine import Config,Evolution,metrics


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='docs/benchmark.json')
    args=parser.parse_args()
    gr=np.loadtxt(Path(__file__).resolve().parents[1]/'gr.csv',delimiter=',',skiprows=1)
    cases=[('CSV usuario',gr[:,0],gr[:,1],lambda x:6.67+11*np.cos(7.23*x**3)),
           ('Coseno cúbico diferente',np.linspace(-.8,1.,60),None,lambda x:2.8+4.6*np.cos(4.3*x**3)),
           ('Seno con fase',np.linspace(-1,1,60),None,lambda x:-1.7+3.2*np.sin(5.1*x+.9)),
           ('Exponencial',np.linspace(-1,1,60),None,lambda x:2.1+1.3*np.exp(1.7*x)),
           ('Racional',np.linspace(-1,1,60),None,lambda x:.4+5.2/(1+2.6*x*x)),
           ('Polinomio',np.linspace(-2,2,60),None,lambda x:1.2-2.7*x+.8*x*x)]
    rows=[]; config=Config(population=100,generations=100)
    for name,x,y,function in cases:
        if y is None: y=function(x)
        for seed in (7,42,91):
            from dataclasses import replace
            start=time.perf_counter(); engine=Evolution(x,y,replace(config,seed=seed))
            while engine.generation<config.generations and not engine.converged: engine.step()
            elapsed=time.perf_counter()-start; snapshot=engine.snapshot()
            unseen=np.linspace(float(min(x))+.0003,float(max(x))-.0003,201)
            mse,nmse,r2=metrics(function(unseen),snapshot.tree.evaluate(unseen))
            row={'case':name,'seed':seed,'seconds':round(elapsed,4),'generation':snapshot.generation,
                 'train_nmse':snapshot.nmse,'validation_nmse':snapshot.validation_nmse,
                 'dense_nmse':nmse,'nodes':snapshot.nodes,'height':snapshot.tree.height,
                 'evaluations':snapshot.evaluations,'expression':str(snapshot.tree)}
            rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
    report={'python':platform.python_version(),'platform':platform.platform(),'config':asdict(config),'results':rows}
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')

if __name__=='__main__': main()
