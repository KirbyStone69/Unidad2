import { describe, it, expect } from "vitest";
import { metrics } from "../src/domain/metrics";
import {
  node,
  terminal,
  evaluate,
  height,
  size,
  traverse,
  validate,
  replace,
  crossover,
  mutate,
  repair,
  randomTree,
  expression,
  seeded,
} from "../src/domain/tree";
import {
  weights,
  tournament,
  sus,
  initialPopulation,
  nextGeneration,
} from "../src/domain/evolution";
import { parseCSV, referenceData } from "../src/domain/csv";
const tree = node("-", node("*", terminal("x"), terminal(2)), terminal(3));
describe("métricas reales", () => {
  it("calcula SSE=2, MSE=2/3, NMSE=1/7 y R²=0", () => {
    const m = metrics([1, 2, 3], [1, 1, 2]);
    expect(m.sse).toBe(2);
    expect(m.mse).toBeCloseTo(2 / 3);
    expect(m.nmse).toBeCloseTo(1 / 7);
    expect(m.r2).toBe(0);
  });
  it("no inventa denominadores cero", () => {
    expect(metrics([0, 0], [0, 0]).nmse).toBeNull();
    expect(metrics([2, 2], [2, 2]).r2).toBeNull();
    expect(() => metrics([], [])).toThrow();
    expect(() => metrics([1], [NaN])).toThrow();
  });
  it("permite R² negativo y MSE mayor que 1", () => {
    expect(metrics([1, 2], [10, 10]).r2).toBeLessThan(0);
    expect(metrics([1, 2], [10, 10]).mse).toBeGreaterThan(1);
  });
});
describe("árboles", () => {
  it("evalúa y mide con raíz en cero", () => {
    expect(evaluate(tree, 4)).toBe(5);
    expect(height(tree)).toBe(2);
    expect(size(tree)).toBe(5);
  });
  it("recorre los tres órdenes", () => {
    expect(traverse(tree, "pre")).toEqual(["-", "*", "x", "2", "3"]);
    expect(traverse(tree, "in")).toEqual(["x", "*", "2", "-", "3"]);
    expect(traverse(tree, "post")).toEqual(["x", "2", "*", "3", "-"]);
  });
  it("rechaza aridad y dominios no reales", () => {
    expect(validate({ value: "+", children: [terminal(1)] })).toBe(false);
    expect(() => evaluate(node("/", terminal(1), terminal(0)), 0)).toThrow();
    expect(() => evaluate(node("sqrt", terminal(-1)), 0)).toThrow();
    expect(() => evaluate(node("log", terminal(0)), 0)).toThrow();
  });
  it("cruza por aristas y no cambia padres", () => {
    const b = node("+", terminal(7), terminal(8));
    const before = JSON.stringify(tree);
    const [a2, b2] = crossover(tree, b, [0], [1]);
    expect(evaluate(a2, 1)).toBe(5);
    expect(evaluate(b2, 1)).toBe(9);
    expect(JSON.stringify(tree)).toBe(before);
    expect(() => crossover(tree, b, [], [0])).toThrow();
  });
  it("reemplaza ramas y repara por poda", () => {
    expect(height(repair(tree, 1))).toBeLessThanOrEqual(1);
    expect(evaluate(replace(tree, [0], terminal(9)), 0)).toBe(6);
  });
  it.each(["terminal", "operator", "switch", "branch"] as const)(
    "mutación %s conserva aridad",
    (type) => {
      const m = mutate(tree, type, seeded(42));
      expect(validate(m)).toBe(true);
      expect(JSON.stringify(m)).not.toBe(JSON.stringify(tree));
    },
  );
  it("genera árboles válidos de altura acotada y semilla reproducible", () => {
    for (let i = 0; i < 100; i++) {
      const t = randomTree(3, seeded(i + 1));
      expect(validate(t)).toBe(true);
      expect(height(t)).toBeLessThanOrEqual(3);
    }
    expect(expression(randomTree(3, seeded(4)))).toBe(
      expression(randomTree(3, seeded(4))),
    );
  });
});
describe("selección y evolución", () => {
  it("menor MSE implica mayor peso y gana torneo", () => {
    expect(weights([0, 3])).toEqual([0.8, 0.2]);
    expect(tournament([{ error: 0.2 }, { error: 0.8 }], 0, 1)).toBe(0);
    expect(weights([Infinity, Infinity])).toEqual([0.5, 0.5]);
  });
  it("SUS utiliza punteros equiespaciados", () => {
    expect(sus([0.75, 0.25], 4, () => 0)).toEqual([0, 0, 0, 1]);
  });
  it("evoluciona ocho individuos conservando la élite", () => {
    const data = [
      { x: 0, y: 0 },
      { x: 1, y: 1 },
      { x: 2, y: 4 },
    ];
    const rng = seeded(80);
    const config = { maxHeight: 3, mutationRate: 0.4, elite: 1 };
    const p = initialPopulation(8, data, config, rng);
    const q = nextGeneration(p, data, config, rng);
    expect(q).toHaveLength(8);
    expect(Math.min(...q.map((i) => i.error))).toBeLessThanOrEqual(
      Math.min(...p.map((i) => i.error)),
    );
    q.forEach((i) => expect(height(i.tree)).toBeLessThanOrEqual(3));
  });
});
describe("CSV", () => {
  it("acepta cabecera, comillas, CRLF y punto y coma", () => {
    expect(parseCSV('x;y\r\n"0";"1"\r\n1;2').points).toEqual([
      { x: 0, y: 1 },
      { x: 1, y: 2 },
    ]);
  });
  it("informa línea inválida sin esconderla", () => {
    const r = parseCSV("x,y\n0,1\n1,hola");
    expect(r.errors[0]).toContain("3");
    expect(r.points).toHaveLength(1);
  });
  it("genera 1000 puntos e incluye extremos", () => {
    const d = referenceData();
    expect(d).toHaveLength(1000);
    expect(d[0]).toEqual({ x: 0, y: 17.67 });
    expect(d[999].x).toBe(1);
  });
});
