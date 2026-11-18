import {
  type Tree,
  type RNG,
  randomTree,
  evaluate,
  paths,
  crossover,
  mutate,
  repair,
  pick,
  clone,
  height,
} from "./tree";
export interface Point {
  x: number;
  y: number;
}
export interface Individual {
  tree: Tree;
  error: number;
}
export interface Config {
  maxHeight: number;
  mutationRate: number;
  elite: number;
}
export function score(tree: Tree, points: Point[]): number {
  try {
    let sum = 0;
    for (const p of points) {
      sum += (p.y - evaluate(tree, p.x)) ** 2;
      if (!Number.isFinite(sum)) return Infinity;
    }
    return points.length ? sum / points.length : Infinity;
  } catch {
    return Infinity;
  }
}
export function weights(errors: number[]): number[] {
  const w = errors.map((e) => (Number.isFinite(e) && e >= 0 ? 1 / (1 + e) : 0)),
    sum = w.reduce((a, b) => a + b, 0);
  return sum ? w.map((v) => v / sum) : w.map(() => 1 / w.length);
}
export const tournament = (pop: { error: number }[], a: number, b: number) =>
  pop[a].error <= pop[b].error ? a : b;
export function sus(
  prob: number[],
  count: number,
  rng: RNG = Math.random,
): number[] {
  const offset = rng() / count;
  return Array.from({ length: count }, (_, i) => {
    const p = offset + i / count;
    let acc = 0;
    for (let j = 0; j < prob.length; j++) {
      acc += prob[j];
      if (p < acc) return j;
    }
    return prob.length - 1;
  });
}
export function initialPopulation(
  n: number,
  data: Point[],
  config: Config,
  rng: RNG = Math.random,
): Individual[] {
  return Array.from({ length: n }, () => {
    const tree = randomTree(config.maxHeight, rng);
    return { tree, error: score(tree, data) };
  }).sort((a, b) => a.error - b.error);
}
export function nextGeneration(
  pop: Individual[],
  data: Point[],
  config: Config,
  rng: RNG = Math.random,
): Individual[] {
  if (pop.every((i) => !Number.isFinite(i.error)))
    return initialPopulation(pop.length, data, config, rng);
  const sorted = [...pop].sort((a, b) => a.error - b.error);
  const next = sorted
    .slice(0, Math.min(config.elite, pop.length))
    .map((i) => ({ tree: clone(i.tree), error: i.error }));
  const choose = () =>
    pop[
      tournament(
        pop,
        Math.floor(rng() * pop.length),
        Math.floor(rng() * pop.length),
      )
    ].tree;
  while (next.length < pop.length) {
    const a = choose(),
      b = choose();
    let children: [Tree, Tree] = [clone(a), clone(b)];
    const pa = paths(a).slice(1),
      pb = paths(b).slice(1);
    if (pa.length && pb.length)
      children = crossover(a, b, pick(pa, rng), pick(pb, rng));
    for (let tree of children) {
      if (rng() < config.mutationRate)
        tree = mutate(
          tree,
          pick(["terminal", "operator", "switch", "branch"] as const, rng),
          rng,
        );
      if (height(tree) > config.maxHeight)
        tree = repair(tree, config.maxHeight);
      next.push({ tree, error: score(tree, data) });
      if (next.length === pop.length) break;
    }
  }
  return next.sort((a, b) => a.error - b.error);
}
