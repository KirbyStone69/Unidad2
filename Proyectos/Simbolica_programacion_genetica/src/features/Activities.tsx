import { useEffect, useState } from "react";
import { TreeView, pathKey } from "../components/TreeView";
import { Plot } from "../components/Plot";
import {
  type Tree,
  type Path,
  type Mutation,
  arities,
  at,
  node,
  terminal,
  evaluate,
  exampleTree,
  simpleTree,
  expression,
  height,
  size,
  traversalPaths,
  randomTree,
  replace,
  seeded,
  crossover,
  paths,
  pick,
  mutate,
  repair,
  clone,
} from "../domain/tree";
import { metrics, fmt } from "../domain/metrics";
import { weights, sus, tournament } from "../domain/evolution";
import { MutationWheel } from "../components/MutationWheel";
import { MetricExercise } from "./MetricExercise";
import { EvolutionDemo } from "./EvolutionDemo";
export function Activities({ unit }: { unit: number }) {
  return (
    <section className="panel activity">
      <div className="eyebrow">
        LABORATORIO INTERACTIVO · UNIDAD {unit.toString().padStart(2, "0")}
      </div>
      {unit === 1 ? (
        <Inverse />
      ) : unit === 2 ? (
        <Editor />
      ) : unit === 3 ? (
        <Traversal />
      ) : unit === 4 ? (
        <Generator />
      ) : unit === 5 ? (
        <MetricsTable />
      ) : unit === 6 ? (
        <Selection />
      ) : unit === 7 ? (
        <Genetics />
      ) : (
        <EvolutionDemo />
      )}
    </section>
  );
}
const bounded = (v: string) =>
  Math.max(-10000, Math.min(10000, Number(v) || 0));
function Inverse() {
  const [show, setShow] = useState(false),
    [candidate, setCandidate] = useState("lineal"),
    [a, setA] = useState(1),
    [b, setB] = useState(0),
    [c, setC] = useState(0);
  const points = [
    { x: 1, y: 1 },
    { x: 2, y: 4 },
    { x: 3, y: 9 },
  ];
  const f = (x: number) =>
    candidate === "lineal"
      ? a * x + b
      : candidate === "cuadratica"
        ? a * x * x + b * x + c
        : x * x + a * (x - 1) * (x - 2) * (x - 3);
  const grid = Array.from({ length: 101 }, (_, i) => i * 0.04);
  const error = metrics(
    points.map((p) => p.y),
    points.map((p) => f(p.x)),
  );
  return (
    <>
      <h3>Los puntos no cuentan toda la historia</h3>
      <p>
        Prueba funciones y observa el error en las tres muestras. Las curvas
        entre muestras pueden ser distintas.
      </p>
      <p className="muted">
        Los coeficientes del ejercicio se limitan a [−10 000,10 000] para
        mantener cálculos legibles.
      </p>
      <div className="controls">
        <label>
          Candidata
          <select
            value={candidate}
            onChange={(e) => setCandidate(e.target.value)}
          >
            <option value="lineal">a·x + b</option>
            <option value="cuadratica">a·x² + b·x + c</option>
            <option value="alternativa">x² + a(x−1)(x−2)(x−3)</option>
          </select>
        </label>
        {[
          ["a", a, setA],
          ["b", b, setB],
          ["c", c, setC],
        ].map(([name, value, set]) => (
          <label key={String(name)}>
            {String(name)}
            <input
              type="number"
              step="0.1"
              value={value as number}
              onChange={(e) =>
                (set as (n: number) => void)(bounded(e.target.value))
              }
            />
          </label>
        ))}
        <button onClick={() => setShow(!show)}>
          {show ? "Ocultar" : "Mostrar"} función original
        </button>
      </div>
      <Plot
        series={[
          { name: "Datos observados", points, color: "#39FF88", dots: true },
          {
            name: "Candidata",
            points: grid.map((x) => ({ x, y: f(x) })),
            color: "#FFB84D",
          },
          ...(show
            ? [
                {
                  name: "Original x²",
                  points: grid.map((x) => ({ x, y: x * x })),
                  color: "#89BFFF",
                },
              ]
            : []),
        ]}
      />
      <div className="metric-inline">
        MSE de la candidata <strong>{fmt(error.mse)}</strong>
      </div>
    </>
  );
}
function Editor() {
  const [tree, setTree] = useState<Tree>(exampleTree),
    [selected, setSelected] = useState<Path>([]);
  const [value, setValue] = useState("x");
  function insert(v: string, p = selected) {
    const old = at(tree, p),
      arity = arities[v] ?? 0;
    setTree(
      replace(
        tree,
        p,
        arity
          ? node(
              v,
              ...Array.from(
                { length: arity },
                (_, i) => old.children[i] ?? terminal("x"),
              ),
            )
          : terminal(v === "x" ? "x" : Number(v)),
      ),
    );
    setSelected(p);
  }
  return (
    <>
      <h3>Construye una expresión</h3>
      <p>
        Selecciona un nodo y pulsa una pieza, o arrástrala hasta el nodo que
        quieres reemplazar. El editor conserva la aridad; si faltan argumentos
        crea hojas x.
      </p>
      <div className="palette">
        {[...Object.keys(arities), "x", "1", "2", "3"].map((v) => (
          <button
            draggable
            key={v}
            onDragStart={(e) => e.dataTransfer.setData("text/plain", v)}
            onClick={() => insert(v)}
          >
            {v}
            <small>{arities[v] ? ` ${arities[v]} args` : " hoja"}</small>
          </button>
        ))}
      </div>
      <div className="split">
        <TreeView
          tree={tree}
          selected={selected}
          onSelect={setSelected}
          onDrop={(p, v) => {
            if ([...Object.keys(arities), "x", "1", "2", "3"].includes(v))
              insert(v, p);
          }}
        />
        <div className="inset">
          <span className="badge">Estructura válida</span>
          <p className="mono">{expression(tree)}</p>
          <p>
            Tamaño <strong>{size(tree)}</strong> · altura{" "}
            <strong>{height(tree)}</strong>
          </p>
          <label className="field">
            Terminal personalizado
            <input value={value} onChange={(e) => setValue(e.target.value)} />
          </label>
          <button
            disabled={
              value !== "x" &&
              (!value.trim() || !Number.isFinite(Number(value)))
            }
            onClick={() => insert(value)}
          >
            Reemplazar nodo seleccionado
          </button>
          <button
            onClick={() => {
              setTree(exampleTree);
              setSelected([]);
            }}
          >
            Restaurar ejemplo
          </button>
          <p className="muted">
            La validez estructural no garantiza el dominio para todo x.
          </p>
        </div>
      </div>
    </>
  );
}
function Traversal() {
  const [order, setOrder] = useState<"pre" | "in" | "post">("post"),
    [step, setStep] = useState(-1),
    [playing, setPlaying] = useState(false),
    [x, setX] = useState(4);
  const seq = traversalPaths(simpleTree, order);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(
      () =>
        setStep((s) => {
          if (s >= seq.length - 1) {
            setPlaying(false);
            return s;
          }
          return s + 1;
        }),
      650,
    );
    return () => clearInterval(id);
  }, [playing, seq.length]);
  return (
    <>
      <h3>Sigue cada visita</h3>
      <div className="controls">
        {(["pre", "in", "post"] as const).map((v) => (
          <button
            key={v}
            className={v === order ? "active" : ""}
            onClick={() => {
              setOrder(v);
              setStep(-1);
              setPlaying(true);
            }}
          >
            {{ pre: "Preorder", in: "Inorder", post: "Postorder" }[v]}
          </button>
        ))}
        <button onClick={() => setPlaying(!playing)}>
          {playing ? "Pausar" : "Animar"}
        </button>
        <button
          onClick={() => {
            setPlaying(false);
            setStep((s) => (s + 1) % seq.length);
          }}
        >
          Siguiente nodo
        </button>
      </div>
      <TreeView
        tree={simpleTree}
        highlight={step >= 0 ? seq[step] : undefined}
      />
      <div className="tokens">
        {seq.map((p, i) => (
          <span key={pathKey(p)} className={i <= step ? "visited" : ""}>
            {String(at(simpleTree, p).value)}
          </span>
        ))}
      </div>
      <p className="muted">
        Inorder muestra tokens; la fórmula completa conserva paréntesis:{" "}
        {expression(simpleTree)}
      </p>
      <p className="muted">Este ejercicio admite x entre −10 000 y 10 000.</p>
      <label className="field narrow">
        Valor de x
        <input
          type="number"
          value={x}
          onChange={(e) => setX(bounded(e.target.value))}
        />
      </label>
      <h4>Evaluación en postorder</h4>
      <ol className="trace">
        {traversalPaths(simpleTree, "post").map((p) => (
          <li key={pathKey(p)}>
            <code>{expression(at(simpleTree, p))}</code>
            <span>= {fmt(evaluate(at(simpleTree, p), x))}</span>
          </li>
        ))}
      </ol>
    </>
  );
}
function Generator() {
  const [max, setMax] = useState(3),
    [full, setFull] = useState(false),
    [tree, setTree] = useState(() => randomTree(3));
  return (
    <>
      <h3>Una biblioteca, muchas estructuras</h3>
      <div className="controls">
        <label>
          Altura máxima
          <input
            type="number"
            min="0"
            max="5"
            value={max}
            onChange={(e) =>
              setMax(
                Math.max(0, Math.min(5, Math.floor(Number(e.target.value)))),
              )
            }
          />
        </label>
        <label>
          Método
          <select
            value={full ? "full" : "grow"}
            onChange={(e) => setFull(e.target.value === "full")}
          >
            <option value="grow">Grow: puede terminar antes</option>
            <option value="full">Full: expande hasta el límite</option>
          </select>
        </label>
        <button
          className="primary"
          onClick={() => setTree(randomTree(max, Math.random, full))}
        >
          Generar árbol
        </button>
      </div>
      <TreeView tree={tree} />
      <div className="metric-inline">
        Tamaño <strong>{size(tree)}</strong> Altura real{" "}
        <strong>{height(tree)}</strong> Máximo configurado{" "}
        <strong>{max}</strong>
      </div>
      <p className="muted">
        Los nodos verdes son operadores; los terminales tienen borde azul. En el
        nivel límite toda rama debe terminar en hoja. Cambiar el límite se
        aplica al generar.
      </p>
      <div className="operation-grid">
        {Object.entries(arities).map(([op, arity]) => (
          <div key={op}>
            <code>{op}</code>
            <span>
              {arity} argumento{arity > 1 ? "s" : ""}
            </span>
          </div>
        ))}
      </div>
      <p className="callout">
        /, %: divisor ≠0 · sqrt: argumento ≥0 · log: argumento &gt;0 · potencia:
        resultado real finito · tan: fuera de polos.
      </p>
    </>
  );
}
function MetricsTable() {
  const [rows, setRows] = useState([
    { x: 1, y: 1, p: 1 },
    { x: 2, y: 2, p: 1 },
    { x: 3, y: 3, p: 2 },
  ]);
  const m = metrics(
    rows.map((r) => r.y),
    rows.map((r) => r.p),
  );
  function edit(i: number, key: "x" | "y" | "p", value: number) {
    setRows(rows.map((r, j) => (i === j ? { ...r, [key]: value } : r)));
  }
  return (
    <>
      <h3>Del residuo a la métrica</h3>
      <p>
        Edita valores reales y predicciones. Aquí ŷ es una entrada libre para
        estudiar métricas; no se calcula a partir de x.
      </p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {["x", "y", "ŷ", "y−ŷ", "(y−ŷ)²", "y²", "y−ȳ", "(y−ȳ)²"].map(
                (t) => (
                  <th key={t}>{t}</th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {(["x", "y", "p"] as const).map((key) => (
                  <td key={key}>
                    <input
                      aria-label={`${key === "p" ? "predicción" : key} fila ${i + 1}`}
                      type="number"
                      value={r[key]}
                      onChange={(e) => edit(i, key, bounded(e.target.value))}
                    />
                  </td>
                ))}
                {[
                  r.y - r.p,
                  (r.y - r.p) ** 2,
                  r.y ** 2,
                  r.y - m.mean,
                  (r.y - m.mean) ** 2,
                ].map((v, j) => (
                  <td key={j}>{fmt(v)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="actions">
        <button
          onClick={() => setRows([...rows, { x: rows.length + 1, y: 0, p: 0 }])}
          disabled={rows.length >= 12}
        >
          Añadir fila
        </button>
        <button
          disabled={rows.length <= 1}
          onClick={() => setRows(rows.slice(0, -1))}
        >
          Quitar última
        </button>
        <span>
          ȳ = {fmt(m.mean)} · SSE = {fmt(m.sse)} · SST = {fmt(m.sst)}
        </span>
      </div>
      <div className="stat-grid">
        {[
          ["MSE", m.mse, "SSE / n"],
          ["NMSE", m.nmse, "SSE / Σy²"],
          ["R²", m.r2, "1 − SSE / SST"],
        ].map(([name, v, formula]) => (
          <div className="stat" key={String(name)}>
            <small>{String(name)}</small>
            <strong>{fmt(v as number | null)}</strong>
            <span>{String(formula)}</span>
          </div>
        ))}
      </div>
      <p className="callout">
        Denominador cero → no definido. MSE y NMSE pueden superar 1. R² puede
        ser negativo. Entradas limitadas a ±10 000.
      </p>
      <MetricExercise />
    </>
  );
}
function Selection() {
  const [errors, setErrors] = useState([0.2, 0.8, 1.5, 3]),
    [a, setA] = useState(0),
    [b, setB] = useState(1),
    [result, setResult] = useState(""),
    [rotation, setRotation] = useState(0);
  const p = weights(errors);
  let start = 0;
  const slices = p.map((prob, i) => {
    const s = start;
    start += prob * 360;
    return `${["#39FF88", "#89BFFF", "#FFB84D", "#C497FF"][i]} ${s}deg ${start}deg`;
  });
  function spin() {
    const v = Math.random();
    let acc = 0,
      index = 0;
    for (let i = 0; i < p.length; i++) {
      acc += p[i];
      if (v < acc) {
        index = i;
        break;
      }
    }
    setRotation((r) => r + 720 + v * 360);
    setResult(
      `Ruleta: elegido individuo ${index + 1} (p=${fmt(p[index])}). El sorteo usa la distribución acumulada.`,
    );
  }
  return (
    <>
      <h3>Menor error, mayor oportunidad</h3>
      <p className="muted">
        Población ilustrativa: los MSE son valores hipotéticos editables para
        estudiar la selección. Este panel no los calcula contra un CSV.
      </p>
      <div className="population">
        {[
          node("^", terminal("x"), terminal(2)),
          node("+", terminal("x"), terminal(1)),
          node("sin", terminal("x")),
          node("cos", terminal("x")),
        ].map((tree, i) => (
          <div className="individual" key={i}>
            <span>Árbol {i + 1}</span>
            <TreeView tree={tree} compact />
            <strong>MSE {fmt(errors[i])}</strong>
          </div>
        ))}
      </div>
      <div className="split">
        <div>
          {errors.map((v, i) => (
            <label className="prob-row" key={i}>
              <span>Árbol {i + 1}</span>
              <input
                aria-label={`MSE individuo ${i + 1}`}
                type="number"
                min="0"
                step="0.1"
                value={v}
                onChange={(e) =>
                  setErrors(
                    errors.map((a, j) =>
                      j === i ? Math.max(0, bounded(e.target.value)) : a,
                    ),
                  )
                }
              />
              <span>p={fmt(p[i] * 100)}%</span>
              <div className="bar">
                <i style={{ width: `${p[i] * 100}%` }} />
              </div>
            </label>
          ))}
        </div>
        <div className="wheel-wrap">
          <div
            className="wheel"
            style={{
              background: `conic-gradient(${slices.join(",")})`,
              transform: `rotate(${rotation}deg)`,
            }}
          >
            <span>SELECCIÓN</span>
          </div>
          <button className="primary" onClick={spin}>
            Sortear ruleta
          </button>
        </div>
      </div>
      <div className="controls">
        {[
          ["Participante A", a, setA],
          ["Participante B", b, setB],
        ].map(([name, value, set]) => (
          <label key={String(name)}>
            {String(name)}
            <select
              value={value as number}
              onChange={(e) =>
                (set as (n: number) => void)(Number(e.target.value))
              }
            >
              {errors.map((_, i) => (
                <option key={i} value={i}>
                  Árbol {i + 1}
                </option>
              ))}
            </select>
          </label>
        ))}
        <button
          onClick={() =>
            setResult(
              `Torneo: gana árbol ${
                tournament(
                  errors.map((error) => ({ error })),
                  a,
                  b,
                ) + 1
              }. Se compara el MSE y se prefiere el menor.`,
            )
          }
        >
          Ejecutar torneo
        </button>
        <button
          onClick={() =>
            setResult(
              `SUS (4 punteros): ${sus(p, 4)
                .map((i) => `árbol ${i + 1}`)
                .join(" → ")}. Un origen aleatorio, separación 1/4.`,
            )
          }
        >
          Muestrear SUS
        </button>
      </div>
      {result && (
        <p role="status" className="feedback success">
          {result}
        </p>
      )}
      <p className="muted">
        Los colores de la rueda corresponden a los individuos 1–4. La animación
        representa el sorteo; el resultado numérico se indica en el mensaje.
      </p>
    </>
  );
}
const parentA = node("+", node("*", terminal("x"), terminal(2)), terminal(3)),
  parentB = node(
    "-",
    node("sin", terminal("x")),
    node("+", terminal(4), terminal("x")),
  );
function Genetics() {
  const [pa, setPa] = useState<Path>([0]),
    [pb, setPb] = useState<Path>([1]),
    [children, setChildren] = useState<[Tree, Tree] | null>(null),
    [crossPhase, setCrossPhase] = useState(0),
    [mutation, setMutation] = useState<Tree>(parentA),
    [beforeMutation, setBeforeMutation] = useState<Tree>(parentA),
    [kind, setKind] = useState<Mutation>("terminal"),
    [pm, setPm] = useState(0.7),
    [ms, setMs] = useState([1, 1, 1, 1]),
    [message, setMessage] = useState(""),
    [limit, setLimit] = useState(2),
    [strategy, setStrategy] = useState("prune"),
    [fixed, setFixed] = useState<Tree | null>(null);
  const oversized = node(
    "+",
    clone(parentB),
    node("*", clone(parentA), clone(parentB)),
  );
  useEffect(() => {
    if (crossPhase < 1 || crossPhase >= 3) return;
    const timer = setTimeout(() => setCrossPhase((p) => p + 1), 650);
    return () => clearTimeout(timer);
  }, [crossPhase]);
  function cross(auto = false) {
    const a = auto ? pick(paths(parentA).slice(1), Math.random) : pa,
      b = auto ? pick(paths(parentB).slice(1), Math.random) : pb;
    setPa(a);
    setPb(b);
    setChildren(crossover(parentA, parentB, a, b));
    setCrossPhase(1);
  }
  function canMutate(type: Mutation) {
    return (
      (type !== "operator" && type !== "switch") ||
      paths(mutation).some((p) =>
        type === "operator"
          ? at(mutation, p).children.length > 0
          : at(mutation, p).children.length === 2,
      )
    );
  }
  function roulette() {
    if (Math.random() >= pm) {
      setMessage("No ocurrió mutación: el sorteo no cayó dentro de Pm.");
      return;
    }
    const sum = ms.reduce((a, b) => a + b, 0);
    let v = Math.random() * sum,
      index = 0;
    for (let i = 0; i < 4; i++) {
      v -= ms[i];
      if (v < 0) {
        index = i;
        break;
      }
    }
    const type = (["terminal", "operator", "switch", "branch"] as const)[index];
    setKind(type);
    if (!canMutate(type)) {
      setMessage(
        `Se sorteó mutación de tipo ${type}, pero no hay un nodo elegible. La propuesta conserva el árbol.`,
      );
      return;
    }
    setBeforeMutation(mutation);
    setMutation(mutate(mutation, type));
    setMessage(
      `Sí ocurrió mutación. Tipo seleccionado: ${type}. Probabilidad conjunta: ${fmt((pm * ms[index]) / sum)}.`,
    );
  }
  function fix() {
    if (strategy === "prune") {
      setFixed(repair(oversized, limit));
      setMessage(
        "Estrategia: poda. Los nodos internos en el nivel límite se reemplazan por x.",
      );
      return;
    }
    const rng = seeded(Date.now());
    for (let i = 1; i <= 20; i++) {
      const t = mutate(parentA, "branch", rng);
      if (height(t) <= limit) {
        setFixed(t);
        setMessage(
          `Rechazo y repetición: propuesta válida en intento ${i} de 20.`,
        );
        return;
      }
    }
    setFixed(repair(parentA, limit));
    setMessage(
      "No hubo propuesta válida en 20 intentos. Se conserva un padre ajustado previamente al límite.",
    );
  }
  return (
    <>
      <h3>Dos padres. Nuevas expresiones.</h3>
      <p>
        Pulsa un nodo distinto de la raíz para seleccionar la arista que llega a
        él. Las ramas seleccionadas se intercambiarán.
      </p>
      <div className="split">
        <div className="inset">
          <h4>Padre 1</h4>
          <TreeView
            tree={parentA}
            selected={pa}
            onSelect={(p) => {
              if (p.length) {
                setPa(p);
                setCrossPhase(0);
                setChildren(null);
              }
            }}
          />
          <code>{expression(at(parentA, pa))}</code>
        </div>
        <div className="inset">
          <h4>Padre 2</h4>
          <TreeView
            tree={parentB}
            selected={pb}
            onSelect={(p) => {
              if (p.length) {
                setPb(p);
                setCrossPhase(0);
                setChildren(null);
              }
            }}
          />
          <code>{expression(at(parentB, pb))}</code>
        </div>
      </div>
      <div className="actions">
        <button
          className="primary"
          disabled={crossPhase === 1 || crossPhase === 2}
          onClick={() => cross()}
        >
          Cruzar ramas seleccionadas
        </button>
        <button
          disabled={crossPhase === 1 || crossPhase === 2}
          onClick={() => cross(true)}
        >
          Cruce aleatorio
        </button>
      </div>
      {crossPhase > 0 && (
        <div className="cross-animation" aria-live="polite">
          <p className="feedback success">
            {crossPhase === 1
              ? "1. Cortamos las aristas seleccionadas: cada rama se separa de su padre."
              : crossPhase === 2
                ? "2. Intercambiamos los subárboles; cada contexto recibe la rama del otro padre."
                : "3. Reconectamos las ramas: dos hijos nuevos, padres intactos."}
          </p>
          {crossPhase < 3 && (
            <>
              <div
                className={
                  "split detached " + (crossPhase === 2 ? "swapping" : "")
                }
              >
                <div className="inset branch-a">
                  <h4>Rama del padre 1 → hijo 2</h4>
                  <TreeView tree={at(parentA, pa)} compact />
                </div>
                <div className="inset branch-b">
                  <h4>Rama del padre 2 → hijo 1</h4>
                  <TreeView tree={at(parentB, pb)} compact />
                </div>
              </div>
              <button onClick={() => setCrossPhase(3)}>Ver hijos ahora</button>
            </>
          )}
        </div>
      )}
      {children && crossPhase === 3 && (
        <div className="split animate-in" key={expression(children[0])}>
          {children.map((t, i) => (
            <div className="inset" key={i}>
              <h4>Hijo {i + 1}</h4>
              <TreeView tree={t} selected={i === 0 ? pa : pb} />
              <code>{expression(t)}</code>
            </div>
          ))}
        </div>
      )}
      <hr />
      <h3>Cuatro maneras de mutar</h3>
      <div className="controls">
        {(["terminal", "operator", "switch", "branch"] as const).map(
          (type, i) => (
            <button
              key={type}
              className={kind === type ? "active" : ""}
              onClick={() => {
                setKind(type);
                if (!canMutate(type)) {
                  setMessage(
                    type === "operator"
                      ? "No hay nodos operadores para sustituir; el árbol se conserva."
                      : "No hay nodos binarios para intercambiar hijos; el árbol se conserva.",
                  );
                  return;
                }
                setBeforeMutation(mutation);
                setMutation(mutate(mutation, type));
                setMessage(
                  [
                    "Cambio de hoja.",
                    "Operador nuevo de igual aridad.",
                    "Hijos intercambiados. Con operadores conmutativos el valor puede conservarse.",
                    "Rama sustituida por estructura nueva.",
                  ][i],
                );
              }}
            >
              {
                [
                  "1 · Terminal",
                  "2 · Operador",
                  "3 · Switching",
                  "4 · Regenerar rama",
                ][i]
              }
            </button>
          ),
        )}
        <button
          onClick={() => {
            setMutation(parentA);
            setBeforeMutation(parentA);
          }}
        >
          Restaurar
        </button>
        <button
          disabled={mutation.children.length !== 2}
          title="Requiere una raíz binaria para demostrar el cambio 2 → 1"
          onClick={() => {
            setKind("operator");
            setBeforeMutation(mutation);
            setMutation(node("sin", clone(mutation.children[0] ?? mutation)));
            setMessage(
              "Cambio explícito a aridad 1: se conserva el hijo izquierdo y se elimina el derecho.",
            );
          }}
        >
          Cambiar raíz a sin (unario)
        </button>
      </div>
      <div className="split">
        <div className="inset">
          <h4>Antes de la mutación</h4>
          <TreeView tree={beforeMutation} />
          <code>{expression(beforeMutation)}</code>
        </div>
        <div className="inset animate-in" key={expression(mutation)}>
          <h4>Después: {kind}</h4>
          <TreeView tree={mutation} />
          <code>{expression(mutation)}</code>
        </div>
      </div>
      <p className="mono">{expression(mutation)}</p>
      <div className="controls">
        <label>
          Pm
          <input
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
        {ms.map((w, i) => (
          <label key={i}>
            Peso tipo {i + 1}
            <input
              type="number"
              min="0"
              max="100"
              value={w}
              onChange={(e) =>
                setMs(
                  ms.map((v, j) =>
                    j === i
                      ? Math.max(0, Math.min(100, Number(e.target.value)))
                      : v,
                  ),
                )
              }
            />
          </label>
        ))}
        <button disabled={!ms.some(Boolean)} onClick={roulette}>
          Sortear Pm y tipo
        </button>
      </div>
      <MutationWheel weights={ms} selected={kind} />
      <p className="muted">
        La ruleta condicional tiene probabilidades{" "}
        {ms
          .map((w) => fmt(w / (ms.reduce((a, b) => a + b, 0) || 1)))
          .join(" / ")}
        . Primero se sortea Pm.
      </p>
      <hr />
      <h3>Repara una propuesta demasiado alta</h3>
      <div className="controls">
        <label>
          Altura permitida
          <input
            type="number"
            min="1"
            max="3"
            value={limit}
            onChange={(e) => {
              setLimit(
                Math.max(1, Math.min(3, Math.floor(Number(e.target.value)))),
              );
              setFixed(null);
            }}
          />
        </label>
        <label>
          Estrategia
          <select
            value={strategy}
            onChange={(e) => {
              setStrategy(e.target.value);
              setFixed(null);
            }}
          >
            <option value="prune">Podar ramas excedentes</option>
            <option value="reject">Rechazar y repetir (máx. 20)</option>
          </select>
        </label>
        <button onClick={fix}>Aplicar estrategia</button>
      </div>
      <div className="split">
        <div>
          <h4>Propuesta: altura {height(oversized)}</h4>
          <TreeView tree={oversized} />
        </div>
        {fixed && (
          <div>
            <h4>Resultado: altura {height(fixed)}</h4>
            <TreeView tree={fixed} />
          </div>
        )}
      </div>
      {message && (
        <p className="feedback success" role="status">
          {message}
        </p>
      )}
    </>
  );
}
