import { useState } from "react";
import { Download, Upload, RotateCcw } from "lucide-react";
import { type Progress, parseProgress } from "../domain/storage";
import { weakQuestions } from "../domain/assessment";
import { lessons } from "../content/lessons";
import { Plot } from "../components/Plot";
import { download } from "./Lab";
export function ProgressView({
  progress,
  onReplace,
  onReview,
}: {
  progress: Progress;
  onReplace: (p: Progress) => void;
  onReview: (id: string) => void;
}) {
  const [message, setMessage] = useState(""),
    [confirm, setConfirm] = useState(false);
  const finals = progress.attempts.filter((a) => a.mode === "final"),
    weak = weakQuestions(progress.attempts);
  const mastered = lessons.filter((l) =>
    progress.attempts.some(
      (a) => a.mode === "unit" && a.unit === l.id && a.score >= 80,
    ),
  ).length;
  return (
    <>
      <header className="page-heading">
        <div className="eyebrow">TU APRENDIZAJE / ESTADÍSTICAS</div>
        <h1>
          Cada intento cuenta<span className="accent">.</span>
        </h1>
        <p>
          Resultados reales guardados en este navegador. Lectura, práctica y
          dominio se muestran por separado.
        </p>
      </header>
      <div className="stat-grid">
        <div className="stat">
          <small>Unidades superadas</small>
          <strong>
            {mastered}
            <em>/8</em>
          </strong>
          <span>Evaluación ≥80%</span>
        </div>
        <div className="stat">
          <small>Intentos realizados</small>
          <strong>{progress.attempts.length}</strong>
          <span>{finals.length} simulacros finales</span>
        </div>
        <div className="stat">
          <small>Mejor simulacro</small>
          <strong>
            {finals.length
              ? Math.max(...finals.map((a) => a.score)) + "%"
              : "—"}
          </strong>
          <span>{weak.length} conceptos por recuperar</span>
        </div>
      </div>
      <section className="panel">
        <h3>Evolución de calificaciones</h3>
        {progress.attempts.length ? (
          <Plot
            xLabel="intento"
            yLabel="nota %"
            series={[
              {
                name: "Calificación obtenida",
                points: progress.attempts.map((a, i) => ({
                  x: i + 1,
                  y: a.score,
                })),
                color: "#39FF88",
              },
            ]}
          />
        ) : (
          <p className="muted">
            Tu gráfica aparecerá al entregar la primera evaluación.
          </p>
        )}
      </section>
      <section className="panel">
        <h3>Dominio por unidad</h3>
        <div className="mastery-list">
          {lessons.map((l) => {
            const attempts = progress.attempts.filter(
                (a) => a.unit === l.id && a.mode === "unit",
              ),
              best = attempts.length
                ? Math.max(...attempts.map((a) => a.score))
                : 0;
            return (
              <div key={l.id}>
                <span className="unit-num">
                  {String(l.id).padStart(2, "0")}
                </span>
                <div>
                  <strong>{l.title}</strong>
                  <div className="bar">
                    <i style={{ width: `${best}%` }} />
                  </div>
                  <small>
                    {attempts.length} intentos ·{" "}
                    {progress.read.includes(l.id)
                      ? "lectura registrada"
                      : "lectura pendiente"}
                  </small>
                </div>
                <span className={best >= 80 ? "badge" : "muted"}>
                  {attempts.length ? best + "%" : "Sin evaluar"}
                </span>
              </div>
            );
          })}
        </div>
      </section>
      <section className="panel">
        <h3>Conceptos que necesitan repaso</h3>
        {weak.length ? (
          <div className="tags">
            {weak.map((w) => (
              <span className="badge warning" key={`${w.unit}-${w.original}`}>
                U{w.unit} ·{" "}
                {
                  progress.attempts
                    .flatMap((a) => a.questions)
                    .find((q) => q.unit === w.unit && q.original === w.original)
                    ?.concept
                }
              </span>
            ))}
          </div>
        ) : (
          <p className="muted">
            No hay errores pendientes registrados. Completa evaluaciones para
            medir tu dominio.
          </p>
        )}
        <h4>Errores recurrentes históricos</h4>
        <div className="tags">
          {Object.entries(
            progress.attempts
              .flatMap((a) => a.questions.filter((q) => a.wrong.includes(q.id)))
              .reduce<Record<string, number>>(
                (counts, q) => ({
                  ...counts,
                  [q.concept]: (counts[q.concept] ?? 0) + 1,
                }),
                {},
              ),
          )
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([concept, count]) => (
              <span className="badge" key={concept}>
                {concept} · {count}
              </span>
            ))}
        </div>
      </section>
      <section className="panel">
        <h3>Historial de intentos</h3>
        {progress.attempts.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Evaluación</th>
                  <th>Nota</th>
                  <th>Revisión</th>
                </tr>
              </thead>
              <tbody>
                {[...progress.attempts].reverse().map((a) => (
                  <tr key={a.id}>
                    <td>{new Date(a.date).toLocaleString("es-MX")}</td>
                    <td>
                      {a.mode === "final"
                        ? "Simulacro final"
                        : a.mode === "recovery"
                          ? "Recuperación"
                          : `Unidad ${a.unit}`}
                    </td>
                    <td>{a.score}%</td>
                    <td>
                      <button onClick={() => onReview(a.id)}>
                        Ver corrección
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">
            Todavía no hay intentos. Ninguna unidad se marca como completada
            automáticamente.
          </p>
        )}
      </section>
      <section className="panel">
        <h3>Tu copia de seguridad</h3>
        <p>
          Exporta el progreso para conservarlo o trasladarlo a otro navegador.
        </p>
        <div className="actions">
          <button
            onClick={() =>
              download(
                "simbolica-progreso.json",
                JSON.stringify(progress, null, 2),
              )
            }
          >
            <Download size={16} /> Exportar progreso
          </button>
          <label className="button upload">
            <Upload size={16} /> Importar copia
            <input
              type="file"
              accept=".json,application/json"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (file)
                  try {
                    if (file.size > 10_000_000)
                      throw new Error("La copia excede 10 MB.");
                    const p = parseProgress(await file.text());
                    onReplace(p);
                    setMessage("Copia importada correctamente.");
                  } catch (err) {
                    setMessage(
                      err instanceof Error ? err.message : "Copia no válida",
                    );
                  }
                e.target.value = "";
              }}
            />
          </label>
          <button className="danger" onClick={() => setConfirm(!confirm)}>
            <RotateCcw size={16} /> Borrar progreso
          </button>
        </div>
        {confirm && (
          <div className="feedback error">
            <p>
              Esto elimina intentos y respuestas locales. Exporta una copia si
              quieres conservarlos.
            </p>
            <button
              className="danger"
              onClick={() => {
                onReplace({
                  version: 1,
                  attempts: [],
                  read: [],
                  activeExam: null,
                  lastUnit: 1,
                });
                setConfirm(false);
                setMessage("Progreso borrado.");
              }}
            >
              Confirmar borrado
            </button>
            <button onClick={() => setConfirm(false)}>Cancelar</button>
          </div>
        )}
        {message && <p role="status">{message}</p>}
      </section>
    </>
  );
}
