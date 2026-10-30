import { defineConfig, devices } from "@playwright/test";

const apiBase = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000";
const webBase = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: webBase,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command:
        "cd ../api && rm -f var/e2e.db && ENV=development DATABASE_URL=sqlite:///./var/e2e.db AUTO_SEED=true WEB_BASE_URL=http://localhost:3000 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: `${apiBase}/api/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      url: `${webBase}/login`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
