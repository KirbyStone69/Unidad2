import { defineConfig, devices } from "@playwright/test";
const production = process.env.E2E_PRODUCTION === "1";
const baseURL = production ? "http://localhost:4173" : "http://localhost:5173";
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL,
    channel: "chromium",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"] },
    },
  ],
  webServer: {
    command: production ? "npm run preview -- --port 4173" : "npm run dev",
    url: baseURL,
    reuseExistingServer: true,
    timeout: 30_000,
  },
  reporter: "list",
});
