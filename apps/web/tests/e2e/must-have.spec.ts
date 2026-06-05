import { expect, test } from "@playwright/test";

test("signup, API key, ingestion, dashboard, and share flow", async ({ page }, testInfo) => {
  const project = testInfo.project.name.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  const email = `owner-${project}-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`;
  await page.goto("/signup");
  await page.getByLabel("Organization").fill("Playwright Org");
  await page.getByLabel("Full name").fill("Playwright Owner");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("Password123!");
  const signupResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/api/backend/auth/signup")
  );
  await page.getByRole("button", { name: "Create workspace" }).click();
  const signupResponse = await signupResponsePromise;
  expect(signupResponse.status(), await signupResponse.text()).toBe(201);

  await expect(page.getByRole("heading", { name: "Analytics overview" })).toBeVisible({
    timeout: 15_000
  });

  await page.getByRole("link", { name: "API Keys" }).click();
  await page.getByLabel("Key name").fill("E2E ingestion");
  await page.getByRole("button", { name: "Generate" }).click();
  await expect(page.locator("code")).toContainText("pa_");
  const apiKey = await page.locator("code").first().innerText();

  await page.getByRole("link", { name: "Ingestion" }).click();
  await page.getByLabel("API key").first().fill(apiKey);
  await page.getByRole("button", { name: "Send event" }).click();
  await expect(page.getByText("Accepted 1 event.")).toBeVisible();

  await page.getByRole("link", { name: "Dashboards" }).click();
  await page.getByLabel("Dashboard name").fill("E2E Growth");
  await page.getByRole("button", { name: "Create" }).click();
  await page.getByLabel("Widget title").fill("Page views");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByText("Page views").last()).toBeVisible();
  await page.getByRole("button", { name: "Share" }).click();
  await expect(page.getByRole("button", { name: "Copy link" })).toBeVisible();
});
