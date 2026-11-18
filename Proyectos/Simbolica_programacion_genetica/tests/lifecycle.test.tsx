import {
  render,
  screen,
  fireEvent,
  cleanup,
  act,
} from "@testing-library/react";
import { afterEach, it, expect, vi } from "vitest";
import App from "../src/App";
import { buildExam, weakQuestions, finishExam } from "../src/domain/assessment";
import {
  emptyProgress,
  saveProgress,
  loadProgress,
} from "../src/domain/storage";
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  localStorage.clear();
});
it("entrega examen vencido una sola vez aunque coincidan los temporizadores", () => {
  vi.useFakeTimers();
  const p = emptyProgress();
  p.activeExam = buildExam("final", 0, 99);
  p.activeExam.deadline = Date.now() - 1;
  saveProgress(p);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Reanudar evaluación" }));
  act(() => vi.advanceTimersByTime(2000));
  expect(
    screen.getByRole("heading", { name: "Corrección completa" }),
  ).toBeInTheDocument();
  expect(loadProgress().progress.attempts).toHaveLength(1);
  expect(loadProgress().progress.activeExam).toBeNull();
});
it("entrega al vencer aunque se haya salido a otra sección", () => {
  vi.useFakeTimers();
  const p = emptyProgress();
  p.activeExam = buildExam("final", 0, 98);
  p.activeExam.deadline = Date.now() + 500;
  saveProgress(p);
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Mi progreso" }));
  act(() => vi.advanceTimersByTime(1500));
  expect(
    screen.getByRole("heading", { name: "Corrección completa" }),
  ).toBeInTheDocument();
  expect(loadProgress().progress.attempts).toHaveLength(1);
});
it("si el almacenamiento está lleno devuelve un aviso y no lanza", () => {
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("QuotaExceededError");
  });
  expect(saveProgress(emptyProgress())).toMatch(/No se pudo guardar/);
});
it("un acierto posterior elimina pendiente sin borrar fallos históricos", () => {
  const e = buildExam("unit", 1, 94),
    q = e.questions[0];
  const before = finishExam(e);
  expect(weakQuestions([before]).some((w) => w.original === q.original)).toBe(
    true,
  );
  e.answers[q.id] = q.answer;
  const after = finishExam(e);
  expect(
    weakQuestions([before, after]).some((w) => w.original === q.original),
  ).toBe(false);
  expect(before.wrong).toContain(q.id);
});
