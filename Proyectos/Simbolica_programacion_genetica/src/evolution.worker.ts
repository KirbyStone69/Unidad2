import { seeded } from "./domain/tree";
import {
  initialPopulation,
  nextGeneration,
  type Individual,
  type Point,
  type Config,
} from "./domain/evolution";
interface Start {
  type: "start";
  data: Point[];
  config: Config;
  seed: number;
  population: number;
  generations: number;
}
let population: Individual[] = [],
  data: Point[] = [],
  config: Config = { maxHeight: 4, mutationRate: 0.3, elite: 1 },
  rng = seeded(1),
  generation = 0,
  limit = 60,
  playing = false,
  timer: ReturnType<typeof setTimeout> | undefined;
function send() {
  const valid = population.filter((i) => Number.isFinite(i.error));
  self.postMessage({
    type: "state",
    population,
    generation,
    mean: valid.length
      ? valid.reduce((s, i) => s + i.error, 0) / valid.length
      : null,
    invalid: population.length - valid.length,
    done: generation >= limit,
  });
}
function step() {
  if (generation >= limit) {
    playing = false;
    send();
    return;
  }
  population = nextGeneration(population, data, config, rng);
  generation++;
  send();
  if (playing && generation < limit) timer = setTimeout(step, 40);
}
self.onmessage = (
  event: MessageEvent<Start | { type: "pause" | "resume" | "step" }>,
) => {
  try {
    const m = event.data;
    if (m.type === "start") {
      clearTimeout(timer);
      data = m.data;
      config = m.config;
      rng = seeded(m.seed);
      generation = 0;
      limit = m.generations;
      population = initialPopulation(m.population, data, config, rng);
      playing = true;
      send();
      timer = setTimeout(step, 40);
    } else if (m.type === "pause") {
      playing = false;
      clearTimeout(timer);
    } else if (m.type === "resume") {
      if (!playing) {
        playing = true;
        step();
      }
    } else {
      playing = false;
      clearTimeout(timer);
      step();
    }
  } catch (e) {
    playing = false;
    self.postMessage({
      type: "error",
      message: e instanceof Error ? e.message : "Error del motor",
    });
  }
};
