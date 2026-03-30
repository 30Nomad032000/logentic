"""
Generate project report PDF from HTML using Puppeteer (via Node.js subprocess).
Also regenerates figures if needed.

Usage:
    python generate_report.py              # Generate PDF from existing HTML
    python generate_report.py --figures    # Regenerate figures first, then PDF
    python generate_report.py --screenshots # Capture dashboard screenshots first
    python generate_report.py --all        # Do everything: figures + screenshots + PDF
"""

import subprocess
import sys
import os
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(ROOT, "project_report.html")
PDF_PATH = os.path.join(ROOT, "Project_Report_Voice_Assistant_Final.pdf")
FIGURES_SCRIPT = os.path.join(ROOT, "generate_figures.py")
SCREENSHOT_SCRIPT = os.path.join(ROOT, "capture_screenshots.js")


def run_cmd(cmd, description):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=False)
    if result.returncode != 0:
        print(f"WARNING: {description} returned exit code {result.returncode}")
    return result.returncode


def generate_figures():
    """Regenerate matplotlib figures."""
    python = sys.executable
    return run_cmd([python, FIGURES_SCRIPT], "Generating figures with matplotlib")


def capture_screenshots():
    """Capture dashboard screenshots with Puppeteer."""
    return run_cmd(["node", SCREENSHOT_SCRIPT],
                   "Capturing dashboard screenshots")


def generate_pdf():
    """Convert HTML report to PDF using Puppeteer."""
    converter_js = os.path.join(ROOT, "_convert_pdf.js")

    html_file_url = "file:///" + HTML_PATH.replace("\\", "/")

    js_code = """
const puppeteer = require("puppeteer");
const path = require("path");

(async () => {
  console.log("Launching browser for PDF generation...");
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage();

  const htmlUrl = """ + repr(html_file_url) + """;
  console.log("Loading HTML from: " + htmlUrl);
  await page.goto(htmlUrl, {
    waitUntil: "networkidle0",
    timeout: 60000,
  });

  // Wait for images to load
  await new Promise(r => setTimeout(r, 3000));

  const pdfPath = """ + repr(PDF_PATH.replace("\\", "/")) + """;
  console.log("Generating PDF: " + pdfPath);
  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    margin: { top: "0", bottom: "0", left: "0", right: "0" },
    displayHeaderFooter: false,
  });

  console.log("PDF generated successfully!");
  await browser.close();
})();
"""

    with open(converter_js, "w") as f:
        f.write(js_code)

    try:
        rc = run_cmd(["node", converter_js], "Generating PDF with Puppeteer")
        return rc
    finally:
        if os.path.exists(converter_js):
            os.unlink(converter_js)


def main():
    parser = argparse.ArgumentParser(description="Generate project report PDF")
    parser.add_argument("--figures", action="store_true",
                        help="Regenerate matplotlib figures")
    parser.add_argument("--screenshots", action="store_true",
                        help="Capture dashboard screenshots (requires server running)")
    parser.add_argument("--all", action="store_true",
                        help="Run everything: figures + screenshots + PDF")
    parser.add_argument("--html-only", action="store_true",
                        help="Skip PDF generation, just prepare assets")
    args = parser.parse_args()

    if args.all:
        args.figures = True
        args.screenshots = True

    if args.figures:
        generate_figures()

    if args.screenshots:
        print("\nNOTE: For screenshots, ensure the server is running:")
        print("  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
        capture_screenshots()

    if not args.html_only:
        if not os.path.exists(HTML_PATH):
            print(f"ERROR: HTML report not found: {HTML_PATH}")
            sys.exit(1)

        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("ERROR: Node.js not found. Install Node.js to generate PDF.")
            sys.exit(1)

        generate_pdf()

    print(f"\n{'='*60}")
    print(f"  DONE!")
    print(f"  HTML Report: {HTML_PATH}")
    if not args.html_only:
        print(f"  PDF Report:  {PDF_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
