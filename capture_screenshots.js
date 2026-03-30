/**
 * Puppeteer script to capture REAL dashboard screenshots from the running server.
 * Run: node capture_screenshots.js
 * Requires: npm install puppeteer
 * Requires: Server running at http://localhost:8000
 */

const puppeteer = require("puppeteer");
const path = require("path");

const OUT = path.join(__dirname, "report_assets");
const BASE = "http://localhost:8000";

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--font-render-hinting=none"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });

  // Navigate to dashboard
  console.log("Loading dashboard at " + BASE + " ...");
  try {
    await page.goto(BASE, { waitUntil: "networkidle2", timeout: 30000 });
  } catch (e) {
    console.error("Could not connect to " + BASE);
    console.error("Make sure the server is running:");
    console.error("  cd voice-assistant && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000");
    await browser.close();
    process.exit(1);
  }

  // Let React render and data load
  await delay(4000);

  // 1. Full dashboard screenshot (top section, no scroll needed)
  console.log("  -> screenshot_dashboard_full.png");
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_full.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 2. Full page scrollable screenshot
  console.log("  -> screenshot_dashboard_fullpage.png");
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_fullpage.png"),
    fullPage: true,
  });

  // 3. Scroll DOWN past the header (header is ~60px tall) and capture mid section
  // Get the actual page height first
  const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
  console.log("  Page body height: " + bodyHeight + "px");

  // Scroll to show content below the header bar
  console.log("  -> screenshot_dashboard_mid.png");
  await page.evaluate(() => window.scrollTo(0, 500));
  await delay(1500);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_mid.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 4. Scroll further to bottom section
  console.log("  -> screenshot_dashboard_bottom.png");
  await page.evaluate(() => window.scrollTo(0, 900));
  await delay(1500);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_bottom.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 5. Narrow viewport (mobile)
  console.log("  -> screenshot_dashboard_narrow.png");
  await page.setViewport({ width: 768, height: 1024, deviceScaleFactor: 2 });
  await page.goto(BASE, { waitUntil: "networkidle2", timeout: 30000 });
  await delay(3000);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_narrow.png"),
    clip: { x: 0, y: 0, width: 768, height: 1024 },
  });

  await browser.close();
  console.log("\nAll screenshots saved to report_assets/");
}

main().catch(err => {
  console.error("Error:", err.message);
  process.exit(1);
});
