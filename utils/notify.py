import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)


def desktop_notification(title: str, message: str):
    """
    Shows a desktop notification on the machine running the server (Linux, notify-send).

    Browser notifications are hidden by Opera when the report tab is the active one,
    so the server notifies the desktop directly. Does nothing if notify-send is missing.
    """
    if shutil.which("notify-send") is None:
        logger.warning("notify-send not found, skipping desktop notification.")
        return
    try:
        subprocess.run(["notify-send", title, message], timeout=5)
    except Exception as e:
        logger.error(f"Desktop notification failed: {e}")
