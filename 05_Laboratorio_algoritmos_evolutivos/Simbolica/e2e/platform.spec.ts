import { test, expect, type Page } from "@playwright/test";
async function nav(page: Page, label: string) {
  const menu = page.getByRole("button", { name: "Abrir menú" });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: label, exact: true }).click();
}
async function unit(page: Page, title: string) {
  const menu = page.getByRole("button", { name: "Abrir menú" });
  if (await menu.isVisible()) await menu.click();
  await page
    .locator(".unit-nav")
    .getByRole("button", { name: new RegExp(title) })
    .click();
  await page.getByRole("button", { name: "Laboratorio", exact: true }).click();
}
test("curso, actividades y evaluación persistente sin errores de consola", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  const external: string[] = [];
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname)) {
      external.push(url.href);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Las mejores ideas/ }),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/inicio-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Continuar aprendizaje" }).click();
  await page.getByRole("button", { name: "Laboratorio", exact: true }).click();
  await page.getByRole("button", { name: "Mostrar función original" }).click();
  await expect(page.getByText("Original x²", { exact: true })).toBeVisible();
  await unit(page, "Árboles de expresión");
  await page.getByLabel("Terminal personalizado").fill("7");
  await page
    .getByRole("button", { name: "Reemplazar nodo seleccionado" })
    .click();
  await expect(page.locator(".inset .mono")).toHaveText("7");
  await unit(page, "Recorridos y evaluación");
  await page.getByRole("button", { name: "Preorder", exact: true }).click();
  await page.getByRole("button", { name: "Pausar", exact: true }).click();
  await page.getByLabel("Valor de x").fill("5");
  await unit(page, "Operaciones y generación");
  await page.getByLabel("Método").selectOption("full");
  await page.getByRole("button", { name: "Generar árbol" }).click();
  await unit(page, "CSV, MSE");
  await page.getByRole("button", { name: "Corregir celdas" }).click();
  await expect(page.getByText("0 de 7 celdas correctas")).toBeVisible();
  await unit(page, "Población y selección");
  await page.getByRole("button", { name: "Ejecutar torneo" }).click();
  await expect(page.getByRole("status")).toContainText("gana árbol 1");
  await unit(page, "Cruce, mutación");
  await page
    .getByRole("button", { name: "Cruzar ramas seleccionadas" })
    .click();
  await expect(page.getByRole("heading", { name: "Hijo 1" })).toBeVisible();
  await page.getByRole("button", { name: "1 · Terminal", exact: true }).click();
  await page.getByRole("button", { name: "Aplicar estrategia" }).click();
  await expect(
    page.getByRole("heading", { name: /Resultado: altura/ }),
  ).toBeVisible();
  await page.screenshot({
    path: `test-results/genetica-${info.project.name}.png`,
    fullPage: true,
  });
  await unit(page, "Ciclo evolutivo");
  await page
    .getByRole("button", { name: "Siguiente generación", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Generación 1");
  await page.getByRole("button", { name: "Evaluación de la unidad" }).click();
  await page.getByRole("button", { name: "Entregar evaluación" }).click();
  await expect(page.getByText("0%", { exact: true })).toBeVisible();
  await nav(page, "Mi progreso");
  await expect(page.getByText("Unidad 8", { exact: true })).toBeVisible();
  await page.reload();
  await nav(page, "Mi progreso");
  await expect(page.getByText("Unidad 8", { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
  expect(external).toEqual([]);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > innerWidth,
  );
  expect(overflow).toBe(false);
});
test("CSV y búsqueda real en worker", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await nav(page, "Laboratorio final");
  await page.getByLabel("Cargar CSV").setInputFiles({
    name: "invalido.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("x,y\n1,nada"),
  });
  await expect(page.getByRole("alert")).toContainText("Línea 2");
  await page.getByLabel("Cargar CSV").setInputFiles({
    name: "datos.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("x,y\n0,1\n1,2\n2,5\n3,10"),
  });
  await expect(page.getByRole("heading", { name: "datos.csv" })).toBeVisible();
  await page.getByLabel("Población", { exact: true }).fill("8");
  await page.getByLabel("Generaciones", { exact: true }).fill("2");
  await page.getByRole("button", { name: "Iniciar búsqueda" }).click();
  await expect(
    page.getByText("Presupuesto completado", { exact: true }),
  ).toBeVisible({ timeout: 20000 });
  await expect(page.getByText("2 / 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Reiniciar", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Iniciar búsqueda" }),
  ).toBeEnabled();
  expect(errors).toEqual([]);
});
test("simulacro conserva reloj y respuestas y solo corrige al entregar", async ({
  page,
}) => {
  await page.goto("/");
  await nav(page, "Examen final");
  await page.getByRole("button", { name: "Comenzar simulacro" }).click();
  await expect(
    page.getByRole("heading", { name: /30 preguntas/ }),
  ).toBeVisible();
  await expect(page.getByText("Corrección completa")).toHaveCount(0);
  const inputs = page.getByRole("radio");
  if (await inputs.count()) await inputs.first().check();
  else {
    const numeric = page.locator(".question input").first();
    if (await numeric.count()) await numeric.fill("1");
  }
  const before = await page.evaluate(
    () => JSON.parse(localStorage.getItem("simbolica-v1")!).activeExam,
  );
  await page.reload();
  await page.getByRole("button", { name: "Reanudar evaluación" }).click();
  const after = await page.evaluate(
    () => JSON.parse(localStorage.getItem("simbolica-v1")!).activeExam,
  );
  expect(after.deadline).toBe(before.deadline);
  expect(after.answers).toEqual(before.answers);
  await page.getByRole("button", { name: "Entregar simulacro" }).click();
  await expect(
    page.getByRole("heading", { name: "Corrección completa" }),
  ).toBeVisible();
  await expect(page.locator(".correction")).toHaveCount(30);
});
