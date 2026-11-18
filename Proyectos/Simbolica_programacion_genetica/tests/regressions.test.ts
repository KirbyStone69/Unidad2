import { it, expect } from "vitest";
import { buildExam, finishExam } from "../src/domain/assessment";
import { emptyProgress, parseProgress } from "../src/domain/storage";
import { parseCSV } from "../src/domain/csv";
import { metrics } from "../src/domain/metrics";
it("no repite originales aunque cambien IDs de variante", () => {
  const a = buildExam("unit", 1, 1);
  const b = buildExam(
    "unit",
    1,
    39,
    a.questions.map((q) => q.id),
  );
  expect(a.questions.map((q) => q.original).sort()).not.toEqual(
    b.questions.map((q) => q.original).sort(),
  );
});
it("rechaza progreso con nota incompatible con respuestas", () => {
  const p = emptyProgress();
  const attempt = finishExam(buildExam("unit", 1, 1));
  attempt.score = 100;
  p.attempts.push(attempt);
  expect(() => parseProgress(JSON.stringify(p))).toThrow();
});
it("rechaza comillas dentro de campos CSV no entrecomillados", () => {
  expect(parseCSV('x,y\n1"",2').errors.length).toBeGreaterThan(0);
});
it("mantiene media finita para observaciones grandes iguales", () => {
  const m = metrics([1e308, 1e308], [1e308, 1e308]);
  expect(m.mean).toBe(1e308);
  expect(m.r2).toBeNull();
  expect(m.mse).toBe(0);
});
it("rechaza desbordamiento de errores en lugar de devolver NaN", () => {
  expect(() => metrics([1e308, -1e308], [0, 0])).toThrow();
});
it("identifica SST cero para una constante que redondearía la suma", () => {
  expect(metrics(Array(6).fill(1), Array(6).fill(1)).r2).toBeNull();
});
