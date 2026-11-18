import { useState } from "react";
import {
  Check,
  BookOpen,
  FlaskConical,
  PencilLine,
  ArrowRight,
} from "lucide-react";
import { lessons } from "../content/lessons";
import { Formula } from "../components/Math";
import { Practice } from "../components/Practice";
import { Activities } from "./Activities";
export function Lessons({
  unit,
  read,
  onRead,
  onExam,
}: {
  unit: number;
  read: boolean;
  onRead: () => void;
  onExam: () => void;
}) {
  const [tab, setTab] = useState("lesson");
  const lesson = lessons[unit - 1];
  return (
    <>
      <header className="page-heading">
        <div className="eyebrow">
          RUTA DE APRENDIZAJE / UNIDAD {String(unit).padStart(2, "0")}
        </div>
        <h1>{lesson.title}</h1>
        <p>{lesson.intro}</p>
        <div className="heading-meta">
          <span>{lesson.duration} de estudio</span>
          <span>10 ejercicios originales</span>
          <span>{read ? "Lectura registrada" : "A tu ritmo"}</span>
        </div>
      </header>
      <div className="lesson-tabs">
        <button
          className={tab === "lesson" ? "active" : ""}
          onClick={() => setTab("lesson")}
        >
          <BookOpen size={17} /> Lección
        </button>
        <button
          className={tab === "lab" ? "active" : ""}
          onClick={() => setTab("lab")}
        >
          <FlaskConical size={17} /> Laboratorio
        </button>
        <button
          className={tab === "practice" ? "active" : ""}
          onClick={() => setTab("practice")}
        >
          <PencilLine size={17} /> Práctica
        </button>
        <button className="assessment-link" onClick={onExam}>
          Evaluación de la unidad <ArrowRight size={17} />
        </button>
      </div>
      {tab === "lesson" ? (
        <>
          <section className="panel objectives">
            <div className="eyebrow">AL TERMINAR PODRÁS</div>
            {lesson.objectives.map((t) => (
              <span key={t}>
                <Check size={16} />
                {t}
              </span>
            ))}
          </section>
          {lesson.sections.map((section, i) => (
            <section className="panel lesson-section" key={section.title}>
              <span className="section-number">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h2>{section.title}</h2>
                <p>{section.text}</p>
                {section.formula && <Formula value={section.formula} />}
                <div className="worked">
                  <div className="eyebrow">EJEMPLO RESUELTO</div>
                  <p>{section.example}</p>
                </div>
                <details>
                  <summary>Comprueba: {section.check}</summary>
                  <p>{section.answer}</p>
                </details>
              </div>
            </section>
          ))}
          <section className="panel">
            <div className="eyebrow">LO ESENCIAL</div>
            <h3>Antes de seguir</h3>
            <ul>
              {lesson.summary.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
            <div className="actions">
              <button
                className="primary"
                onClick={() => {
                  onRead();
                  setTab("lab");
                }}
              >
                {read
                  ? "Volver al laboratorio"
                  : "Registrar lectura e ir al laboratorio"}{" "}
                <ArrowRight size={16} />
              </button>
              <button onClick={() => setTab("practice")}>
                Practicar ahora
              </button>
            </div>
          </section>
        </>
      ) : tab === "lab" ? (
        <Activities unit={unit} />
      ) : (
        <Practice unit={unit} />
      )}
    </>
  );
}
