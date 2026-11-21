import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from web_gui import server


@pytest.fixture
def client():
    return TestClient(server.app)


def fake_run(returncode: int, stderr: str = ""):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


@pytest.fixture
def notify(mocker):
    # Never show real desktop pop-ups during tests
    return mocker.patch("web_gui.server.desktop_notification")


def test_index_serves_report(client, mocker, tmp_path):
    report = tmp_path / "report.html"
    report.write_text("<html>report</html>")
    mocker.patch("web_gui.server.REPORT_PATH", report)

    response = client.get("/")

    assert response.status_code == 200
    assert "report" in response.text


def test_refresh_success(client, mocker):
    run = mocker.patch("web_gui.server.subprocess.run", return_value=fake_run(0))

    response = client.post("/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Report refreshed."}
    cmd = run.call_args.args[0]
    # Uses the server's own Python, so the venv is always the right one
    assert cmd[0] == sys.executable
    assert "-a" not in cmd


def test_filter_passes_filter_and_sort(client, mocker):
    run = mocker.patch("web_gui.server.subprocess.run", return_value=fake_run(0))

    response = client.post("/filter")

    assert response.status_code == 200
    cmd = run.call_args.args[0]
    assert cmd[-4:] == ["-cv", "classification:D+", "-s", "recommendationKey"]


def test_actualize_success_notifies(client, mocker, notify):
    run = mocker.patch("web_gui.server.subprocess.run", return_value=fake_run(0))

    response = client.post("/actualize")

    assert response.status_code == 200
    assert "-a" in run.call_args.args[0]
    assert "actualized" in notify.call_args.args[1]


def test_actualize_failure_returns_500_with_stderr(client, mocker, notify):
    mocker.patch(
        "web_gui.server.subprocess.run", return_value=fake_run(1, "Yahoo rate limit")
    )

    response = client.post("/actualize")

    assert response.status_code == 500
    assert response.json() == {"status": "error", "error": "Yahoo rate limit"}
    assert "failed" in notify.call_args.args[1]


def test_index_without_report_shows_download_page(client, mocker, tmp_path):
    mocker.patch("web_gui.server.REPORT_PATH", tmp_path / "missing.html")

    response = client.get("/")

    assert response.status_code == 404
    assert "No report yet" in response.text
