export interface Tree {
  value: string | number;
  children: Tree[];
}
export type Path = number[];
export type RNG = () => number;
export const arities: Record<string, number> = {
  "+": 2,
  "-": 2,
  "*": 2,
  "/": 2,
  "%": 2,
  "^": 2,
  sqrt: 1,
  log: 1,
  sin: 1,
  cos: 1,
  tan: 1,
};
export const terminal = (value: string | number): Tree => ({
  value,
  children: [],
});
export const node = (value: string, ...children: Tree[]): Tree => ({
  value,
  children,
});
export const clone = (t: Tree): Tree => ({
  value: t.value,
  children: t.children.map(clone),
});
export const height = (t: Tree): number =>
  t.children.length ? 1 + Math.max(...t.children.map(height)) : 0;
export const size = (t: Tree): number =>
  1 + t.children.reduce((n, c) => n + size(c), 0);
export const label = (t: Tree) => String(t.value);
export function validate(t: Tree): boolean {
  return t.children.length === 0
    ? t.value === "x" ||
        (typeof t.value === "number" && Number.isFinite(t.value))
    : typeof t.value === "string" &&
        arities[t.value] === t.children.length &&
        t.children.every(validate);
}
export function evaluate(t: Tree, x: number): number {
  if (!validate(t)) throw new Error("Árbol con aridad o terminal inválido.");
  if (!t.children.length) return t.value === "x" ? x : Number(t.value);
  const [a, b] = t.children.map((c) => evaluate(c, x));
  let v: number;
  switch (t.value) {
    case "+":
      v = a + b;
      break;
    case "-":
      v = a - b;
      break;
    case "*":
      v = a * b;
      break;
    case "/":
      if (b === 0) throw new Error("División por cero");
      v = a / b;
      break;
    case "%":
      if (b === 0) throw new Error("Módulo por cero");
      v = a % b;
      break;
    case "^":
      v = a ** b;
      break;
    case "sqrt":
      if (a < 0) throw new Error("Raíz negativa en reales");
      v = Math.sqrt(a);
      break;
    case "log":
      if (a <= 0) throw new Error("Logaritmo requiere argumento positivo");
      v = Math.log(a);
      break;
    case "sin":
      v = Math.sin(a);
      break;
    case "cos":
      v = Math.cos(a);
      break;
    case "tan":
      if (Math.abs(Math.cos(a)) < 1e-10)
        throw new Error("Tangente cerca de un polo");
      v = Math.tan(a);
      break;
    default:
      throw new Error("Operador desconocido");
  }
  if (!Number.isFinite(v)) throw new Error("Resultado no real o no finito");
  return v;
}
export function paths(t: Tree, p: Path = []): Path[] {
  return [p, ...t.children.flatMap((c, i) => paths(c, [...p, i]))];
}
export const at = (t: Tree, p: Path): Tree =>
  p.reduce((n, i) => {
    if (!n.children[i]) throw new Error("Camino inexistente");
    return n.children[i];
  }, t);
export function replace(t: Tree, p: Path, branch: Tree): Tree {
  if (!p.length) return clone(branch);
  at(t, p);
  return {
    ...t,
    children: t.children.map((c, i) =>
      i === p[0] ? replace(c, p.slice(1), branch) : clone(c),
    ),
  };
}
export function traversalPaths(
  t: Tree,
  order: "pre" | "in" | "post",
  p: Path = [],
): Path[] {
  const children = t.children.map((c, i) =>
    traversalPaths(c, order, [...p, i]),
  );
  if (order === "pre") return [p, ...children.flat()];
  if (order === "post") return [...children.flat(), p];
  return [...(children[0] ?? []), p, ...children.slice(1).flat()];
}
export const traverse = (t: Tree, order: "pre" | "in" | "post") =>
  traversalPaths(t, order).map((p) => label(at(t, p)));
export function expression(t: Tree): string {
  if (!t.children.length) return label(t);
  if (t.children.length === 1)
    return `${t.value}(${expression(t.children[0])})`;
  return `(${expression(t.children[0])} ${t.value} ${expression(t.children[1])})`;
}
export function seeded(seed: number): RNG {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const pick = <T>(items: T[], rng: RNG): T =>
  items[Math.min(items.length - 1, Math.floor(rng() * items.length))];
export function randomTree(
  maxHeight: number,
  rng: RNG = Math.random,
  full = false,
): Tree {
  maxHeight = Math.floor(maxHeight);
  if (maxHeight <= 0 || (!full && rng() < 0.3))
    return terminal(rng() < 0.5 ? "x" : Math.round((rng() * 10 - 5) * 10) / 10);
  const op = pick(Object.keys(arities), rng);
  return node(
    op,
    ...Array.from({ length: arities[op] }, () =>
      randomTree(maxHeight - 1, rng, full),
    ),
  );
}
export function crossover(a: Tree, b: Tree, pa: Path, pb: Path): [Tree, Tree] {
  if (!pa.length || !pb.length)
    throw new Error("El cruce por aristas requiere cortes debajo de la raíz.");
  return [replace(a, pa, at(b, pb)), replace(b, pb, at(a, pa))];
}
export type Mutation = "terminal" | "operator" | "switch" | "branch";
export function mutate(t: Tree, type: Mutation, rng: RNG = Math.random): Tree {
  const candidates = paths(t).filter((p) => {
    const n = at(t, p);
    return type === "terminal"
      ? !n.children.length
      : type === "operator"
        ? n.children.length > 0
        : type === "switch"
          ? n.children.length === 2
          : true;
  });
  if (!candidates.length)
    return type === "branch" ? randomTree(2, rng) : clone(t);
  const p = pick(candidates, rng),
    n = at(t, p);
  let branch: Tree;
  if (type === "terminal")
    branch = terminal(n.value === "x" ? Math.round(rng() * 50) / 10 : "x");
  else if (type === "operator")
    branch = node(
      pick(
        Object.keys(arities).filter(
          (op) => arities[op] === n.children.length && op !== n.value,
        ),
        rng,
      ),
      ...n.children.map(clone),
    );
  else if (type === "switch")
    branch = node(String(n.value), clone(n.children[1]), clone(n.children[0]));
  else {
    branch = randomTree(2, rng);
    if (expression(branch) === expression(n))
      branch = terminal(n.value === "x" ? 1 : "x");
  }
  return replace(t, p, branch);
}
export function repair(t: Tree, maxHeight: number): Tree {
  maxHeight = Math.floor(maxHeight);
  if (maxHeight <= 0) return t.children.length ? terminal("x") : clone(t);
  return { ...t, children: t.children.map((c) => repair(c, maxHeight - 1)) };
}
export const exampleTree = node(
  "sqrt",
  node(
    "-",
    node(
      "+",
      node("*", terminal(2), node("^", terminal("x"), terminal(2))),
      node("*", terminal(5), terminal("x")),
    ),
    terminal(3),
  ),
);
export const simpleTree = node(
  "*",
  node("+", terminal("x"), terminal(2)),
  node("-", terminal("x"), terminal(3)),
);
