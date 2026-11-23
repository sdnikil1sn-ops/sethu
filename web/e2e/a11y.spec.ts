import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Accessibility and layout of every screen (Phase 5, item 4): axe (WCAG 2.1 A and AA) must find nothing
// serious or critical; nothing may be wider than a 375 px phone screen; the keyboard reaches the content.
// With SETHU_SCREENS=1 it also saves a screenshot of each screen at 1366 and 375 px wide to docs/screens/.
const PASSWORD = process.env.DEMO_USER_PASSWORD ?? "";
const SCREENS = process.env.SETHU_SCREENS === "1";
const WIDTHS = [1366, 375];

const NAMES: Record<string, string> = { rao: "officer", fernandes: "bureau head", menon: "oversight", admin: "admin", das: "auditor" };

async function signIn(page: Page, user: string) {
  await page.context().clearCookies();
  await page.goto("/");
  await page.locator("#username").fill(user);
  await page.locator("#password").fill(PASSWORD);
  await page.locator("#kc-login").click();
  await expect(page.getByText(`${user} (${NAMES[user]})`)).toBeVisible();
}

/** Serious and critical axe results, one line each, so a failure says what and where. */
async function axe(page: Page): Promise<string[]> {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  return result.violations
    .filter((v) => v.impact === "serious" || v.impact === "critical")
    .map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
}

async function check(page: Page, name: string) {
  await page.locator("main h1").first().waitFor();
  await page.waitForLoadState("networkidle");
  const problems: string[] = [];
  for (const width of WIDTHS) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 768 });
    await page.waitForTimeout(300);
    problems.push(...(await axe(page)).map((p) => `${name} @${width}: ${p}`));
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (overflow > 1) problems.push(`${name} @${width}: the page is ${overflow}px wider than the screen`);
    if (SCREENS) await page.screenshot({ path: `../docs/screens/${name}-${width}.png`, fullPage: true });
  }
  await page.setViewportSize({ width: 1366, height: 768 });
  return problems;
}

test.describe.configure({ mode: "serial" });
test.beforeAll(() => expect(PASSWORD, "set DEMO_USER_PASSWORD (the stack's .env)").not.toBe(""));

const SCREENS_BY_USER: Record<string, string[]> = {
  admin: ["/", "/institutions", "/cases", "/graph", "/overlaps", "/alerts", "/findings", "/queue", "/reports",
          "/intake", "/admin", "/ai", "/audit"],
  rao: ["/mine"],
  fernandes: ["/workload"],
};

test("every screen passes axe and fits a 375 px screen", async ({ page }) => {
  test.setTimeout(600_000);
  const problems: string[] = [];
  for (const [user, routes] of Object.entries(SCREENS_BY_USER)) {
    await signIn(page, user);
    for (const route of routes) {
      await page.goto(`/#${route}`);
      const name = route === "/" ? "dashboard" : route.slice(1);
      problems.push(...(await check(page, user === "admin" ? name : `${name}-${user}`)));
    }
  }
  // Pages reached through a link: a case (as its own bureau's officer) and an institution profile.
  await signIn(page, "rao");
  await page.goto("/#/cases?bureau=PGRC");
  await page.getByRole("link", { name: /^C-\d{3}$/ }).first().click();
  problems.push(...(await check(page, "case")));
  await page.goto("/#/institutions");
  await page.getByRole("link", { name: "Greenfield Institute of Technology" }).first().click();
  problems.push(...(await check(page, "institution")));
  expect(problems, problems.join("\n")).toEqual([]);
});

test("the keyboard reaches the content, with a visible focus", async ({ page }) => {
  await signIn(page, "rao");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("button", { name: "Skip to main content" });
  await expect(skip).toBeFocused();
  const outline = await skip.evaluate((el) => getComputedStyle(el).outlineStyle);
  expect(outline).not.toBe("none");
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await page.keyboard.press("Tab");          // the first control inside the content
  expect(await page.evaluate(() => !!document.activeElement?.closest("main"))).toBe(true);
});

test("on a phone, the stacked case list is still a table to assistive technology", async ({ page }) => {
  await signIn(page, "menon");
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/#/cases?overdue=true");
  const table = page.getByRole("table");
  await expect(table).toHaveCount(1);
  await expect(table.getByRole("columnheader", { name: "Case" })).toHaveCount(1);
  expect(await table.getByRole("cell").count()).toBeGreaterThan(20);
});
