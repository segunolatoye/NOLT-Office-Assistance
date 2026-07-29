"""User preferences and settings persistence."""

import json
from pathlib import Path
from typing import Optional

from .paths import get_app_data_dir


class Preferences:
    """Manages user preferences with JSON persistence."""

    def __init__(self):
        self.prefs_file = get_app_data_dir() / "preferences.json"
        self.data = self._load()

    def _load(self) -> dict:
        """Load preferences from file or return defaults."""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return self._defaults()

    @staticmethod
    def _defaults() -> dict:
        """Default preferences structure."""
        return {
            "last_output_folder_images_to_pdf": None,
            "last_output_folder_pdf_to_word": None,
            "last_output_folder_pdf_to_images": None,
            "last_output_folder_merge_pdf": None,
            "last_output_folder_split_pdf": None,
            "file_size_warning_mb": 100,
        }

    def save(self) -> None:
        """Persist preferences to disk."""
        self.prefs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.prefs_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get preference value."""
        return self.data.get(key, default)

    def set(self, key: str, value: Optional[str]) -> None:
        """Set and persist preference value."""
        self.data[key] = value
        self.save()

    def get_last_output_folder(self, operation: str) -> Optional[str]:
        """Get last output folder for operation (images_to_pdf, pdf_to_word, etc)."""
        key = f"last_output_folder_{operation}"
        path = self.get(key)
        if path and Path(path).exists():
            return path
        return None

    def set_last_output_folder(self, operation: str, folder: str) -> None:
        """Set last output folder for operation."""
        key = f"last_output_folder_{operation}"
        self.set(key, str(folder))

    def get_file_size_warning_mb(self) -> int:
        """Get file size warning threshold in MB."""
        return self.data.get("file_size_warning_mb", 100)


# Singleton instance
_prefs: Optional[Preferences] = None


def get_preferences() -> Preferences:
    """Get or create global preferences instance."""
    global _prefs
    if _prefs is None:
        _prefs = Preferences()
    return _prefs
