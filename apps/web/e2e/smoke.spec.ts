import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("login lands on the institution dashboard with live synthetic metrics", async ({ page }) => {
  await page.goto("/login");
  await page.screenshot({
    path: "../../docs/evidence/login.png",
    fullPage: true,
  });
  await login(page, "operator@demo-ait.edu");
  await expect(page).toHaveURL(/\/institution$/);
  await expect(page.getByRole("heading", { name: /overview$/i })).toBeVisible();
  await expect(page.getByText(/synthetic/i).first()).toBeVisible();
  await page.screenshot({
    path: "../../docs/evidence/institution-dashboard.png",
    fullPage: true,
  });
});
