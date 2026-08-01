import subprocess
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import configuration as cfg

app = FastAPI(title="Stock Market Research", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="View report", tags=["Dashboard"])
def index():
    """Serves the main stock report."""
    report_path = Path(cfg.REPORT_DIR) / "simple_stock_report.html"
    return FileResponse(report_path)


@app.post("/actualize", summary="Actualize data", tags=["Reports"])
def actualize():
    """Triggers the create_report.py script with the actualize flag."""
    try:
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        result = subprocess.run(
            [python_cmd, str(script_path), "-d", str(data_dir), "-a"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success", "message": "Report updated."}
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": result.stderr},
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )


@app.post("/filter", summary="Filter report (D+ stocks)", tags=["Reports"])
def filter_report():
    """Runs create_report.py with specific filter and sort, no actualization."""
    try:
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        result = subprocess.run(
            [
                python_cmd,
                str(script_path),
                "-d",
                str(data_dir),
                "-cv",
                "classification:D+",
                "-s",
                "recommendationKey",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success", "message": "Report filtered."}
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": result.stderr},
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )


@app.post("/refresh", summary="Refresh report", tags=["Reports"])
def refresh_report():
    """Regenerates the report from existing data (no actualization)."""
    try:
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        result = subprocess.run(
            [python_cmd, str(script_path), "-d", str(data_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"status": "success", "message": "Report refreshed."}
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": result.stderr},
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )


if __name__ == "__main__":
    import uvicorn

    print("\n--- Stock Market Research Server (FastAPI) ---")
    print(f"Report available at:  http://localhost:{cfg.FASTAPI_PORT}")
    print(f"API docs available at: http://localhost:{cfg.FASTAPI_PORT}/docs")
    print("Press Ctrl+C to stop the server.\n")
    uvicorn.run(app, host="0.0.0.0", port=cfg.FASTAPI_PORT)
