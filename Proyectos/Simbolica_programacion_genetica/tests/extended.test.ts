import { it, expect } from "vitest";
import { bank, makeQuestion } from "../src/content/questions";
import { grade, buildExam, finishExam } from "../src/domain/assessment";
import { metrics } from "../src/domain/metrics";
import {
  arities,
  node,
  terminal,
  evaluate,
  exampleTree,
  size,
  height,
  paths,
  crossover,
  randomTree,
  seeded,
  validate,
  mutate,
  repair,
} from "../src/domain/tree";
import { parseCSV } from "../src/domain/csv";
it("verifica soluciones avanzadas contra cálculos independientes", () => {
  expect(size(exampleTree)).toBe(12);
  expect(height(exampleTree)).toBe(5);
  const m = metrics([2, 4, 6], [1, 5, 7]);
  expect(Number(makeQuestion(5, 10).answer)).toBeCloseTo(m.r2!);
  expect(Number(makeQuestion(5, 11).answer)).toBeCloseTo(m.nmse!);
  expect(Number(makeQuestion(6, 11).answer)).toBeCloseTo(1 - (3 / 4) ** 2);
  for (let v = 0; v < 20; v++) {
    const k = (v % 5) + 2;
    expect(
      grade(makeQuestion(3, 10, v), String(k === 3 ? 4.5 : 9 / (k - 3))),
    ).toBe(true);
  }
});
it("todos los distractores son distintos y todas las variantes numéricas finitas", () => {
  for (const q of bank) {
    if (q.type === "choice") {
      expect(new Set(q.options).size, q.id).toBe(q.options!.length);
      expect(q.options![Number(q.answer)], q.id).toBeTruthy();
    }
    for (let v = 0; v < 10; v++) {
      const candidate = makeQuestion(q.unit, q.original, v);
      if (candidate.type === "number")
        expect(Number.isFinite(Number(candidate.answer)), candidate.id).toBe(
          true,
        );
    }
  }
});
it("simulacro utiliza exclusivamente problemas avanzados", () => {
  expect(
    buildExam("final", 0, 42).questions.every((q) => q.original >= 10),
  ).toBe(true);
});
it("cada primitiva respeta aridad y semántica ordinaria", () => {
  const expected: Record<string, number> = {
    "+": 6,
    "-": 2,
    "*": 8,
    "/": 2,
    "%": 0,
    "^": 16,
    sqrt: 2,
    log: Math.log(4),
    sin: Math.sin(4),
    cos: Math.cos(4),
    tan: Math.tan(4),
  };
  for (const [op, arity] of Object.entries(arities)) {
    const t = node(
      op,
      ...(arity === 2 ? [terminal(4), terminal(2)] : [terminal(4)]),
    );
    expect(validate(t)).toBe(true);
    expect(evaluate(t, 0)).toBeCloseTo(expected[op]);
  }
  expect(() => evaluate(node("tan", terminal(Math.PI / 2)), 0)).toThrow();
  expect(() => evaluate(node("^", terminal(-1), terminal(0.5)), 0)).toThrow();
});
it("cruces, mutaciones y poda conservan árboles y límites en múltiples semillas", () => {
  for (let i = 1; i < 80; i++) {
    const rng = seeded(i),
      a = randomTree(4, rng, true),
      b = randomTree(3, rng, true),
      sa = JSON.stringify(a),
      sb = JSON.stringify(b);
    const [child] = crossover(a, b, paths(a)[1], paths(b)[1]);
    for (const type of ["terminal", "operator", "switch", "branch"] as const) {
      expect(validate(repair(mutate(child, type, rng), 3))).toBe(true);
      expect(height(repair(mutate(child, type, rng), 3))).toBeLessThanOrEqual(
        3,
      );
    }
    expect(JSON.stringify(a)).toBe(sa);
    expect(JSON.stringify(b)).toBe(sb);
  }
});
it("CSV no acepta comillas mal colocadas, columnas extra ni cabecera malformada", () => {
  for (const source of [
    "x,y\n1,2,3",
    'x,y\n"1"oops,2',
    'x,y\n"1,2',
    'x"",y\n1,2',
  ])
    expect(parseCSV(source).errors.length, source).toBeGreaterThan(0);
});
it("entregar conserva respuestas sin recalificar histórico al cambiar la sesión", () => {
  const e = buildExam("unit", 5, 4);
  const q = e.questions[0];
  e.answers[q.id] = q.answer;
  const attempt = finishExam(e);
  e.answers[q.id] = "";
  expect(attempt.answers[q.id]).toBe(q.answer);
});
