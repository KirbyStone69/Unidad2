import {
  render,
  screen,
  fireEvent,
  cleanup,
  act,
} from "@testing-library/react";
import { afterEach, it, expect, vi } from "vitest";
import { Activities } from "../src/features/Activities";
import { Plot } from "../src/components/Plot";
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});
it("explica el corte, intercambio y resultado durante el cruce animado", () => {
  vi.useFakeTimers();
  render(<Activities unit={7} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Cruzar ramas seleccionadas" }),
  );
  expect(screen.getByText(/1. Cortamos las aristas/)).toBeInTheDocument();
  act(() => vi.advanceTimersByTime(700));
  expect(screen.getByText(/2. Intercambiamos/)).toBeInTheDocument();
  act(() => vi.advanceTimersByTime(700));
  expect(screen.getByRole("heading", { name: "Hijo 1" })).toBeInTheDocument();
});
it("normaliza valores extremos antes de generar coordenadas SVG", () => {
  const { container } = render(
    <Plot
      series={[
        {
          name: "Extremos",
          points: [
            { x: -1e308, y: -1e308 },
            { x: 1e308, y: 1e308 },
          ],
          color: "#fff",
        },
      ]}
    />,
  );
  expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
});
