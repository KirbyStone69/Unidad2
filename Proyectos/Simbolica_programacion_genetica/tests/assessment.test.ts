import { describe, it, expect, beforeEach } from "vitest";
import { bank, makeQuestion } from "../src/content/questions";
import { lessons } from "../src/content/lessons";
import {
  grade,
  buildExam,
  finishExam,
  remainingSeconds,
} from "../src/domain/assessment";
import {
  loadProgress,
  saveProgress,
  emptyProgress,
} from "../src/domain/storage";
beforeEach(() => localStorage.clear());
describe("contenido y corrección", () => {
  it("tiene ocho unidades y diez originales por unidad", () => {
    expect(lessons).toHaveLength(8);
    for (let u = 1; u <= 8; u++) {
      expect(bank.filter((q) => q.unit === u).length).toBeGreaterThanOrEqual(
        10,
      );
    }
    expect(new Set(bank.map((q) => q.id)).size).toBe(bank.length);
  });
  it("cada solución se corrige como correcta y no acepta vacío", () => {
    for (const q of bank) {
      expect(grade(q, q.answer), q.id).toBe(true);
      expect(grade(q, ""), q.id).toBe(false);
      expect(q.explanation.length).toBeGreaterThan(30);
    }
  });
  it("usa tolerancia numérica y orden exacto", () => {
    const q = makeQuestion(5, 2, 2);
    expect(q.type).toBe("number");
    expect(grade(q, String(Number(q.answer) + 0.00001))).toBe(true);
    expect(grade(q, "Infinity")).toBe(false);
    const order = bank.find((q) => q.type === "order")!;
    expect(grade(order, order.answer)).toBe(true);
    expect(grade(order, "1,1,1")).toBe(false);
  });
  it("simulacro ponderado con 30 preguntas y variantes distintas", () => {
    const a = buildExam("final", 0, 1);
    const b = buildExam("final", 0, 2);
    expect(a.questions).toHaveLength(30);
    expect(new Set(a.questions.map((q) => q.id)).size).toBe(30);
    expect(a.questions.map((q) => q.id)).not.toEqual(
      b.questions.map((q) => q.id),
    );
    expect(a.questions.filter((q) => q.unit === 5)).toHaveLength(5);
  });
  it("no repite conjunto inmediato de evaluación", () => {
    const a = buildExam("unit", 1, 1);
    const b = buildExam(
      "unit",
      1,
      1,
      a.questions.map((q) => q.id),
    );
    expect(a.questions.map((q) => q.id).sort()).not.toEqual(
      b.questions.map((q) => q.id).sort(),
    );
  });
  it("califica resultados reales y reloj por fecha absoluta", () => {
    const e = buildExam("unit", 1, 8);
    e.answers = {};
    expect(finishExam(e).score).toBe(0);
    e.questions.forEach((q) => (e.answers[q.id] = q.answer));
    expect(finishExam(e).score).toBe(100);
    expect(remainingSeconds(10000, 5500)).toBe(5);
    expect(remainingSeconds(10000, 12000)).toBe(0);
  });
});
describe("persistencia", () => {
  it("inicia sin unidades completadas y persiste intentos", () => {
    const p = emptyProgress();
    expect(p.attempts).toHaveLength(0);
    const e = buildExam("unit", 1, 2);
    e.answers = {};
    p.attempts.push(finishExam(e));
    saveProgress(p);
    expect(loadProgress().progress.attempts[0].score).toBe(0);
  });
  it("recupera JSON corrupto y rechaza estructuras incompletas", () => {
    localStorage.setItem("simbolica-v1", "{");
    expect(loadProgress().warning).toBeTruthy();
    localStorage.setItem(
      "simbolica-v1",
      JSON.stringify({ version: 1, attempts: [{}] }),
    );
    expect(loadProgress().progress.attempts).toHaveLength(0);
  });
  it("preserva sesión activa, respuestas y deadline al recargar", () => {
    const p = emptyProgress();
    p.activeExam = buildExam("final", 0, 12);
    p.activeExam.deadline = 12345;
    p.activeExam.answers[p.activeExam.questions[0].id] = "2";
    saveProgress(p);
    expect(loadProgress().progress.activeExam).toEqual(p.activeExam);
  });
});
it("acepta espacios alrededor de los pasos ordenados", () => {
  const q = bank.find((q) => q.type === "order")!;
  expect(grade(q, q.answer.split(",").join(", "))).toBe(true);
});
it("recuperación evita repetir la misma variante numérica", () => {
  const old = makeQuestion(5, 2, 1);
  const e = buildExam("recovery", 0, 8, [old.id], [{ unit: 5, original: 2 }]);
  expect(e.questions[0].prompt).not.toBe(old.prompt);
});
it("el orden presentado cambia sin alterar la solución lógica", () => {
  const a = makeQuestion(1, 8, 1),
    b = makeQuestion(1, 8, 2);
  expect(a.options).not.toEqual(b.options);
  expect(grade(b, b.answer)).toBe(true);
});
