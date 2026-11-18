import { useState } from "react";
import { makeQuestion } from "../content/questions";
import { grade } from "../domain/assessment";
export function Practice({ unit }: { unit: number }) {
  const [index, setIndex] = useState(0),
    [answer, setAnswer] = useState(""),
    [checked, setChecked] = useState(false);
  const q = makeQuestion(unit, index, 1);
  return (
    <section className="panel">
      <div className="eyebrow">PRÁCTICA GUIADA · {index + 1}/10</div>
      <h3>{q.concept}</h3>
      <p>{q.prompt}</p>
      {q.code && <pre>{q.code}</pre>}
      {q.type === "choice" ? (
        <div className="choices">
          {q.options!.map((s, i) => (
            <label
              key={i}
              className={"choice " + (answer === String(i) ? "chosen" : "")}
            >
              <input
                type="radio"
                name="practice"
                checked={answer === String(i)}
                onChange={() => {
                  setAnswer(String(i));
                  setChecked(false);
                }}
              />
              {s}
            </label>
          ))}
        </div>
      ) : (
        <>
          <label className="field">
            {q.type === "order"
              ? "Ordena los números separados por comas"
              : "Tu resultado"}
            <input
              value={answer}
              onChange={(e) => {
                setAnswer(e.target.value);
                setChecked(false);
              }}
              placeholder={q.type === "order" ? "2,1,3" : "0"}
            />
          </label>
          {q.type === "order" && (
            <ol>
              {q.options!.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
          )}
        </>
      )}
      <div className="actions">
        <button
          className="primary"
          disabled={!answer}
          onClick={() => setChecked(true)}
        >
          Comprobar
        </button>
        <button
          onClick={() => {
            setIndex((index + 1) % 10);
            setAnswer("");
            setChecked(false);
          }}
        >
          Otro ejercicio →
        </button>
      </div>
      {checked && (
        <div className={"feedback " + (grade(q, answer) ? "success" : "error")}>
          <strong>
            {grade(q, answer) ? "Correcto." : "Revisemos el razonamiento."}
          </strong>
          <p>{q.explanation}</p>
        </div>
      )}
    </section>
  );
}
