import { type Tree, type Path, height, size, label } from "../domain/tree";
export const pathKey = (p: Path) => p.join(".") || "root";
interface Props {
  tree: Tree;
  selected?: Path;
  highlight?: Path;
  onSelect?: (p: Path) => void;
  onDrop?: (p: Path, value: string) => void;
  compact?: boolean;
  title?: string;
}
export function TreeView({
  tree,
  selected,
  highlight,
  onSelect,
  onDrop,
  compact,
  title = "Árbol de expresión",
}: Props) {
  const nodes: { t: Tree; p: Path; x: number; y: number }[] = [];
  const edges: { a: number; b: number; c: number; d: number }[] = [];
  let leaf = 0;
  function layout(t: Tree, p: Path = [], level = 0): number {
    const xs = t.children.map((c, i) => layout(c, [...p, i], level + 1));
    const x = xs.length
      ? xs.reduce((a, b) => a + b, 0) / xs.length
      : leaf++ * 76 + 45;
    const y = level * 74 + 35;
    nodes.push({ t, p, x, y });
    t.children.forEach((_, i) =>
      edges.push({ a: x, b: y, c: xs[i], d: y + 74 }),
    );
    return x;
  }
  layout(tree);
  const w = Math.max(leaf * 76 + 15, 200),
    h = (height(tree) + 1) * 74;
  return (
    <div className={"tree-wrap " + (compact ? "compact" : "")}>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        style={{ minWidth: compact ? 160 : w, flexShrink: 0 }}
        aria-label={title}
        role={onSelect ? "group" : "img"}
      >
        <title>
          {title}; {size(tree)} nodos; altura {height(tree)}
        </title>
        {edges.map((e, i) => (
          <path
            key={i}
            d={`M${e.a},${e.b + 19} C${e.a},${e.b + 43} ${e.c},${e.d - 43} ${e.c},${e.d - 19}`}
            className="tree-edge"
          />
        ))}
        {nodes.map(({ t, p, x, y }) => {
          const branch = selected && selected.every((v, i) => p[i] === v),
            active = selected && pathKey(selected) === pathKey(p),
            lit = highlight && pathKey(highlight) === pathKey(p);
          return (
            <g
              key={pathKey(p)}
              transform={`translate(${x},${y})`}
              className={`tree-node ${t.children.length ? "operator" : "terminal"} ${active ? "selected" : ""} ${branch ? "selected-branch" : ""} ${lit ? "lit" : ""}`}
              role={onSelect ? "button" : undefined}
              tabIndex={onSelect ? 0 : undefined}
              aria-label={`${label(t)}, nivel ${p.length}${active ? ", seleccionado" : ""}`}
              onClick={() => onSelect?.(p)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect?.(p);
                }
              }}
              onDragOver={(e) => {
                if (onDrop) e.preventDefault();
              }}
              onDrop={(e) => {
                e.preventDefault();
                onDrop?.(p, e.dataTransfer.getData("text/plain"));
              }}
            >
              <circle r="22" />
              <text textAnchor="middle" dy="5">
                {label(t)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
