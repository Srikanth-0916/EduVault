import { expect, type Page } from "@playwright/test";

export const DEMO_PASSWORD = "Demo@1234";

export async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Work email").fill(email);
  await page.getByLabel(/^Password/).fill(DEMO_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

export async function switchUser(page: Page, email: string) {
  await page.evaluate(() => window.localStorage.clear());
  await login(page, email);
}
