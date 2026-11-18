import type { Point } from "../domain/evolution";
interface Series {
  name: string;
  points: Point[];
  color: string;
  dots?: boolean;
}
export function Plot({
  series,
  height = 240,
  xLabel = "x",
  yLabel = "y",
}: {
  series: Series[];
  height?: number;
  xLabel?: string;
  yLabel?: string;
}) {
  const all = series
    .flatMap((s) => s.points)
    .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
  if (!all.length)
    return (
      <div className="empty-chart">Sin valores finitos para graficar.</div>
    );
  const extent = all.reduce(
    (e, p) => ({
      minX: Math.min(e.minX, p.x),
      maxX: Math.max(e.maxX, p.x),
      minY: Math.min(e.minY, p.y),
      maxY: Math.max(e.maxY, p.y),
    }),
    { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity },
  );
  const normalizeScale = (min: number, max: number) => {
    const magnitude = Math.max(Math.abs(min), Math.abs(max));
    return magnitude > 1e100 || (magnitude > 0 && magnitude < 1e-100)
      ? magnitude
      : 1;
  };
  const scaleX = normalizeScale(extent.minX, extent.maxX),
    scaleY = normalizeScale(extent.minY, extent.maxY);
  let minX = extent.minX / scaleX,
    maxX = extent.maxX / scaleX,
    minY = extent.minY / scaleY,
    maxY = extent.maxY / scaleY;
  if (minX === maxX) {
    minX -= 1;
    maxX += 1;
  }
  if (minY === maxY) {
    minY -= 1;
    maxY += 1;
  }
  const margin = (maxY - minY) * 0.12;
  minY -= margin;
  maxY += margin;
  const scaledX = (x: number) => 55 + ((x - minX) / (maxX - minX)) * 620;
  const scaledY = (y: number) =>
    height - 35 - ((y - minY) / (maxY - minY)) * (height - 60);
  const X = (x: number) => scaledX(x / scaleX),
    Y = (y: number) => scaledY(y / scaleY);
  return (
    <div className="plot">
      <svg
        role="img"
        aria-label={series.map((s) => s.name).join(" y ")}
        viewBox={`0 0 700 ${height}`}
      >
        <title>{series.map((s) => s.name).join(" frente a ")}</title>
        {Array.from({ length: 5 }, (_, i) => {
          const y = minY + ((maxY - minY) * i) / 4;
          return (
            <g key={i}>
              <line
                x1="55"
                x2="675"
                y1={scaledY(y)}
                y2={scaledY(y)}
                className="chart-grid"
              />
              <text
                x="45"
                y={scaledY(y) + 4}
                textAnchor="end"
                className="chart-label"
              >
                {Number(y.toPrecision(3))}
              </text>
              <text
                x={55 + i * 155}
                y={height - 12}
                textAnchor="middle"
                className="chart-label"
              >
                {Number((minX + ((maxX - minX) * i) / 4).toPrecision(3))}
              </text>
            </g>
          );
        })}
        {series.map((s) => {
          const sampled = s.points
            .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y))
            .filter(
              (_, i) =>
                i % Math.max(1, Math.floor(s.points.length / 400)) === 0 ||
                i === s.points.length - 1,
            );
          return (
            <g key={s.name}>
              {s.dots ? (
                sampled.map(
                  (p, i) =>
                    Number.isFinite(p.y) && (
                      <circle
                        key={i}
                        cx={X(p.x)}
                        cy={Y(p.y)}
                        r={s.points.length > 30 ? 1.6 : 4}
                        fill={s.color}
                      />
                    ),
                )
              ) : (
                <path
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2.3"
                  d={sampled
                    .map((p, i) => `${i ? "L" : "M"}${X(p.x)},${Y(p.y)}`)
                    .join(" ")}
                />
              )}
            </g>
          );
        })}
        <text x="680" y={height - 12} className="chart-label">
          {xLabel}
        </text>
        <text x="15" y="14" className="chart-label">
          {yLabel}
        </text>
      </svg>
      {(scaleX !== 1 || scaleY !== 1) && (
        <p className="muted">
          Ejes normalizados para evitar desbordamiento: x /{" "}
          {scaleX.toExponential(2)}, y / {scaleY.toExponential(2)}.
        </p>
      )}
      <div className="legend">
        {series.map((s) => (
          <span key={s.name}>
            <i style={{ background: s.color }} />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}
