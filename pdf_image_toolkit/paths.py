import platform
import tempfile
from pathlib import Path

from .config import APP_DIR_NAME


def get_app_data_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        base_dir = Path.home() / "AppData" / "Local"

    elif system == "Darwin":
        base_dir = Path.home() / "Library" / "Application Support"

    else:
        base_dir = Path.home() / ".local" / "share"

    app_dir = base_dir / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_log_dir() -> Path:
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_temp_dir() -> Path:
    temp_dir = Path(tempfile.gettempdir()) / APP_DIR_NAME.lower()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir