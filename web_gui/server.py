import subprocess
import os
import flask
from flask import Flask, send_from_directory, jsonify
import configuration as cfg
from pathlib import Path

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    """Serves the main stock report."""
    return send_from_directory(cfg.REPORT_DIR, "simple_stock_report.html")


@app.route("/actualize", methods=["POST", "OPTIONS"])
def actualize():
    """Triggers the create_report.py script with the actualize flag."""
    if flask.request.method == "OPTIONS":
        response = flask.make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    try:
        # Construct the command to run create_report.py
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        result = subprocess.run(
            [python_cmd, str(script_path), "-d", str(data_dir), "-a"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            res = jsonify({"status": "success", "message": "Report updated."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 200
        else:
            res = jsonify({"status": "error", "error": result.stderr})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 500

    except Exception as e:
        res = jsonify({"status": "error", "error": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500


@app.route("/filter", methods=["POST", "OPTIONS"])
def filter_report():
    """Runs create_report.py with specific filter and sort, no actualization."""
    if flask.request.method == "OPTIONS":
        response = flask.make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    try:
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        # Command: python create_report.py -d my_data/ -cv classification:D+ -s recommendationKey
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
            res = jsonify({"status": "success", "message": "Report filtered."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 200
        else:
            res = jsonify({"status": "error", "error": result.stderr})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 500

    except Exception as e:
        res = jsonify({"status": "error", "error": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500


@app.route("/refresh", methods=["POST", "OPTIONS"])
def refresh_report():
    """Regenerates the report from existing data (no actualization)."""
    if flask.request.method == "OPTIONS":
        response = flask.make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    try:
        script_path = Path(cfg.BASE_DIR) / "data_pipeline" / "create_report.py"
        data_dir = cfg.DATA_DIR

        python_cmd = "python3" if os.name != "nt" else "python"

        # Command: python create_report.py -d my_data/
        result = subprocess.run(
            [python_cmd, str(script_path), "-d", str(data_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            res = jsonify({"status": "success", "message": "Report refreshed."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 200
        else:
            res = jsonify({"status": "error", "error": result.stderr})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 500

    except Exception as e:
        res = jsonify({"status": "error", "error": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500


if __name__ == "__main__":
    print(f"\n--- Stock Market Research Server ---")
    print(f"Report available at: http://localhost:{cfg.FLASK_PORT}")
    print(f"Press Ctrl+C to stop the server.\n")
    app.run(host="0.0.0.0", port=cfg.FLASK_PORT, debug=True)
