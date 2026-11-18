import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  FlaskConical,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Network,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from "lucide-react";
import { loadProgress, saveProgress, type Progress } from "./domain/storage";
import {
  buildExam,
  finishExam,
  weakQuestions,
  type ExamMode,
  type Attempt,
} from "./domain/assessment";
import { bank } from "./content/questions";
import { lessons } from "./content/lessons";
import { Lessons } from "./features/Lessons";
import { Assessment, ExamSetup, Result } from "./features/Assessment";
import { ProgressView } from "./features/Progress";
import { Lab } from "./features/Lab";
import { TreeView } from "./components/TreeView";
import { simpleTree } from "./domain/tree";
type Route =
  | "home"
  | "unit"
  | "final"
  | "recovery"
  | "assessment"
  | "result"
  | "progress"
  | "lab";
export default function App() {
  const [initial] = useState(loadProgress);
  const [progress, setProgress] = useState<Progress>(initial.progress),
    [warning, setWarning] = useState(initial.warning ?? ""),
    [route, setRoute] = useState<Route>("home"),
    [unit, setUnit] = useState(initial.progress.lastUnit),
    [result, setResult] = useState<Attempt | null>(null),
    [mobile, setMobile] = useState(false);
  useEffect(() => {
    const message = saveProgress(progress);
    if (message) setWarning(message);
  }, [progress]);
  const submit = useCallback(() => {
    setProgress((p) => {
      if (!p.activeExam) return p;
      const attempt = finishExam(p.activeExam);
      setResult(attempt);
      return { ...p, attempts: [...p.attempts, attempt], activeExam: null };
    });
    setRoute("result");
  }, []);
  // Deadline is enforced even when the student visits a different section.
  useEffect(() => {
    if (!progress.activeExam?.deadline) return;
    const id = setInterval(() => {
      if (
        progress.activeExam?.deadline &&
        Date.now() >= progress.activeExam.deadline
      )
        submit();
    }, 1000);
    return () => clearInterval(id);
  }, [progress.activeExam?.deadline, submit]);
  function go(r: Route) {
    setRoute(r);
    setMobile(false);
    window.scrollTo?.({ top: 0, behavior: "instant" });
  }
  function openUnit(u: number) {
    setUnit(u);
    setProgress((p) => ({ ...p, lastUnit: u }));
    go("unit");
  }
  function start(mode: ExamMode, u = 0, minutes = 0) {
    if (progress.activeExam) {
      go("assessment");
      return;
    }
    const previous =
      mode === "recovery"
        ? progress.attempts.flatMap((a) => a.questions.map((q) => q.id))
        : ([...progress.attempts]
            .reverse()
            .find((a) => a.mode === mode && a.unit === u)
            ?.questions.map((q) => q.id) ?? []);
    const exam = buildExam(
      mode,
      u,
      Date.now(),
      previous,
      weakQuestions(progress.attempts),
    );
    if (minutes) exam.deadline = Date.now() + minutes * 60_000;
    setProgress((p) => ({ ...p, activeExam: exam }));
    go("assessment");
  }
  const mastered = lessons.filter((l) =>
    progress.attempts.some(
      (a) => a.mode === "unit" && a.unit === l.id && a.score >= 80,
    ),
  ).length;
  const nav = [
    { route: "home" as Route, label: "Vista general", icon: LayoutDashboard },
    { route: "lab" as Route, label: "Laboratorio final", icon: FlaskConical },
    { route: "recovery" as Route, label: "Repasar errores", icon: RotateCcw },
    { route: "final" as Route, label: "Examen final", icon: GraduationCap },
    { route: "progress" as Route, label: "Mi progreso", icon: TrendingUp },
  ];
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (mobile ? "open" : "")}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            go("home");
          }}
        >
          <span className="brand-icon">
            <Network size={24} />
          </span>
          <span>
            SIMBÓLICA<small>GENETIC PROGRAMMING LAB</small>
          </span>
        </a>
        <button
          className="mobile-close"
          aria-label="Cerrar menú"
          onClick={() => setMobile(false)}
        >
          <X />
        </button>
        <div className="sidebar-label">ESPACIO DE ESTUDIO</div>
        <nav>
          {nav.map((item) => (
            <button
              aria-label={item.label}
              key={item.route}
              className={route === item.route ? "selected" : ""}
              onClick={() => go(item.route)}
            >
              <item.icon size={18} />
              {item.label}
              {route === item.route && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-divider" />
        <div className="sidebar-label">
          RUTA DE APRENDIZAJE <span>08</span>
        </div>
        <nav className="unit-nav">
          {lessons.map((l) => {
            const passed = progress.attempts.some(
              (a) => a.mode === "unit" && a.unit === l.id && a.score >= 80,
            );
            return (
              <button
                key={l.id}
                title={l.title}
                className={route === "unit" && unit === l.id ? "selected" : ""}
                onClick={() => openUnit(l.id)}
              >
                <span className={"nav-number " + (passed ? "passed" : "")}>
                  {passed ? <Check size={13} /> : String(l.id).padStart(2, "0")}
                </span>
                <span>{l.title}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div>
            <ShieldCheck size={17} />
            <span>Tu progreso se guarda aquí</span>
          </div>
          <small>Sin cuentas. A tu ritmo.</small>
          <div className="bar">
            <i style={{ width: `${(mastered / 8) * 100}%` }} />
          </div>
          <span>{mastered} de 8 unidades superadas</span>
        </div>
      </aside>
      {mobile && <div className="scrim" onClick={() => setMobile(false)} />}
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu"
            aria-label="Abrir menú"
            onClick={() => setMobile(true)}
          >
            <Menu />
          </button>
          <div className="breadcrumb">
            Academia <ChevronRight size={13} />{" "}
            <strong>Regresión simbólica</strong>
          </div>
          <div className="top-status">
            <span className="status-dot" /> MODO LOCAL{" "}
            <span className="avatar">TÚ</span>
          </div>
        </header>
        <main>
          {warning && (
            <div role="alert" className="feedback error">
              {warning}
              <button onClick={() => setWarning("")}>Cerrar aviso</button>
            </div>
          )}
          {progress.activeExam && route !== "assessment" && (
            <div className="resume-banner">
              <span>
                <Activity size={17} /> Tienes una evaluación en curso
                {progress.activeExam.deadline ? " · el reloj sigue activo" : ""}
                .
              </span>
              <button onClick={() => go("assessment")}>
                Reanudar evaluación <ArrowRight size={16} />
              </button>
            </div>
          )}
          {route === "home" ? (
            <>
              <header className="home-heading">
                <div>
                  <div className="eyebrow">
                    <span className="status-dot" /> APRENDE. EXPERIMENTA.
                    EVOLUCIONA.
                  </div>
                  <h1>
                    Las mejores ideas
                    <br />
                    también <span className="accent">evolucionan.</span>
                  </h1>
                  <p>
                    Domina la regresión simbólica con programación genética.
                    <br className="desktop-break" /> De tu primer árbol de
                    expresión a un examen universitario.
                  </p>
                  <div className="actions">
                    <button
                      className="primary large"
                      onClick={() => openUnit(progress.lastUnit)}
                    >
                      Continuar aprendizaje <ArrowRight size={18} />
                    </button>
                    <button className="large" onClick={() => go("lab")}>
                      <FlaskConical size={17} /> Explorar laboratorio
                    </button>
                  </div>
                  <div className="hero-details">
                    <span>
                      <BookOpen size={15} /> 8 unidades interactivas
                    </span>
                    <span>
                      <Target size={15} /> {bank.length} ejercicios originales
                    </span>
                    <span>
                      <ShieldCheck size={15} /> Sin registro
                    </span>
                  </div>
                </div>
                <div className="hero-visual">
                  <div className="floating-tag">EXPRESIÓN → PROGRAMA</div>
                  <TreeView tree={simpleTree} />
                  <div className="hero-equation">
                    f(x) = (x + 2) · (x − 3)
                    <span>
                      <i /> EXPLORA EL ESPACIO DE FUNCIONES
                    </span>
                  </div>
                </div>
              </header>
              <div className="stat-grid dashboard-stats">
                <div className="stat">
                  <div>
                    <BookOpen size={18} />
                    <small>Tu recorrido</small>
                  </div>
                  <strong>
                    {mastered}
                    <em>/ 8</em>
                  </strong>
                  <span>unidades superadas</span>
                </div>
                <div className="stat">
                  <div>
                    <Target size={18} />
                    <small>Práctica acumulada</small>
                  </div>
                  <strong>{progress.attempts.length}</strong>
                  <span>evaluaciones entregadas</span>
                </div>
                <div className="stat">
                  <div>
                    <TrendingUp size={18} />
                    <small>Mejor calificación</small>
                  </div>
                  <strong>
                    {progress.attempts.length
                      ? Math.max(...progress.attempts.map((a) => a.score)) + "%"
                      : "—"}
                  </strong>
                  <span>
                    {progress.attempts.length
                      ? "sigue construyendo tu dominio"
                      : "tu primer intento te espera"}
                  </span>
                </div>
              </div>
              <section className="learning-path">
                <div className="section-heading">
                  <div>
                    <div className="eyebrow">TU MAPA DE CONOCIMIENTO</div>
                    <h2>Una idea a la vez.</h2>
                  </div>
                  <span className="muted">Fundamentos → aplicación</span>
                </div>
                <div className="unit-grid">
                  {lessons.map((l) => {
                    const attempts = progress.attempts.filter(
                        (a) => a.mode === "unit" && a.unit === l.id,
                      ),
                      best = attempts.length
                        ? Math.max(...attempts.map((a) => a.score))
                        : null;
                    return (
                      <button
                        className="unit-card"
                        key={l.id}
                        onClick={() => openUnit(l.id)}
                      >
                        <div className="unit-card-top">
                          <span className="unit-index">
                            {String(l.id).padStart(2, "0")}
                          </span>
                          <span
                            className={
                              "badge " +
                              (best !== null && best >= 80 ? "" : "neutral")
                            }
                          >
                            {best !== null
                              ? best >= 80
                                ? "Superada"
                                : "En práctica"
                              : progress.read.includes(l.id)
                                ? "Leída"
                                : "Por explorar"}
                          </span>
                        </div>
                        <h3>{l.title}</h3>
                        <p>{l.short}</p>
                        <div className="card-bottom">
                          <span>{l.duration} · 10 ejercicios</span>
                          <ArrowRight size={17} />
                        </div>
                        <div className="bar">
                          <i style={{ width: `${best ?? 0}%` }} />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>
              <section className="final-promo">
                <div className="promo-icon">
                  <GraduationCap size={30} />
                </div>
                <div>
                  <div className="eyebrow">EL SIGUIENTE DESAFÍO</div>
                  <h3>Piensa como en el examen.</h3>
                  <p>
                    30 preguntas, tiempo configurable y corrección completa por
                    tema.
                  </p>
                </div>
                <button onClick={() => go("final")}>
                  Preparar simulacro <ArrowRight size={17} />
                </button>
              </section>
              <div className="footer-note">
                <Sparkles size={14} /> Comprender el proceso vale más que
                memorizar una respuesta.
              </div>
            </>
          ) : route === "unit" ? (
            <Lessons
              key={unit}
              unit={unit}
              read={progress.read.includes(unit)}
              onRead={() =>
                setProgress((p) => ({
                  ...p,
                  read: [...new Set([...p.read, unit])],
                }))
              }
              onExam={() => start("unit", unit)}
            />
          ) : route === "assessment" && progress.activeExam ? (
            <Assessment
              exam={progress.activeExam}
              onChange={(exam) =>
                setProgress((p) => ({ ...p, activeExam: exam }))
              }
              onSubmit={submit}
            />
          ) : route === "result" && result ? (
            <Result
              attempt={result}
              onRetry={() =>
                result.mode === "final"
                  ? go("final")
                  : start(result.mode, result.unit)
              }
              onRecovery={() => go("recovery")}
            />
          ) : route === "final" ? (
            <ExamSetup onStart={(minutes) => start("final", 0, minutes)} />
          ) : route === "recovery" ? (
            <ExamSetup
              mode="recovery"
              weakCount={weakQuestions(progress.attempts).length}
              onStart={() => start("recovery")}
            />
          ) : route === "progress" ? (
            <ProgressView
              progress={progress}
              onReplace={setProgress}
              onReview={(id) => {
                setResult(progress.attempts.find((a) => a.id === id)!);
                go("result");
              }}
            />
          ) : route === "lab" ? (
            <Lab />
          ) : (
            <div className="panel">
              <h2>La evaluación ya fue entregada</h2>
              <button onClick={() => go("progress")}>
                Consultar historial
              </button>
            </div>
          )}
        </main>
        <footer className="site-footer">
          <span>SIMBÓLICA / Laboratorio de aprendizaje</span>
          <span>Construido para entender, no para memorizar.</span>
        </footer>
      </div>
    </div>
  );
}
