import assert from "node:assert/strict";
import { chromium } from "playwright";

const base = process.env.VIEWSOURCE_SITE_URL || "http://127.0.0.1:8765/";
const browser = await chromium.launch({headless:true});
const page = await browser.newPage({viewport:{width:1440,height:900},colorScheme:"dark"});
try {
  await page.goto(base,{waitUntil:"networkidle"});
  await page.getByRole("heading",{name:"An interface is a living system."}).waitFor();
  assert.equal(await page.locator("#theme-select").inputValue(),"system");
  assert.equal(await page.locator("html").getAttribute("data-theme"),"system");

  await page.locator("#theme-select").selectOption("light");
  assert.equal(await page.locator("html").getAttribute("data-theme"),"light");
  await page.reload({waitUntil:"networkidle"});
  assert.equal(await page.locator("#theme-select").inputValue(),"light");
  await page.locator("#theme-select").selectOption("dark");
  assert.equal(await page.locator("html").getAttribute("data-theme"),"dark");
  await page.locator("#theme-select").selectOption("system");

  await page.locator(".chapter-link").filter({hasText:"CSS"}).click();
  await page.getByRole("heading",{name:"A design language in thousands of declarations."}).waitFor();
  await page.getByRole("button",{name:"E2-023"}).click();
  await page.getByRole("heading",{name:"Finding F2-023"}).waitFor();

  await page.locator(".chapter-link").filter({hasText:"JavaScript"}).click();
  await page.getByRole("heading",{name:"Parsed module relationships"}).waitFor();
  assert.equal(await page.locator(".module-source").count(),8);
  await page.locator(".module-source").first().click();
  assert.equal(await page.locator(".inspection-card").count(),1);
    await page.locator(".chapter-link").filter({hasText:"Components"}).click();
  await page.locator(".graph-node").first().click();
  assert.equal(await page.locator(".inspection-card").count(),1);

  await page.locator(".chapter-link").filter({hasText:"Research queue"}).click();
  await page.getByRole("heading",{name:"Work that stays on the map."}).waitFor();
  assert.ok(await page.locator(".queue-group").count()>=10);
  await page.locator(".queue-group").first().locator("summary").click();
  assert.ok(await page.locator(".task").count()>0);

  await page.locator("#version-select").selectOption("1");
  await page.getByRole("heading",{name:"A snapshot of an interface"}).waitFor();
  await page.locator("#version-select").selectOption("2");
  await page.getByRole("heading",{name:"An interface is a living system."}).waitFor();

  await page.locator("#site-search").fill("WebSocket");
  await page.getByRole("heading",{name:"Results for “WebSocket”"}).waitFor();
  assert.ok(await page.locator(".evidence-pill,.entity-mini").count()>0);
  await page.locator("#clear-search").click();

  await page.setViewportSize({width:390,height:844});
  const overflow = await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
  assert.ok(overflow<=2,"Unexpected page horizontal overflow: "+overflow+"px");
  console.log("PASS: chapters, evidence, graph, task queues, versions, search, appearance persistence and mobile layout");
} finally {
  await browser.close();
}

