"""Immutable, arity-checked expression trees and a protected numeric grammar."""
from dataclasses import dataclass
from functools import cached_property
import math
import numpy as np

LIMIT = 1e6
EPS = 1e-12
ARITY = {'+':2, '-':2, '*':2, '/':2, 'sin':1, 'cos':1, 'square':1,
         'cube':1, 'exp':1, 'log':1, 'sqrt':1, 'tanh':1, 'abs':1, 'atan':1, 'sigmoid':1, 'neg':1}
BINARY = ('+', '-', '*', '/')
EXTRA_OPERATORS = ('atan', 'sigmoid', 'neg')
DEFAULT_OPERATORS = tuple(op for op in ARITY if op not in EXTRA_OPERATORS)
NAMED = {'pi': math.pi, 'e': math.e}


def finite(values):
    return np.clip(np.nan_to_num(values, nan=0., posinf=LIMIT, neginf=-LIMIT), -LIMIT, LIMIT)


def apply_operator(op, args):
    a = args[0]
    with np.errstate(all='ignore'):
        if op == '+': result = a + args[1]
        elif op == '-': result = a - args[1]
        elif op == '*': result = a * args[1]
        elif op == '/':
            result = np.divide(a, args[1], out=np.ones_like(a), where=np.abs(args[1]) > 1e-8)
        elif op == 'sin': result = np.sin(a)
        elif op == 'cos': result = np.cos(a)
        elif op == 'square': result = a * a
        elif op == 'cube': result = a * a * a
        elif op == 'exp': result = np.exp(np.clip(a, -20., np.log(LIMIT)))
        elif op == 'log': result = np.log(np.maximum(np.abs(a), EPS))
        elif op == 'sqrt': result = np.sqrt(np.abs(a))
        elif op == 'tanh': result = np.tanh(a)
        elif op == 'abs': result = np.abs(a)
        elif op == 'atan': result = np.arctan(a)
        elif op == 'sigmoid': result = np.exp(-np.logaddexp(0.,-a))
        elif op == 'neg': result = -a
        else: raise ValueError(f'Operador desconocido: {op}')
    return finite(result)


@dataclass(frozen=True)
class Node:
    value: str
    children: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, 'children', tuple(self.children))
        if self.value in ARITY:
            if len(self.children) != ARITY[self.value]:
                raise ValueError(f'{self.value} requiere {ARITY[self.value]} argumento(s).')
        elif self.children:
            raise ValueError(f'Operador desconocido: {self.value}')
        elif self.value != 'x' and self.value not in NAMED:
            try:
                if not math.isfinite(float(self.value)): raise ValueError
            except (ValueError, TypeError):
                raise ValueError(f'Terminal inválido: {self.value}') from None
        if not all(isinstance(c, Node) for c in self.children):
            raise ValueError('Los hijos deben ser nodos de expresión.')

    @cached_property
    def height(self):
        return 0 if not self.children else 1 + max(c.height for c in self.children)

    @cached_property
    def size(self):
        return 1 + sum(c.size for c in self.children)

    @property
    def is_constant(self):
        return not self.children and self.value != 'x'

    def evaluate(self, x):
        x = np.asarray(x, dtype=np.float64)
        if not self.children:
            if self.value == 'x': return finite(x)
            value = NAMED[self.value] if self.value in NAMED else float(self.value)
            return np.full_like(x, np.clip(value, -LIMIT, LIMIT), dtype=np.float64)
        return apply_operator(self.value, [c.evaluate(x) for c in self.children])

    @property
    def label(self):
        if self.is_constant and self.value not in NAMED: return f'{float(self.value):.4g}'
        return {'square':'x²', 'cube':'x³'}.get(self.value, self.value)

    def __str__(self):
        if not self.children:
            return self.value if self.value in ('x', *NAMED) else f'{float(self.value):.10g}'
        if len(self.children) == 1: return f'{self.value}({self.children[0]})'
        return f'({self.children[0]} {self.value} {self.children[1]})'

    def to_python(self):
        """NumPy expression with the same protected semantics as evaluate()."""
        if not self.children:
            if self.value == 'x':
                return 'np.clip(np.nan_to_num(np.asarray(x, dtype=np.float64), nan=0.0, posinf=1e6, neginf=-1e6), -1e6, 1e6)'
            if self.value in NAMED: return 'np.'+self.value
            return repr(float(np.clip(float(self.value), -LIMIT, LIMIT)))
        args=[c.to_python() for c in self.children]; a=args[0]
        if self.value in ('+','-','*'): raw=f'({a} {self.value} {args[1]})'
        elif self.value == '/':
            raw=f'np.divide({a}, {args[1]}, out=np.ones_like(x, dtype=np.float64), where=(np.abs({args[1]}) > 1e-8))'
        elif self.value == 'square': raw=f'({a} ** 2)'
        elif self.value == 'cube': raw=f'({a} ** 3)'
        elif self.value == 'exp': raw=f'np.exp(np.clip({a}, -20.0, np.log(1e6)))'
        elif self.value == 'log': raw=f'np.log(np.maximum(np.abs({a}), 1e-12))'
        elif self.value == 'sqrt': raw=f'np.sqrt(np.abs({a}))'
        elif self.value == 'atan': raw=f'np.arctan({a})'
        elif self.value == 'sigmoid': raw=f'np.exp(-np.logaddexp(0.0, -({a})))'
        elif self.value == 'neg': raw=f'(-({a}))'
        else: raw=f'np.{self.value}({a})'
        return f'np.clip({raw}, -1e6, 1e6)'

    def paths(self, prefix=()):
        yield prefix
        for i,c in enumerate(self.children): yield from c.paths(prefix+(i,))

    def at(self, path):
        return self if not path else self.children[path[0]].at(path[1:])

    def replace(self, path, other):
        if not path: return other
        children = list(self.children)
        children[path[0]] = children[path[0]].replace(path[1:], other)
        return Node(self.value, tuple(children))


def constant(value):
    value = float(value)
    if not math.isfinite(value): raise ValueError('Constante no finita.')
    return Node(str(int(value)) if value.is_integer() else repr(value))


def repair(node, depth, max_nodes=None):
    if depth <= 0 and node.children: return Node('x')
    result = Node(node.value, tuple(repair(c, depth-1) for c in node.children))
    if max_nodes is not None:
        # Prune the deepest branch first, preserving useful structure near the root.
        while result.size > max_nodes:
            branches = [p for p in result.paths() if result.at(p).children]
            path = max(branches, key=lambda p:(len(p), result.at(p).size))
            result = result.replace(path, Node('x'))
    return result


def simplify(node):
    if not node.children: return node
    children = tuple(simplify(c) for c in node.children)
    result = Node(node.value, children)
    if all(c.is_constant for c in children): return constant(result.evaluate(np.zeros(1))[0])
    if len(children) == 2:
        a,b = children
        zero = lambda n:n.is_constant and float(n.evaluate(np.zeros(1))[0]) == 0
        one = lambda n:n.is_constant and float(n.evaluate(np.zeros(1))[0]) == 1
        if node.value == '+':
            if zero(b): return a
            if zero(a): return b
        if node.value == '-' and zero(b): return a
        if node.value == '*':
            if zero(a) or zero(b): return constant(0)
            if one(a): return b
            if one(b): return a
        if node.value == '/' and one(b): return a
    return result


def random_tree(rng, depth, full=False, operators=DEFAULT_OPERATORS):
    if depth <= 0 or not operators or (not full and rng.random() < .3):
        if rng.random() < .60: return Node('x')
        if rng.random() < .1: return Node(rng.choice(('pi','e')))
        if rng.random() < .5: return constant(rng.choice([-2,-1,0,1,2,3]))
        return constant(rng.uniform(-10,10))
    # Half of choices are arithmetic to keep mixed unary/binary trees expressive.
    binary = tuple(op for op in operators if ARITY[op] == 2)
    pool = binary if binary and rng.random() < .5 else operators
    op = rng.choice(pool)
    return Node(op, tuple(random_tree(rng, depth-1, full, operators) for _ in range(ARITY[op])))
