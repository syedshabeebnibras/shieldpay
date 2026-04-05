import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test("renders hero section with CTA", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/ShieldPay/);
    await expect(
      page.getByRole("heading", { name: /get paid for/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /start protecting/i }),
    ).toBeVisible();
  });

  test("navigates to register from CTA", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /get started/i }).first().click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("smooth scroll to features section", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /see how it works/i }).click();
    // Wait for scroll
    await page.waitForTimeout(500);
    const section = page.locator("#how-it-works");
    await expect(section).toBeInViewport();
  });
});

test.describe("Auth Pages", () => {
  test("register page renders form", async ({ page }) => {
    await page.goto("/register");
    await expect(
      page.getByRole("heading", { name: /create your account/i }),
    ).toBeVisible();
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByText(/freelancer/i)).toBeVisible();
    await expect(page.getByText(/client/i)).toBeVisible();
  });

  test("login page renders form", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("heading", { name: /welcome back/i }),
    ).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });

  test("register validates required fields", async ({ page }) => {
    await page.goto("/register");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/full name is required/i)).toBeVisible();
  });
});

test.describe("Payment Page", () => {
  test("shows error for invalid token", async ({ page }) => {
    await page.goto("/pay/invalid-token-12345");
    // Should show the error/not found state after loading
    await page.waitForTimeout(2000);
    await expect(
      page.getByText(/not found|expired|something went wrong/i),
    ).toBeVisible();
  });
});

test.describe("Dashboard", () => {
  test("redirects unauthenticated users", async ({ page }) => {
    // Mock API to return 401
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ status: 401, body: '{"detail":"Not authenticated"}' }),
    );
    await page.goto("/dashboard");
    // The useAuth hook should redirect to login on 401
    // (via the axios interceptor)
  });
});
