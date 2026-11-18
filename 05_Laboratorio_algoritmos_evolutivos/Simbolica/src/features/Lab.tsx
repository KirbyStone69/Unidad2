import { useEffect, useRef, useState } from "react";
import {
  Upload,
  Download,
  Play,
  Pause,
  RotateCcw,
  FlaskConical,
} from "lucide-react";
import { referenceData, parseCSV } from "../domain/csv";
import { type Individual, type Point } from "../domain/evolution";
import { evaluate, expression, terminal, node } from "../domain/tree";
import { metrics, fmt } from "../domain/metrics";
import { Plot } from "../components/Plot";
import { TreeView } from "../components/TreeView";
export function download(
  name: string,
  content: string,
  type = "application/json",
) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
interface State {
  population: Individual[];
  generation: number;
  mean: number | null;
  invalid: number;
  done: boolean;
}
export function Lab() {
  const [data, setData] = useState(referenceData),
    [source, setSource] = useState("Referencia · 1000 puntos"),
    [errors, setErrors] = useState<string[]>([]),
    [seed, setSeed] = useState(42),
    [pop, setPop] = useState(32),
    [maxHeight, setMaxHeight] = useState(4),
    [generations, setGenerations] = useState(60),
    [pm, setPm] = useState(0.3),
    [state, setState] = useState<State | null>(null),
    [running, setRunning] = useState(false),
    [history, setHistory] = useState<Point[]>([]),
    [means, setMeans] = useState<Point[]>([]),
    [selected, setSelected] = useState(0),
    [compare, setCompare] = useState("evolved");
  const worker = useRef<Worker | null>(null);
  useEffect(() => () => worker.current?.terminate(), []);
  function reset() {
    worker.current?.terminate();
    worker.current = null;
    setState(null);
    setHistory([]);
    setMeans([]);
    setRunning(false);
    setSelected(0);
  }
  function start() {
    reset();
    try {
      const w = new Worker(new URL("../evolution.worker.ts", import.meta.url), {
        type: "module",
      });
      worker.current = w;
      w.onmessage = (e) => {
        if (e.data.type === "error") {
          setErrors([e.data.message]);
          setRunning(false);
          return;
        }
        const s = e.data as State;
        setState(s);
        setHistory((h) => [
          ...h,
          { x: s.generation, y: s.population[0].error },
        ]);
        if (s.mean !== null)
          setMeans((h) => [...h, { x: s.generation, y: s.mean! }]);
        if (s.done) setRunning(false);
      };
      w.onerror = () => {
        setErrors([
          "El motor no pudo ejecutarse. Revisa la consola o reinicia el laboratorio.",
        ]);
        setRunning(false);
      };
      w.postMessage({
        type: "start",
        data,
        seed,
        population: pop,
        generations,
        config: { maxHeight, mutationRate: pm, elite: 1 },
      });
      setRunning(true);
    } catch (e) {
      setErrors([String(e)]);
    }
  }
  function control(type: "pause" | "resume" | "step") {
    worker.current?.postMessage({ type });
    setRunning(type === "resume");
  }
  const evolved =
    state?.population[Math.min(selected, (state?.population.length ?? 1) - 1)]
      ?.tree;
  const candidate =
    compare === "square"
      ? node("^", terminal("x"), terminal(2))
      : compare === "linear"
        ? node("+", terminal("x"), terminal(1))
        : evolved;
  let predictions: Point[] = [],
    errorMessage = "",
    m: ReturnType<typeof metrics> | null = null;
  if (candidate) {
    try {
      predictions = data.map((p) => ({ x: p.x, y: evaluate(candidate, p.x) }));
      m = metrics(
        data.map((p) => p.y),
        predictions.map((p) => p.y),
      );
    } catch (e) {
      errorMessage = e instanceof Error ? e.message : "Candidata inválida";
      predictions = [];
    }
  }
  async function load(file: File) {
    if (file.size > 5_000_000) {
      setErrors(["El CSV no debe superar 5 MB."]);
      return;
    }
    try {
      const result = parseCSV(await file.text());
      setErrors(result.errors);
      if (!result.errors.length) {
        reset();
        setData(result.points);
        setSource(file.name);
      }
    } catch {
      setErrors(["No se pudo leer el archivo."]);
    }
  }
  return (
    <>
      <header className="page-heading">
        <div className="eyebrow">EXPERIMENTA / LABORATORIO FINAL</div>
        <h1>
          De los puntos a la expresión<span className="accent">.</span>
        </h1>
        <p>
          Una búsqueda evolutiva real y acotada. El motor recibe datos,
          operadores y una semilla; no recibe la fórmula generadora.
        </p>
      </header>
      <div className="lab-banner">
        <FlaskConical size={22} />
        <div>
          <strong>PG real simplificada</strong>
          <span>
            Torneo binario · cruce de ramas · cuatro mutaciones · poda · una
            élite. No garantiza recuperar la ecuación original.
          </span>
        </div>
      </div>
      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">01 / DATOS</div>
            <h3>{source}</h3>
          </div>
          <span className="badge">{data.length} muestras</span>
        </div>
        <div className="actions">
          <label className="button upload">
            <Upload size={16} /> Cargar CSV
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void load(f);
                e.target.value = "";
              }}
            />
          </label>
          <button
            onClick={() =>
              download(
                "referencia.csv",
                "x,y\n" +
                  referenceData()
                    .map((p) => `${p.x},${p.y}`)
                    .join("\n"),
                "text/csv",
              )
            }
          >
            <Download size={16} /> Descargar referencia
          </button>
          <button
            onClick={() => {
              reset();
              setData(referenceData());
              setSource("Referencia · 1000 puntos");
              setErrors([]);
            }}
          >
            Restaurar referencia
          </button>
        </div>
        <p className="muted">
          Referencia: y=6.67+11·cos(7.23·x³), x∈[0,1]. CSV: x,y; encabezado
          opcional, coma o punto y coma, punto decimal. Máximo 50 000 filas / 5
          MB. Una fila inválida bloquea toda la importación y conserva los datos
          anteriores.
        </p>
        {errors.length > 0 && (
          <div role="alert" className="feedback error">
            {errors.slice(0, 8).map((e) => (
              <p key={e}>{e}</p>
            ))}
            {errors.length > 8 && (
              <p>Y {errors.length - 8} errores adicionales.</p>
            )}
          </div>
        )}
        <Plot
          series={[
            {
              name: "Observaciones",
              points: data,
              color: "#39FF88",
              dots: true,
            },
            ...(predictions.length
              ? [
                  {
                    name: "Candidata",
                    points: [...predictions].sort((a, b) => a.x - b.x),
                    color: "#FFB84D",
                  },
                ]
              : []),
          ]}
        />
        <div className="controls">
          <label>
            Comparar
            <select
              value={compare}
              onChange={(e) => setCompare(e.target.value)}
            >
              <option value="evolved">Individuo evolutivo seleccionado</option>
              <option value="square">Manual: x²</option>
              <option value="linear">Manual: x+1</option>
            </select>
          </label>
          {state && (
            <label>
              Individuo
              <select
                value={selected}
                onChange={(e) => setSelected(Number(e.target.value))}
              >
                {state.population.map((i, k) => (
                  <option key={k} value={k}>
                    #{k + 1} · MSE {fmt(i.error)}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {candidate && (
          <div className="candidate">
            <code>{expression(candidate)}</code>
            {errorMessage ? (
              <p className="error-text">
                Inválido en los datos: {errorMessage}
              </p>
            ) : (
              m && (
                <div className="metric-inline">
                  MSE <strong>{fmt(m.mse)}</strong> NMSE{" "}
                  <strong>{fmt(m.nmse)}</strong> R² <strong>{fmt(m.r2)}</strong>
                </div>
              )
            )}
          </div>
        )}
      </section>
      <section className="panel">
        <div className="eyebrow">02 / BÚSQUEDA</div>
        <h3>Configura el presupuesto</h3>
        <div className="controls">
          {[
            {
              label: "Semilla",
              value: seed,
              set: setSeed,
              min: 1,
              max: 999999,
            },
            { label: "Población", value: pop, set: setPop, min: 8, max: 64 },
            {
              label: "Altura máxima",
              value: maxHeight,
              set: setMaxHeight,
              min: 1,
              max: 5,
            },
            {
              label: "Generaciones",
              value: generations,
              set: setGenerations,
              min: 1,
              max: 200,
            },
          ].map((v) => (
            <label key={v.label}>
              {v.label}
              <input
                disabled={!!state}
                type="number"
                value={v.value}
                min={v.min}
                max={v.max}
                onChange={(e) =>
                  v.set(
                    Math.max(
                      v.min,
                      Math.min(v.max, Math.floor(Number(e.target.value))),
                    ),
                  )
                }
              />
            </label>
          ))}
          <label>
            Pm
            <input
              disabled={!!state}
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={pm}
              onChange={(e) =>
                setPm(Math.max(0, Math.min(1, Number(e.target.value))))
              }
            />
          </label>
        </div>
        <div className="actions">
          <button className="primary" disabled={!!state} onClick={start}>
            <Play size={16} /> Iniciar búsqueda
          </button>
          <button
            disabled={!state || state.done}
            onClick={() => control(running ? "pause" : "resume")}
          >
            {running ? <Pause size={16} /> : <Play size={16} />}{" "}
            {running ? "Pausar" : "Reproducir"}
          </button>
          <button
            disabled={!state || state.done}
            onClick={() => control("step")}
          >
            Siguiente generación
          </button>
          <button onClick={reset}>
            <RotateCcw size={16} /> Reiniciar
          </button>
        </div>
        {state && (
          <>
            <div className="stat-grid">
              <div className="stat">
                <small>Generación</small>
                <strong>
                  {state.generation} / {generations}
                </strong>
                <span>
                  {state.done
                    ? "Presupuesto completado"
                    : running
                      ? "Buscando"
                      : "En pausa"}
                </span>
              </div>
              <div className="stat">
                <small>Mejor MSE</small>
                <strong>{fmt(state.population[0].error)}</strong>
                <span>Entrenamiento · {data.length} puntos</span>
              </div>
              <div className="stat">
                <small>Individuos inválidos</small>
                <strong>
                  {state.invalid} / {pop}
                </strong>
                <span>Penalización: error infinito</span>
              </div>
            </div>
            <Plot
              xLabel="generación"
              yLabel="MSE"
              series={[
                {
                  name: "Mejor poblacional (con élite)",
                  points: history.filter((p) => Number.isFinite(p.y)),
                  color: "#39FF88",
                },
                {
                  name: "Promedio finito",
                  points: means.filter((p) => Number.isFinite(p.y)),
                  color: "#89BFFF",
                },
              ]}
            />
            {candidate && <TreeView tree={candidate} />}
          </>
        )}
        <p className="callout">
          La curva muestra error de entrenamiento, no de validación. Todas las
          métricas usan todas las filas; solo el dibujo se submuestrea. Las
          constantes iniciales son aleatorias en [−5,5] y pueden combinarse; no
          existe una plantilla con la solución objetivo.
        </p>
      </section>
    </>
  );
}
