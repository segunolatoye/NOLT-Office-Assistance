APP_NAME = "NOLT Office Assistant (OA)"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME}"

# Sanitized name used for on-disk folders (app data, logs, temp).
# Kept separate from APP_NAME so filesystem paths stay stable even if the
# display name changes or contains characters that are awkward in paths.
APP_DIR_NAME = "NOLTOfficeAssistant"

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}

SUPPORTED_EXPORT_IMAGE_FORMATS = {"png", "jpg"}

MIN_DPI = 72
MAX_DPI = 600
DEFAULT_DPI = 200

# Keeps very large images from consuming excessive memory during PDF creation.
# A4 at 300 DPI is approximately 2480 x 3508.
DEFAULT_MAX_IMAGE_SIZE = (2480, 3508)