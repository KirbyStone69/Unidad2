import { type Question, bank, makeQuestion } from "../content/questions";
import { seeded } from "./tree";
export type ExamMode = "unit" | "final" | "recovery";
export interface Exam {
  id: string;
  mode: ExamMode;
  unit: number;
  questions: Question[];
  answers: Record<string, string>;
  deadline: number | null;
  startedAt: number;
}
export interface Attempt {
  id: string;
  mode: ExamMode;
  unit: number;
  score: number;
  date: number;
  questions: Question[];
  answers: Record<string, string>;
  wrong: string[];
}
export function grade(q: Question, response: string): boolean {
  if (!response?.trim()) return false;
  if (q.type === "number") {
    const value = Number(response.replace(",", "."));
    return (
      Number.isFinite(value) &&
      Math.abs(value - Number(q.answer)) <= (q.tolerance ?? 0.001)
    );
  }
  if (q.type === "order")
    return (
      response
        .split(",")
        .map((v) => v.trim())
        .join(",") === q.answer
    );
  return response.trim() === q.answer;
}
function shuffle<T>(arr: T[], rng: () => number): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
export function buildExam(
  mode: ExamMode,
  unit = 0,
  seed = Date.now(),
  previous: string[] = [],
  weak: { unit: number; original: number }[] = [],
): Exam {
  const rng = seeded(seed);
  let selected: Question[] = [];
  const variant = Math.abs(seed) % 100000;
  if (mode === "final") {
    const counts = [2, 3, 5, 2, 5, 4, 5, 4];
    for (let u = 1; u <= 8; u++) {
      selected.push(
        ...shuffle(
          bank.filter((q) => q.unit === u && q.original >= 10),
          rng,
        )
          .slice(0, counts[u - 1])
          .map((q) => makeQuestion(u, q.original, variant)),
      );
    }
  } else if (mode === "recovery") {
    const unique = [
      ...new Map(weak.map((w) => [`${w.unit}-${w.original}`, w])).values(),
    ];
    const source = unique.length
      ? unique
      : bank.map((q) => ({ unit: q.unit, original: q.original }));
    selected = shuffle(source, rng)
      .slice(0, 10)
      .map((w) => {
        let next = makeQuestion(w.unit, w.original, variant);
        const last = previous
          .filter((id) => id.startsWith(`u${w.unit}-q${w.original}-v`))
          .at(-1);
        if (last) {
          const old = makeQuestion(
            w.unit,
            w.original,
            Number(last.split("-v")[1]),
          );
          const same = (q: Question) =>
            q.prompt === old.prompt &&
            JSON.stringify(q.options) === JSON.stringify(old.options) &&
            q.answer === old.answer;
          for (let offset = 1; offset <= 100 && same(next); offset++)
            next = makeQuestion(w.unit, w.original, variant + offset);
        }
        return next;
      });
  } else {
    const source = shuffle(
      bank.filter((q) => q.unit === unit && q.original < 10),
      rng,
    );
    selected = source
      .slice(0, 7)
      .map((q) => makeQuestion(q.unit, q.original, variant));
    if (
      selected.every((q) =>
        previous.some((id) => id.split("-v")[0] === q.id.split("-v")[0]),
      )
    )
      selected = source
        .slice(2, 9)
        .map((q) => makeQuestion(q.unit, q.original, variant + 1));
  }
  return {
    id: `exam-${seed}-${Math.round(rng() * 1e8)}`,
    mode,
    unit,
    questions: shuffle(selected, rng),
    answers: {},
    deadline: null,
    startedAt: Date.now(),
  };
}
export const remainingSeconds = (deadline: number, now = Date.now()) =>
  Math.max(0, Math.ceil((deadline - now) / 1000));
export function finishExam(exam: Exam): Attempt {
  const wrong = exam.questions
    .filter((q) => !grade(q, exam.answers[q.id] ?? ""))
    .map((q) => q.id);
  return {
    id: exam.id,
    mode: exam.mode,
    unit: exam.unit,
    score: Math.round(
      ((exam.questions.length - wrong.length) / exam.questions.length) * 100,
    ),
    date: Date.now(),
    questions: exam.questions,
    answers: { ...exam.answers },
    wrong,
  };
}
export function weakQuestions(
  attempts: Attempt[],
): { unit: number; original: number }[] {
  const status = new Map<
    string,
    { unit: number; original: number; wrong: boolean }
  >();
  for (const a of attempts)
    for (const q of a.questions)
      status.set(`${q.unit}-${q.original}`, {
        unit: q.unit,
        original: q.original,
        wrong: !grade(q, a.answers[q.id] ?? ""),
      });
  return [...status.values()].filter((v) => v.wrong);
}
