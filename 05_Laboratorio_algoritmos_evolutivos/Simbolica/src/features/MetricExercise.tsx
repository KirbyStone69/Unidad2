import { useState } from "react";
import { metrics, fmt } from "../domain/metrics";
export function MetricExercise() {
  const [k, setK] = useState(2),
    [answers, setAnswers] = useState<Record<string, string>>({}),
    [checked, setChecked] = useState(false);
  const y = [k, k + 2, k + 4],
    p = [k - 1, k + 3, k + 5],
    m = metrics(y, p);
  const fields = [
    { id: "residue", label: "y−ŷ en fila 1", value: 1 },
    { id: "square", label: "(y−ŷ)² en fila 1", value: 1 },
    { id: "mean", label: "Media real ȳ", value: m.mean },
    { id: "sse", label: "SSE total", value: m.sse },
    { id: "mse", label: "MSE", value: m.mse },
    { id: "nmse", label: "NMSE", value: m.nmse! },
    { id: "r2", label: "R²", value: m.r2! },
  ];
  const correct = (id: string, value: number) =>
    answers[id]?.trim() &&
    Number.isFinite(Number(answers[id].replace(",", "."))) &&
    Math.abs(Number(answers[id].replace(",", ".")) - value) <= 0.001;
  return (
    <div className="metric-exercise inset">
      <div className="eyebrow">EJERCICIO DE CELDAS FALTANTES</div>
      <h4>Completa la tabla y las métricas</h4>
      <p>
        Datos nuevos para calcular sin consultar la tabla anterior. Usa
        tolerancia ±0.001.
      </p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Fila</th>
              <th>y</th>
              <th>ŷ</th>
            </tr>
          </thead>
          <tbody>
            {y.map((v, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td>{v}</td>
                <td>{p[i]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="exercise-fields">
        {fields.map((f) => (
          <label className="field" key={f.id}>
            {f.label}
            <input
              aria-label={`${f.label} a calcular`}
              inputMode="decimal"
              value={answers[f.id] ?? ""}
              onChange={(e) => {
                setAnswers({ ...answers, [f.id]: e.target.value });
                setChecked(false);
              }}
            />
            {checked && (
              <small
                className={correct(f.id, f.value) ? "accent" : "error-text"}
              >
                {correct(f.id, f.value)
                  ? "Correcto"
                  : `Revisa: ${fmt(f.value)}`}
              </small>
            )}
          </label>
        ))}
      </div>
      <div className="actions">
        <button className="primary" onClick={() => setChecked(true)}>
          Corregir celdas
        </button>
        <button
          onClick={() => {
            setK((v) => (v % 6) + 2);
            setAnswers({});
            setChecked(false);
          }}
        >
          Nueva variante
        </button>
      </div>
      {checked && (
        <div className="feedback success">
          <strong>
            {fields.filter((f) => correct(f.id, f.value)).length} de{" "}
            {fields.length} celdas correctas
          </strong>
          <p>
            Residuos: [1,−1,−1]. Cuadrados: [1,1,1]. SSE=3; MSE=3/3=1. Media=
            {k + 2}; SST=4+0+4=8. Energía={y.map((v) => v * v).join("+")}=
            {m.energy}. NMSE=3/{m.energy}={fmt(m.nmse)}. R²=1−3/8=0.625.
          </p>
        </div>
      )}
    </div>
  );
}
