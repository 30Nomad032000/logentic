/**
 * Puppeteer script to capture dashboard screenshots from the running server.
 * Run: node capture_screenshots.js
 * Requires: npm install puppeteer (already in package.json)
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

  // 1. Full dashboard screenshot
  console.log("  -> screenshot_dashboard.png");
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 2. Full page screenshot
  console.log("  -> screenshot_dashboard_fullpage.png");
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_fullpage.png"),
    fullPage: true,
  });

  // 3. Top section (stats cards)
  console.log("  -> screenshot_stats.png");
  await page.screenshot({
    path: path.join(OUT, "screenshot_stats.png"),
    clip: { x: 0, y: 0, width: 1400, height: 300 },
  });

  // 4. Scroll to middle and capture
  console.log("  -> screenshot_dashboard_mid.png");
  await page.evaluate(() => window.scrollTo(0, 400));
  await delay(1000);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_mid.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 5. Scroll to bottom
  console.log("  -> screenshot_dashboard_bottom.png");
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await delay(1000);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_bottom.png"),
    clip: { x: 0, y: 0, width: 1400, height: 900 },
  });

  // 6. Try clicking on tabs if they exist
  try {
    // Conversations tab
    const convTab = await page.$('[value="conversations"], [data-value="conversations"]');
    if (convTab) {
      await convTab.click();
      await delay(2000);
      console.log("  -> screenshot_conversations.png");
      await page.screenshot({
        path: path.join(OUT, "screenshot_conversations.png"),
        clip: { x: 0, y: 200, width: 1400, height: 700 },
      });
    }

    // Health tab
    const healthTab = await page.$('[value="health"], [data-value="health"]');
    if (healthTab) {
      await healthTab.click();
      await delay(2000);
      console.log("  -> screenshot_health_latency.png");
      await page.screenshot({
        path: path.join(OUT, "screenshot_health_latency.png"),
        clip: { x: 0, y: 200, width: 1400, height: 700 },
      });
    }

    // Try-it / Tasks tab
    const tryitTab = await page.$('[value="tryit"], [data-value="tryit"]');
    if (tryitTab) {
      await tryitTab.click();
      await delay(2000);
      console.log("  -> screenshot_tryit_tasks.png");
      await page.screenshot({
        path: path.join(OUT, "screenshot_tryit_tasks.png"),
        clip: { x: 0, y: 200, width: 1400, height: 700 },
      });
    }
  } catch (e) {
    console.log("  (some tabs not found, skipping: " + e.message + ")");
  }

  // 7. Narrow viewport for responsive view
  console.log("  -> screenshot_dashboard_narrow.png");
  await page.setViewport({ width: 768, height: 1024, deviceScaleFactor: 2 });
  await page.goto(BASE, { waitUntil: "networkidle2", timeout: 30000 });
  await delay(3000);
  await page.screenshot({
    path: path.join(OUT, "screenshot_dashboard_narrow.png"),
    fullPage: false,
  });

  await browser.close();
  console.log("\nAll screenshots saved to report_assets/");
}

main().catch(err => {
  console.error("Error:", err.message);
  process.exit(1);
});
