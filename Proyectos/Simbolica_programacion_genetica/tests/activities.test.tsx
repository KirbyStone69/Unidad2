import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { afterEach, it, expect, vi } from "vitest";
import { Activities } from "../src/features/Activities";
import { randomTree, repair, height } from "../src/domain/tree";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
it("limita entradas extremas de las gráficas sin desmontar el curso", () => {
  render(<Activities unit={1} />);
  fireEvent.change(screen.getByLabelText("a"), { target: { value: "1e308" } });
  expect(screen.getByLabelText("a")).toHaveValue(10000);
  expect(
    screen.getByText("Los puntos no cuentan toda la historia"),
  ).toBeInTheDocument();
});
it("limita entradas extremas de la evaluación sin lanzar", () => {
  render(<Activities unit={3} />);
  fireEvent.change(screen.getByLabelText("Valor de x"), {
    target: { value: "1e308" },
  });
  expect(screen.getByLabelText("Valor de x")).toHaveValue(10000);
});
it("normaliza altura fraccionaria hacia abajo", () => {
  expect(height(randomTree(1.5, () => 0.9, true))).toBeLessThanOrEqual(1);
  expect(
    height(
      repair(
        randomTree(3, () => 0.9, true),
        1.5,
      ),
    ),
  ).toBeLessThanOrEqual(1);
});
it("explica cuando una mutación de operador no tiene nodo elegible", () => {
  vi.spyOn(Math, "random").mockReturnValue(0);
  render(<Activities unit={7} />);
  fireEvent.click(screen.getByRole("button", { name: "4 · Regenerar rama" }));
  fireEvent.click(screen.getByRole("button", { name: "2 · Operador" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "No hay nodos operadores",
  );
  expect(
    screen.getByRole("button", { name: "Cambiar raíz a sin (unario)" }),
  ).toBeDisabled();
  vi.restoreAllMocks();
});
