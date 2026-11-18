import { useEffect, useState } from "react";
import {
  Clock3,
  Check,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import {
  type Exam,
  type Attempt,
  grade,
  remainingSeconds,
} from "../domain/assessment";
import { lessons } from "../content/lessons";
export function ExamSetup({
  onStart,
  mode = "final",
  weakCount = 0,
}: {
  onStart: (minutes: number) => void;
  mode?: "final" | "recovery";
  weakCount?: number;
}) {
  const [minutes, setMinutes] = useState(60);
  return (
    <div className="exam-setup panel">
      <div className="exam-orb">
        <Clock3 size={40} />
      </div>
      <div className="eyebrow">
        {mode === "final"
          ? "SIMULACRO UNIVERSITARIO"
          : "RECUPERACIÓN PERSONALIZADA"}
      </div>
      <h2>
        {mode === "final"
          ? "Pon a prueba tu criterio."
          : "Convierte los errores en dominio."}
      </h2>
      <p>
        {mode === "final"
          ? "30 preguntas de aplicación, cálculo e interpretación. Incluye código, árboles, selección y operadores genéticos. Las respuestas se corrigen solo al entregar."
          : `${weakCount} conceptos con respuestas pendientes. Practicarás nuevas variantes centradas en tus errores recientes; si aún no hay errores, usarás un repaso general.`}
      </p>
      <div className="setup-details">
        <span>
          <Check size={16} /> Resultados por tema
        </span>
        <span>
          <Check size={16} /> Corrección razonada
        </span>
        <span>
          <Check size={16} /> Progreso local
        </span>
      </div>
      {mode === "final" && (
        <label className="field narrow">
          Tiempo disponible
          <select
            value={minutes}
            onChange={(e) => setMinutes(Number(e.target.value))}
          >
            {[30, 45, 60, 90, 120].map((m) => (
              <option key={m} value={m}>
                {m} minutos
              </option>
            ))}
          </select>
        </label>
      )}
      <button
        className="primary large"
        onClick={() => onStart(mode === "final" ? minutes : 0)}
      >
        {mode === "final" ? "Comenzar simulacro" : "Comenzar recuperación"}{" "}
        <ChevronRight size={18} />
      </button>
      <p className="muted">
        Puedes cambiar de sección y reanudar. Recargar conserva tus respuestas;
        en el simulacro el reloj sigue corriendo.
      </p>
    </div>
  );
}
export function Assessment({
  exam,
  onChange,
  onSubmit,
}: {
  exam: Exam;
  onChange: (e: Exam) => void;
  onSubmit: () => void;
}) {
  const [current, setCurrent] = useState(0),
    [seconds, setSeconds] = useState(
      exam.deadline ? remainingSeconds(exam.deadline) : 0,
    );
  const q = exam.questions[Math.min(current, exam.questions.length - 1)];
  const answered = exam.questions.filter(
    (q) => !!exam.answers[q.id]?.trim(),
  ).length;
  useEffect(() => {
    if (!exam.deadline) return;
    const tick = () => {
      const left = remainingSeconds(exam.deadline!);
      setSeconds(left);
      if (left === 0) onSubmit();
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [exam.deadline, onSubmit]);
  function answer(value: string) {
    onChange({ ...exam, answers: { ...exam.answers, [q.id]: value } });
  }
  const response = exam.answers[q.id] ?? "";
  const orderValues = response ? response.split(",") : [];
  return (
    <div className="assessment">
      <div className="exam-header">
        <div>
          <div className="eyebrow">
            {exam.mode === "final"
              ? "SIMULACRO"
              : exam.mode === "unit"
                ? `UNIDAD ${exam.unit}`
                : "RECUPERACIÓN"}
          </div>
          <h2>
            {exam.questions.length} preguntas · {answered} respondidas
          </h2>
        </div>
        {exam.deadline && (
          <span className={"timer " + (seconds < 120 ? "urgent" : "")}>
            <Clock3 size={18} />
            {Math.floor(seconds / 60)
              .toString()
              .padStart(2, "0")}
            :{(seconds % 60).toString().padStart(2, "0")}
          </span>
        )}
      </div>
      <div className="bar">
        <i style={{ width: `${(answered / exam.questions.length) * 100}%` }} />
      </div>
      <div className="question-nav">
        {exam.questions.map((question, i) => (
          <button
            key={question.id}
            aria-label={`Ir a pregunta ${i + 1}`}
            className={
              (i === current ? "current " : "") +
              (exam.answers[question.id] ? "answered" : "")
            }
            onClick={() => setCurrent(i)}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <section className="panel question">
        <span className="badge">
          Pregunta {current + 1} / {exam.questions.length}
        </span>
        <span className="muted">
          {" "}
          Unidad {q.unit} · {q.concept}
        </span>
        <h3>{q.prompt}</h3>
        {q.code && <pre>{q.code}</pre>}
        {q.type === "choice" ? (
          <div className="choices">
            {q.options!.map((option, i) => (
              <label
                className={"choice " + (response === String(i) ? "chosen" : "")}
                key={i}
              >
                <input
                  name={q.id}
                  type="radio"
                  checked={response === String(i)}
                  onChange={() => answer(String(i))}
                />
                <b>{String.fromCharCode(65 + i)}</b>
                <span>{option}</span>
              </label>
            ))}
          </div>
        ) : q.type === "number" ? (
          <label className="field">
            Resultado numérico (tolerancia absoluta ±{q.tolerance ?? 0.001})
            <input
              inputMode="decimal"
              autoComplete="off"
              value={response}
              onChange={(e) => answer(e.target.value)}
              placeholder="Escribe tu cálculo final"
            />
          </label>
        ) : (
          <div>
            <p>
              Pulsa los pasos en el orden correcto. También puedes escribir su
              numeración separada por comas.
            </p>
            <div className="choices">
              {q.options!.map((option, i) => (
                <button
                  className={
                    "choice " +
                    (orderValues.includes(String(i + 1)) ? "chosen" : "")
                  }
                  key={i}
                  disabled={orderValues.includes(String(i + 1))}
                  onClick={() =>
                    answer([...orderValues, String(i + 1)].join(","))
                  }
                >
                  {i + 1}. {option}
                </button>
              ))}
            </div>
            <label className="field">
              Orden elegido
              <input
                value={response}
                placeholder="2,1,3"
                onChange={(e) => answer(e.target.value)}
              />
            </label>
            <button onClick={() => answer("")}>Limpiar orden</button>
          </div>
        )}
        <div className="question-footer">
          <button
            disabled={current === 0}
            onClick={() => setCurrent(current - 1)}
          >
            <ChevronLeft size={16} /> Anterior
          </button>
          <button
            disabled={current === exam.questions.length - 1}
            onClick={() => setCurrent(current + 1)}
          >
            Siguiente <ChevronRight size={16} />
          </button>
        </div>
      </section>
      <div className="exam-submit">
        <p className="muted">
          <AlertCircle size={16} /> {exam.questions.length - answered} sin
          responder. Las respuestas vacías cuentan como incorrectas.
        </p>
        <button className="primary" onClick={onSubmit}>
          {exam.mode === "final" ? "Entregar simulacro" : "Entregar evaluación"}
        </button>
      </div>
    </div>
  );
}
function responseText(q: Attempt["questions"][number], answer: string) {
  return !answer
    ? "Sin respuesta"
    : q.type === "choice"
      ? (q.options?.[Number(answer)] ?? "Respuesta no válida")
      : answer;
}
export function Result({
  attempt,
  onRetry,
  onRecovery,
}: {
  attempt: Attempt;
  onRetry: () => void;
  onRecovery: () => void;
}) {
  const [filter, setFilter] = useState(0);
  const right = attempt.questions.length - attempt.wrong.length;
  return (
    <>
      <section className="panel result-hero">
        <div>
          <div className="eyebrow">RESULTADO GUARDADO</div>
          <h2>
            {attempt.score >= 80
              ? "Buen trabajo. Sigue profundizando."
              : "Ya sabemos qué necesitas practicar."}
          </h2>
          <p>
            {right} de {attempt.questions.length} correctas ·{" "}
            {new Date(attempt.date).toLocaleDateString("es-MX")}
          </p>
          <div className="actions">
            <button className="primary" onClick={onRetry}>
              Nuevo intento
            </button>
            <button onClick={onRecovery}>Repasar errores</button>
          </div>
        </div>
        <strong className="score">{attempt.score}%</strong>
      </section>
      <section className="panel">
        <h3>Corrección completa</h3>
        <label className="field narrow">
          Revisar por tema
          <select
            value={filter}
            onChange={(e) => setFilter(Number(e.target.value))}
          >
            <option value={0}>Todos los temas</option>
            {[...new Set(attempt.questions.map((q) => q.unit))]
              .sort()
              .map((u) => (
                <option key={u} value={u}>
                  {u}. {lessons[u - 1].title}
                </option>
              ))}
          </select>
        </label>
        {attempt.questions
          .filter((q) => !filter || q.unit === filter)
          .map((q) => {
            const chosen = attempt.answers[q.id] ?? "",
              correct = grade(q, chosen);
            return (
              <article
                className={"correction " + (correct ? "right" : "wrong")}
                key={q.id}
              >
                <div className="eyebrow">
                  UNIDAD {q.unit} · {q.concept} ·{" "}
                  {correct ? "CORRECTA" : "POR REPASAR"}
                </div>
                <h4>{q.prompt}</h4>
                {q.code && <pre>{q.code}</pre>}
                <p>
                  Tu respuesta: <strong>{responseText(q, chosen)}</strong>
                </p>
                {!correct && (
                  <p className="error-text">
                    {chosen
                      ? "La respuesta elegida no satisface la regla o el cálculo de este problema."
                      : "Faltó responder este problema."}{" "}
                    Solución: <strong>{responseText(q, q.answer)}</strong>
                  </p>
                )}
                <p className="explanation">{q.explanation}</p>
                {!correct && (
                  <span className="badge warning">Repasar: {q.concept}</span>
                )}
              </article>
            );
          })}
      </section>
    </>
  );
}
