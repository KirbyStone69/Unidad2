import numpy as np
from laboratorio.engine import Node, Config, Evolution, metrics, repair

def test_metrics():
 assert metrics(np.array([1.,2.]), np.array([1.,2.])) == (0.,0.,1.)

def test_protected_division():
 n = Node('/', (Node('x'), Node('0')))
 assert np.isfinite(n.evaluate(np.arange(5.))).all()

def test_repair():
 n = Node('+', (Node('+', (Node('x'),Node('x'))),Node('x')))
 assert repair(n, 1).height <= 1
 assert n.height == 2

def test_evolution():
 x=np.linspace(-2,2,40); y=x*x+x+1
 a=Evolution(x,y,Config(population=100,generations=12,seed=7))
 scores=[a.snapshot().mse]
 for _ in range(12): scores.append(a.step().mse)
 assert all(b<=a for a,b in zip(scores,scores[1:]))
 assert scores[-1]<scores[0]
 assert all(n.height<=a.config.max_depth for n in a.population)
 b=Evolution(x,y,Config(population=100,generations=12,seed=7))
 assert b.snapshot().mse==scores[0]
