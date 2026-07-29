"""UI utilities and helpers for the desktop application."""

from pathlib import Path
from typing import List


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_total_file_size(paths: List[str | Path]) -> int:
    """Calculate total size of files in MB."""
    total = 0
    for path in paths:
        try:
            total += Path(path).stat().st_size
        except (OSError, ValueError):
            pass
    return total


def get_listbox_count_text(count: int, label: str = "file") -> str:
    """Generate count text for display. e.g., '5 files' or '1 file'."""
    plural = "s" if count != 1 else ""
    return f"({count} {label}{plural})"


def load_icon_safe(icon_path: str | Path) -> bytes | None:
    """
    Safely load icon file with fallback support.
    Supports .ico, .png, and other PIL-supported formats.
    """
    try:
        path = Path(icon_path)
        if not path.exists():
            return None
        if not path.is_file():
            return None
        return path.read_bytes()
    except (OSError, ValueError):
        return None
