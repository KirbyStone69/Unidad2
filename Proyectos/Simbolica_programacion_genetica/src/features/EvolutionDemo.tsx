import { useEffect, useState } from "react";
import { TreeView } from "../components/TreeView";
import { Plot } from "../components/Plot";
import {
  type Tree,
  clone,
  crossover,
  paths,
  pick,
  mutate,
  repair,
  expression,
  height,
} from "../domain/tree";
import {
  type Individual,
  initialPopulation,
  score,
  tournament,
} from "../domain/evolution";
import { fmt } from "../domain/metrics";
const data = Array.from({ length: 9 }, (_, i) => ({
  x: i / 4,
  y: (i / 4) ** 2 + 1,
}));
const config = { maxHeight: 3, mutationRate: 0.5, elite: 1 };
const stages = [
  "Evaluar población",
  "Seleccionar padres",
  "Cruzar subárboles",
  "Sortear y aplicar mutación",
  "Reparar altura",
  "Evaluar descendientes",
  "Conservar élite y reemplazar",
];
interface Demo {
  pop: Individual[];
  generation: number;
  stage: number;
  parents: Tree[];
  children: Tree[];
  trace: string;
  history: { x: number; y: number }[];
  means: { x: number; y: number }[];
}
function fresh(): Demo {
  const pop = initialPopulation(8, data, config);
  return {
    pop,
    generation: 0,
    stage: 0,
    parents: [],
    children: [],
    trace:
      "Se generaron ocho árboles. Ahora evaluamos en y=x²+1 para nueve puntos.",
    history: [{ x: 0, y: pop[0].error }],
    means: [{ x: 0, y: mean(pop) }],
  };
}
function mean(pop: Individual[]) {
  const valid = pop.filter((i) => Number.isFinite(i.error));
  return valid.length
    ? valid.reduce((s, i) => s + i.error, 0) / valid.length
    : NaN;
}
function advance(d: Demo): Demo {
  const s = { ...d };
  switch (d.stage) {
    case 0:
      s.pop = d.pop
        .map((i) => ({ ...i, error: score(i.tree, data) }))
        .sort((a, b) => a.error - b.error);
      s.trace =
        "Cada árbol se evaluó en las mismas nueve muestras. El error no finito se penaliza.";
      break;
    case 1: {
      const parents = Array.from({ length: 8 }, () => {
        const a = Math.floor(Math.random() * 8),
          b = Math.floor(Math.random() * 8);
        return clone(d.pop[tournament(d.pop, a, b)].tree);
      });
      s.parents = parents;
      s.trace =
        "Ocho torneos binarios eligieron padres. Gana el menor MSE de cada pareja.";
      break;
    }
    case 2: {
      const out: Tree[] = [];
      for (let i = 0; i < 8; i += 2) {
        const a = d.parents[i],
          b = d.parents[i + 1],
          pa = paths(a).slice(1),
          pb = paths(b).slice(1);
        out.push(
          ...(pa.length && pb.length
            ? crossover(a, b, pick(pa, Math.random), pick(pb, Math.random))
            : [clone(a), clone(b)]),
        );
      }
      s.children = out;
      s.trace =
        "Se intercambiaron ramas por aristas. Padres sin aristas se copiaron; el cruce puede exceder altura.";
      break;
    }
    case 3: {
      let count = 0;
      s.children = d.children.map((t) => {
        if (Math.random() < config.mutationRate) {
          count++;
          return mutate(
            t,
            pick(
              ["terminal", "operator", "switch", "branch"] as const,
              Math.random,
            ),
          );
        }
        return t;
      });
      s.trace = `Se sorteó Pm=0.5 para cada hijo: ${count} propuestas de mutación. Después se eligió tipo con pesos iguales.`;
      break;
    }
    case 4: {
      const count = d.children.filter((t) => height(t) > 3).length;
      s.children = d.children.map((t) => repair(t, 3));
      s.trace = `Poda aplicada a ${count} árboles por encima de altura 3. En el nivel límite se sustituyen operaciones por x.`;
      break;
    }
    case 5:
      s.trace = `MSE de hijos: ${d.children.map((t) => fmt(score(t, data))).join(" · ")}. Ahora se pueden comparar con los padres.`;
      break;
    case 6: {
      const elite = [...d.pop].sort((a, b) => a.error - b.error)[0];
      const children = d.children
        .slice(0, 7)
        .map((tree) => ({ tree, error: score(tree, data) }));
      s.pop = [
        { tree: clone(elite.tree), error: elite.error },
        ...children,
      ].sort((a, b) => a.error - b.error);
      if (s.pop.every((i) => !Number.isFinite(i.error)))
        s.pop = initialPopulation(8, data, config);
      s.generation = d.generation + 1;
      s.history = [...d.history, { x: s.generation, y: s.pop[0].error }];
      s.means = [...d.means, { x: s.generation, y: mean(s.pop) }];
      s.trace =
        "Una copia del mejor padre y siete hijos forman exactamente ocho individuos. El archivo guarda los mejores por generación.";
      break;
    }
  }
  s.stage = (d.stage + 1) % stages.length;
  return s;
}
export function EvolutionDemo() {
  const [d, setD] = useState(fresh),
    [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(
      () =>
        setD((s) => (s.generation >= 40 ? (setPlaying(false), s) : advance(s))),
      850,
    );
    return () => clearInterval(id);
  }, [playing]);
  return (
    <>
      <h3>Observa una generación por dentro</h3>
      <p>
        Objetivo de esta demostración real: y=x²+1 en nueve puntos. Ocho
        individuos, altura máxima 3, Pm=0.5 y una élite.
      </p>
      <div className="controls">
        <button className="primary" onClick={() => setD(advance)}>
          Siguiente operación
        </button>
        <button
          onClick={() =>
            setD((s) => {
              let next = s;
              const target = s.generation + 1;
              while (next.generation < target) next = advance(next);
              return next;
            })
          }
        >
          Siguiente generación
        </button>
        <button onClick={() => setPlaying(!playing)}>
          {playing ? "Pausar" : "Reproducir"}
        </button>
        <button
          onClick={() => {
            setPlaying(false);
            setD(fresh());
          }}
        >
          Reiniciar
        </button>
      </div>
      <div className="cycle-steps">
        {stages.map((s, i) => (
          <span className={i === d.stage ? "current" : ""} key={s}>
            {i + 1}. {s}
          </span>
        ))}
      </div>
      <p className="feedback success" role="status">
        Generación {d.generation} · {d.trace}
      </p>
      <div className="population">
        {d.pop.map((i, k) => (
          <div className="individual" key={k}>
            <span>
              #{k + 1}
              {k === 0 ? " · mejor" : ""}
            </span>
            <code>{expression(i.tree)}</code>
            <strong>MSE {fmt(i.error)}</strong>
          </div>
        ))}
      </div>
      {d.children.length > 0 && d.stage >= 3 && (
        <div>
          <h4>Dos descendientes de esta operación</h4>
          <div className="split">
            {d.children.slice(0, 2).map((t, i) => (
              <TreeView tree={t} compact key={i} />
            ))}
          </div>
        </div>
      )}
      <Plot
        xLabel="generación"
        yLabel="MSE"
        series={[
          {
            name: "Mejor MSE poblacional",
            points: d.history.filter((p) => Number.isFinite(p.y)),
            color: "#39FF88",
          },
          {
            name: "Promedio finito",
            points: d.means.filter((p) => Number.isFinite(p.y)),
            color: "#FFB84D",
          },
        ]}
      />
      <p className="muted">
        Promedio calculado solo sobre individuos finitos; los inválidos se
        muestran como tales. La reproducción se pausa al llegar a 40
        generaciones; puedes seguir manualmente.
      </p>
    </>
  );
}
