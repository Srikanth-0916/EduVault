import { expect, test } from "@playwright/test";

import { login, switchUser } from "./helpers";

test("institution uploads, validates, attests; reviewer accepts the batch", async ({ page }) => {
  await login(page, "operator@demo-ait.edu");
  await page.goto("/institution/batches/new");
  await page.getByRole("button", { name: "Continue to upload" }).click();
  await page.getByRole("button", { name: "Use bundled sample" }).click();
  await expect(page.getByText(/staged/)).toBeVisible();
  await page.getByRole("button", { name: "Run validation" }).click();
  await expect(page.getByText("Validation complete")).toBeVisible();
  await page.getByRole("button", { name: "Open batch results" }).click();
  await expect(page).toHaveURL(/\/institution\/batches\/(?!new$)[^/]+$/);
  const batchUrl = new URL(page.url()).pathname;
  await page.screenshot({
    path: "../../docs/evidence/batch-results.png",
    fullPage: true,
  });

  await switchUser(page, "nodal@demo-ait.edu");
  await page.goto(batchUrl);
  await page.getByRole("button", { name: "Attest & submit" }).click();
  await page.getByLabel("Attesting nodal officer").fill("Nisha Kulkarni");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Confirm attestation" }).click();
  await expect(page.getByText(/Under AICTE review/i).first()).toBeVisible();

  await switchUser(page, "reviewer@aicte.demo");
  await page.goto("/aicte");
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await page.screenshot({
    path: "../../docs/evidence/aicte-dashboard.png",
    fullPage: true,
  });
  await page.goto("/aicte/review");
  await page.locator('a[href^="/aicte/review/"]').first().click();
  await expect(page.getByRole("heading", { name: "Decision" })).toBeVisible();
  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await page.getByLabel("Decision reason").fill("Synthetic browser acceptance run");
  await page.getByRole("button", { name: "Confirm acceptance" }).click();
  await expect(page.getByText(/Decision recorded/i)).toBeVisible();
  await page.screenshot({
    path: "../../docs/evidence/review-decision.png",
    fullPage: true,
  });
});
