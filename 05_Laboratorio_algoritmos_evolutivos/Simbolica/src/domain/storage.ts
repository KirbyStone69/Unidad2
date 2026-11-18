import { finishExam, type Attempt, type Exam } from "./assessment";
import type { Question } from "../content/questions";
export interface Progress {
  version: 1;
  attempts: Attempt[];
  read: number[];
  activeExam: Exam | null;
  lastUnit: number;
}
export const emptyProgress = (): Progress => ({
  version: 1,
  attempts: [],
  read: [],
  activeExam: null,
  lastUnit: 1,
});
const key = "simbolica-v1";
function isQuestion(q: unknown): q is Question {
  if (!q || typeof q !== "object") return false;
  const v = q as Question;
  return (
    v.revision === 1 &&
    typeof v.id === "string" &&
    Number.isInteger(v.unit) &&
    v.unit >= 1 &&
    v.unit <= 8 &&
    Number.isInteger(v.original) &&
    typeof v.prompt === "string" &&
    typeof v.answer === "string" &&
    typeof v.explanation === "string" &&
    typeof v.concept === "string" &&
    ["choice", "number", "order"].includes(v.type) &&
    (v.type === "number" ||
      (Array.isArray(v.options) &&
        v.options.every((s) => typeof s === "string")))
  );
}
function isAnswers(a: unknown): a is Record<string, string> {
  return (
    !!a &&
    typeof a === "object" &&
    !Array.isArray(a) &&
    Object.values(a).every((v) => typeof v === "string")
  );
}
function isAttempt(a: unknown): a is Attempt {
  if (!a || typeof a !== "object") return false;
  const v = a as Attempt;
  return (
    typeof v.id === "string" &&
    ["unit", "final", "recovery"].includes(v.mode) &&
    Number.isInteger(v.unit) &&
    Number.isFinite(v.score) &&
    v.score >= 0 &&
    v.score <= 100 &&
    Number.isFinite(v.date) &&
    Array.isArray(v.questions) &&
    v.questions.length > 0 &&
    v.questions.every(isQuestion) &&
    isAnswers(v.answers) &&
    Array.isArray(v.wrong) &&
    v.wrong.every((s) => typeof s === "string")
  );
}
function isExam(e: unknown): e is Exam {
  if (!e || typeof e !== "object") return false;
  const v = e as Exam;
  return (
    typeof v.id === "string" &&
    ["unit", "final", "recovery"].includes(v.mode) &&
    Number.isInteger(v.unit) &&
    Array.isArray(v.questions) &&
    v.questions.length > 0 &&
    v.questions.every(isQuestion) &&
    isAnswers(v.answers) &&
    (v.deadline === null || Number.isFinite(v.deadline)) &&
    Number.isFinite(v.startedAt)
  );
}
export function parseProgress(text: string): Progress {
  const p = JSON.parse(text) as Progress;
  if (
    p.version !== 1 ||
    !Array.isArray(p.attempts) ||
    !p.attempts.every(isAttempt) ||
    !Array.isArray(p.read) ||
    !p.read.every((u) => Number.isInteger(u) && u >= 1 && u <= 8) ||
    !(p.activeExam === null || isExam(p.activeExam)) ||
    !Number.isInteger(p.lastUnit) ||
    p.lastUnit < 1 ||
    p.lastUnit > 8
  )
    throw new Error("Archivo de progreso incompatible o incompleto.");
  for (const a of p.attempts) {
    const checked = finishExam({
      id: a.id,
      mode: a.mode,
      unit: a.unit,
      questions: a.questions,
      answers: a.answers,
      deadline: null,
      startedAt: a.date,
    });
    if (
      a.score !== checked.score ||
      JSON.stringify([...a.wrong].sort()) !==
        JSON.stringify([...checked.wrong].sort())
    )
      throw new Error(
        "Calificación incompatible con las respuestas guardadas.",
      );
  }
  return p;
}
export function loadProgress(): { progress: Progress; warning?: string } {
  try {
    const raw = localStorage.getItem(key);
    return { progress: raw ? parseProgress(raw) : emptyProgress() };
  } catch {
    return {
      progress: emptyProgress(),
      warning:
        "No se pudo recuperar el progreso local. Puedes seguir en memoria o importar una copia válida.",
    };
  }
}
export function saveProgress(p: Progress): string | undefined {
  try {
    localStorage.setItem(key, JSON.stringify(p));
    return undefined;
  } catch {
    return "No se pudo guardar en este navegador. Exporta tu progreso antes de cerrar.";
  }
}
