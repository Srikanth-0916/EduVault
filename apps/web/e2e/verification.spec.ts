import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("student authorizes a scoped share, verifier sees only claims, revocation denies", async ({
  page,
}) => {
  await login(page, "student@demo-ait.edu");
  await page.goto("/student/sharing");
  await page.getByRole("button", { name: "Create share" }).click();
  await page.getByLabel("Recipient name").fill("Acme HR");
  await page.getByLabel("Organisation").fill("Acme Demo");
  await page.getByLabel("Recipient email").fill("hr@acme-demo.example");
  await page.getByLabel("Purpose").fill("Employment screening");
  await page.getByLabel("Institution", { exact: true }).check();
  await page.getByLabel("Programme", { exact: true }).check();
  await page.getByLabel("Enrolment status", { exact: true }).check();
  await page.getByRole("button", { name: "Review authorization" }).click();
  await page.getByRole("button", { name: "Authorize share" }).click();
  await expect(page.getByText("Share authorized")).toBeVisible();

  const verifyUrl = await page.locator("code").filter({ hasText: "/verify/" }).textContent();
  expect(verifyUrl).toContain("/verify/");
  await page.screenshot({
    path: "../../docs/evidence/student-share.png",
    fullPage: true,
  });

  await page.goto(verifyUrl!.trim());
  await expect(page.getByText("Verification link is valid")).toBeVisible();
  await expect(page.getByText("Synthetic demo", { exact: true })).toBeVisible();
  const pageText = await page.locator("body").innerText();
  expect(pageText).not.toContain("123456789012");
  await page.screenshot({
    path: "../../docs/evidence/public-verification.png",
    fullPage: true,
  });

  await page.goto("/student/sharing");
  await page.getByText("Acme HR").first().click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Revoke access" }).click();
  await expect(page.getByText("Revoked").first()).toBeVisible();

  await page.goto(verifyUrl!.trim());
  await expect(page.getByText("Verification unavailable")).toBeVisible();
  await page.screenshot({
    path: "../../docs/evidence/denied-verification.png",
    fullPage: true,
  });
});

test("unknown verification tokens deny generically", async ({ page }) => {
  await page.goto("/verify/this-token-does-not-exist");
  await expect(page.getByText("Verification unavailable")).toBeVisible();
  const text = await page.locator("body").innerText();
  expect(text).toContain("does not reveal whether a student record existed");
  expect(text).not.toContain("123456789012");
});
