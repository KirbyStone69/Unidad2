import type { Mutation } from "../domain/tree";
export function MutationWheel({
  weights,
  selected,
}: {
  weights: number[];
  selected: Mutation;
}) {
  const total = weights.reduce((a, b) => a + b, 0);
  let angle = 0;
  const colors = ["#39FF88", "#89BFFF", "#FFB84D", "#C497FF"],
    labels = ["Terminal", "Operador", "Switching", "Regenerar"],
    types = ["terminal", "operator", "switch", "branch"];
  const slices = weights.map((w, i) => {
    const start = angle;
    angle += total ? (w / total) * 360 : 0;
    return `${colors[i]} ${start}deg ${angle}deg`;
  });
  return (
    <div className="mutation-wheel">
      <div
        className="wheel"
        style={{
          background: total ? `conic-gradient(${slices.join(",")})` : "#294533",
        }}
        role="img"
        aria-label="Ruleta condicional de los cuatro tipos de mutación"
      >
        <span>TIPO DE MUTACIÓN</span>
      </div>
      <div>
        {labels.map((label, i) => (
          <div
            className={"wheel-label " + (types[i] === selected ? "accent" : "")}
            key={label}
          >
            <i style={{ background: colors[i] }} />
            {label}
            <strong>
              {total
                ? ((100 * weights[i]) / total).toFixed(1) + "%"
                : "Sin peso"}
            </strong>
          </div>
        ))}
        <p className="muted">
          Pesos normalizados después de que el sorteo de Pm determine que sí
          habrá mutación.
        </p>
      </div>
    </div>
  );
}
