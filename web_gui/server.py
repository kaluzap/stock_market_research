import subprocess
import sys
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import configuration as cfg
from utils.notify import desktop_notification

app = FastAPI(title="Stock Market Research", version="1.0.0")

SCRIPT_PATH = cfg.BASE_DIR / "data_pipeline" / "create_report.py"
REPORT_PATH = cfg.REPORT_DIR / "simple_stock_report.html"

# Only one pipeline run at a time: two runs (e.g. two clicks on "Actualize
# Data") would write the same data and report files at the same time
pipeline_lock = threading.Lock()

# Shown before the first report exists (e.g. right after cloning the repo)
NO_REPORT_PAGE = """<!DOCTYPE html>
<html><body style="font-family: sans-serif; margin: 2rem">
<h1>No report yet</h1>
<p>Download the stock data to build the first report (this takes about 30 seconds).</p>
<button onclick="this.disabled = true; this.textContent = 'Downloading...';
  fetch('/actualize', {method: 'POST'}).then(() => location.reload())">
  Download data</button>
</body></html>"""


def run_report(*extra_args: str) -> subprocess.CompletedProcess | None:
    """Runs create_report.py with the same Python (and venv) as the server.

    Returns None, without running it, if another run is still in progress.
    """
    if not pipeline_lock.acquire(blocking=False):
        return None
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "-d", str(cfg.DATA_DIR), *extra_args],
            capture_output=True,
            text=True,
        )
    finally:
        pipeline_lock.release()


def to_response(result: subprocess.CompletedProcess | None, message: str):
    if result is None:
        return JSONResponse(
            status_code=409,
            content={
                "status": "error",
                "error": "The report is already being updated. Try again in a moment.",
            },
        )
    if result.returncode == 0:
        return {"status": "success", "message": message}
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": result.stderr},
    )


@app.get("/", summary="View report", tags=["Dashboard"])
def index():
    """Serves the main stock report."""
    if not REPORT_PATH.exists():
        return HTMLResponse(NO_REPORT_PAGE, status_code=404)
    return FileResponse(REPORT_PATH)


@app.post("/actualize", summary="Actualize data", tags=["Reports"])
def actualize():
    """Downloads fresh data from Yahoo Finance and rebuilds the report."""
    result = run_report("-a")
    if result is None:
        pass  # Busy: the run in progress sends its own notification
    elif result.returncode == 0:
        desktop_notification(
            "Stock Market Research", "Data actualized. The report has been updated."
        )
    else:
        desktop_notification("Stock Market Research", "Data actualization failed.")
    return to_response(result, "Report updated.")


@app.post("/filter", summary="Filter report (D+ stocks)", tags=["Reports"])
def filter_report():
    """Rebuilds the report with only D+ stocks, sorted by recommendation."""
    result = run_report("-cv", "classification:D+", "-s", "recommendationKey")
    return to_response(result, "Report filtered.")


@app.post("/refresh", summary="Refresh report", tags=["Reports"])
def refresh_report():
    """Rebuilds the report from the stored data (no download)."""
    result = run_report()
    return to_response(result, "Report refreshed.")


if __name__ == "__main__":
    import uvicorn

    print("\n--- Stock Market Research Server ---")
    print(f"Report available at:   http://localhost:{cfg.SERVER_PORT}")
    print(f"API docs available at: http://localhost:{cfg.SERVER_PORT}/docs")
    print("Press Ctrl+C to stop the server.\n")
    # Only reachable from this computer, not from the local network
    uvicorn.run(app, host="127.0.0.1", port=cfg.SERVER_PORT)
