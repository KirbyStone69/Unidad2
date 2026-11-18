import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { afterEach, beforeEach, it, expect } from "vitest";
import App from "../src/App";
afterEach(cleanup);
beforeEach(() => localStorage.clear());
it("permite estudiar, responder y entregar sin completar unidades de forma ficticia", () => {
  render(<App />);
  fireEvent.click(
    screen.getByRole("button", { name: /Continuar aprendizaje/i }),
  );
  expect(screen.getByText("Buscar sin recorrerlo todo")).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: /Evaluación de la unidad/i }),
  );
  expect(screen.getByText(/7 preguntas/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Entregar evaluación" }));
  expect(screen.getByText("0%")).toBeInTheDocument();
  expect(screen.getByText(/Corrección completa/i)).toBeInTheDocument();
});
it("no muestra correcciones antes de entregar un examen y conserva respuestas", () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Examen final" }));
  fireEvent.click(screen.getByRole("button", { name: "Comenzar simulacro" }));
  expect(screen.queryByText("Corrección completa")).not.toBeInTheDocument();
  expect(screen.getByText(/30 preguntas/)).toBeInTheDocument();
  const choice = screen.queryAllByRole("radio")[0];
  if (choice) fireEvent.click(choice);
  const raw = JSON.parse(localStorage.getItem("simbolica-v1")!);
  expect(raw.activeExam.deadline).toBeGreaterThan(Date.now());
  cleanup();
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Reanudar evaluación" }));
  expect(screen.getByText(/30 preguntas/)).toBeInTheDocument();
});
