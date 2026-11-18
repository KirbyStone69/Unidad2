import type { Point } from "./evolution";
export const referenceData = (): Point[] =>
  Array.from({ length: 1000 }, (_, i) => {
    const x = i / 999;
    return { x, y: 6.67 + 11 * Math.cos(7.23 * x ** 3) };
  });
export function parseCSV(text: string): { points: Point[]; errors: string[] } {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/),
    points: Point[] = [],
    errors: string[] = [];
  if (lines.length > 50002)
    return {
      points: [],
      errors: ["Máximo 50 000 filas para mantener el laboratorio receptivo."],
    };
  const first = lines.find((l) => l.trim()) ?? "",
    delimiter = first.includes(";") ? ";" : ",";
  let firstContent = true;
  lines.forEach((line, index) => {
    if (!line.trim()) return;
    const cells: string[] = [];
    let cell = "",
      quoted = false,
      closed = false,
      malformed = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (quoted && line[i + 1] === '"') {
          cell += '"';
          i++;
        } else if (quoted) {
          quoted = false;
          closed = true;
        } else if (!cell.trim() && !closed) {
          quoted = true;
        } else malformed = true;
      } else if (c === delimiter && !quoted) {
        cells.push(cell.trim());
        cell = "";
        closed = false;
      } else {
        if (closed && c.trim()) malformed = true;
        cell += c;
      }
    }
    cells.push(cell.trim());
    if (
      !malformed &&
      !quoted &&
      firstContent &&
      cells.length === 2 &&
      cells[0].toLowerCase() === "x" &&
      cells[1].toLowerCase() === "y"
    ) {
      firstContent = false;
      return;
    }
    firstContent = false;
    if (
      malformed ||
      quoted ||
      cells.length !== 2 ||
      cells.some((c) => !c || !Number.isFinite(Number(c)))
    )
      errors.push(`Línea ${index + 1}: se esperan dos números finitos x,y.`);
    else points.push({ x: Number(cells[0]), y: Number(cells[1]) });
  });
  if (!points.length) errors.push("No hay puntos válidos.");
  return { points, errors };
}
