import { expect, type Page, test } from "@playwright/test";

// The demo people (infra/demo-users) and their shared dev password, from the stack's .env.
const PASSWORD = process.env.DEMO_USER_PASSWORD ?? "";
const ROLES = {
  rao: "officer",
  fernandes: "bureau head",
  iyer: "bureau head",
  menon: "oversight",
  admin: "admin",
  das: "auditor",
} as const;

test.beforeAll(() => {
  expect(PASSWORD, "set DEMO_USER_PASSWORD (the stack's .env)").not.toBe("");
});

async function signIn(page: Page, user: keyof typeof ROLES) {
  await page.context().clearCookies();
  await page.goto("/");
  await page.locator("#username").fill(user);
  await page.locator("#password").fill(PASSWORD);
  await page.locator("#kc-login").click();
  await expect(page.getByText(`${user} (${ROLES[user]})`)).toBeVisible();
}

test.describe.configure({ mode: "serial" });

test("every role signs in and sees its own menu", async ({ page }) => {
  for (const user of Object.keys(ROLES) as (keyof typeof ROLES)[]) {
    await signIn(page, user);
    const audit = page.getByRole("link", { name: "Audit log" });
    if (["menon", "admin", "das"].includes(user)) await expect(audit).toBeVisible();
    else await expect(audit).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Admin" })).toHaveCount(user === "admin" ? 1 : 0);
  }
});

test("search finds an institution by an alias", async ({ page }) => {
  await signIn(page, "rao");
  await page.getByRole("searchbox", { name: "Search institutions and cases" }).fill("GIT Pune");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("link", { name: "Greenfield Institute of Technology" }).first()).toBeVisible();
});

test("an approved overlap queues an alert to both bureau heads", async ({ page }) => {
  await signIn(page, "admin");
  await page.goto("/#/overlaps");
  const detected = page.waitForResponse((r) => r.url().includes("/api/v1/overlaps/detect"), { timeout: 60_000 });
  await page.getByRole("button", { name: "Look for new overlaps now" }).click();
  expect((await detected).ok()).toBe(true);
  await signIn(page, "fernandes");
  await page.goto("/#/overlaps");
  const decided = page.waitForResponse((r) => r.url().includes("/api/v1/overlaps/") && r.request().method() === "POST");
  // The two refs come in id order, which differs per seed.
  await page.getByRole("button", { name: /^Approve link between C-10[12] and C-10[12]$/ }).first().click();
  expect((await decided).ok()).toBe(true);
  await page.goto("/#/alerts");
  await expect(page.getByText("C-101").first()).toBeVisible();
  await expect(page.getByText(/fernandes@sethu\.test/).first()).toBeVisible();
});

test("a complaint sent to the intake API becomes a case", async ({ page, request }) => {
  await signIn(page, "admin");
  await page.goto("/#/intake");
  await page.getByRole("button", { name: /API key for pgrc-portal/ }).click();
  const key = (await page.locator("p[role=status] code").textContent()) ?? "";
  expect(key).toMatch(/^sethu_/);
  const nonce = `${Date.now()}-${Math.random().toString(16).slice(2)}`.padEnd(16, "0");
  const sent = await request.post("/api/v1/intake/submissions", {
    headers: { "X-Sethu-Key": key, "X-Sethu-Timestamp": String(Math.floor(Date.now() / 1000)), "X-Sethu-Nonce": nonce },
    data: {
      institution_name: "Greenfield Institute of Technology",
      category: "Fee refund",
      body: `Browser test ${nonce}: the caution deposit has not been refunded four months after withdrawal.`,
      complainant: { name: "Playwright Testperson", email: "playwright.testperson@sethu.test" },
    },
  });
  expect(sent.status()).toBe(202);
  await expect
    .poll(async () => {
      await page.reload({ waitUntil: "networkidle" });
      await page.getByRole("heading", { name: "Queue" }).waitFor();
      return page.locator("td", { hasText: /^IN-\d{6}/ }).count();
    }, { timeout: 60_000, intervals: [3_000] })
    .toBeGreaterThan(0);
});

test("a bureau head assigns a case and closes it with a reason", async ({ page }) => {
  await signIn(page, "fernandes");
  await page.goto("/#/cases?bureau=PGRC&status=open");
  await page.getByRole("link", { name: /^C-\d{3}$/ }).first().click();
  await page.getByRole("combobox").first().selectOption("assign");
  await page.getByRole("combobox").nth(1).selectOption({ label: "Anita Rao (officer)" });
  await page.getByRole("button", { name: "Record action" }).click();
  await expect(page.getByText("Assigned to Anita Rao by Maria Fernandes")).toBeVisible();
  await page.getByRole("combobox").first().selectOption("close");
  await page.getByRole("combobox").nth(1).selectOption("resolved");
  await page.getByRole("button", { name: "Record action" }).click();
  await expect(page.getByText("Closed: Resolved by Maria Fernandes")).toBeVisible();
});

test("a report runs and exports as CSV", async ({ page }) => {
  await signIn(page, "menon");
  await page.goto("/#/reports");
  await expect(page.locator("table tbody tr").first()).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export CSV" }).click();
  expect((await download).suggestedFilename()).toMatch(/\.csv$/);
});

test("Verify chain reports the audit log intact", async ({ page }) => {
  await signIn(page, "das");
  await page.goto("/#/audit");
  await page.getByRole("button", { name: "Verify chain" }).click();
  await expect(page.getByText(/^Chain intact, \d+ entries/)).toBeVisible();
});
