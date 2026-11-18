export interface Metrics {
  mean: number;
  sse: number;
  mse: number;
  nmse: number | null;
  r2: number | null;
  sst: number;
  energy: number;
}
export function metrics(y: number[], pred: number[]): Metrics {
  if (
    !y.length ||
    y.length !== pred.length ||
    [...y, ...pred].some((v) => !Number.isFinite(v))
  )
    throw new Error(
      "Se requieren vectores finitos del mismo tamaño, no vacíos.",
    );
  const constant = y.every((v) => v === y[0]);
  const mean = constant ? y[0] : y.reduce((s, v) => s + v / y.length, 0);
  const sse = y.reduce((s, v, i) => s + (v - pred[i]) ** 2, 0),
    sst = y.reduce((s, v) => s + (v - mean) ** 2, 0),
    energy = y.reduce((s, v) => s + v * v, 0);
  if (!Number.isFinite(sse) || !Number.isFinite(mean))
    throw new Error(
      "El cálculo excede el rango numérico. Reduce la escala de los datos.",
    );
  const energyScale = y.reduce((m, v) => Math.max(m, Math.abs(v)), 0),
    centerScale = y.reduce((m, v) => Math.max(m, Math.abs(v - mean)), 0);
  const energyNorm = energyScale
    ? y.reduce((s, v) => s + (v / energyScale) ** 2, 0)
    : 0;
  const centerNorm = centerScale
    ? y.reduce((s, v) => s + ((v - mean) / centerScale) ** 2, 0)
    : 0;
  return {
    mean,
    sse,
    mse: sse / y.length,
    nmse:
      energyScale === 0 ? null : sse / energyScale / energyScale / energyNorm,
    r2:
      centerScale === 0
        ? null
        : 1 - sse / centerScale / centerScale / centerNorm,
    sst,
    energy,
  };
}
export const fmt = (n: number | null, digits = 4) =>
  n === null
    ? "No definido"
    : !Number.isFinite(n)
      ? "Inválido"
      : Number(n.toPrecision(digits)).toLocaleString("es-MX", {
          maximumFractionDigits: 6,
        });
