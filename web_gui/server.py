import subprocess
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

import configuration as cfg
from utils.notify import desktop_notification

app = FastAPI(title="Stock Market Research", version="1.0.0")

SCRIPT_PATH = cfg.BASE_DIR / "data_pipeline" / "create_report.py"
REPORT_PATH = cfg.REPORT_DIR / "simple_stock_report.html"


def run_report(*extra_args: str) -> subprocess.CompletedProcess:
    """Runs create_report.py with the same Python (and venv) as the server."""
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "-d", str(cfg.DATA_DIR), *extra_args],
        capture_output=True,
        text=True,
    )


def to_response(result: subprocess.CompletedProcess, message: str):
    if result.returncode == 0:
        return {"status": "success", "message": message}
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": result.stderr},
    )


@app.get("/", summary="View report", tags=["Dashboard"])
def index():
    """Serves the main stock report."""
    return FileResponse(REPORT_PATH)


@app.post("/actualize", summary="Actualize data", tags=["Reports"])
def actualize():
    """Downloads fresh data from Yahoo Finance and rebuilds the report."""
    result = run_report("-a")
    if result.returncode == 0:
        desktop_notification("Stock Market Research", "Data actualized. The report has been updated.")
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
