# PDF Image Toolkit - Favicon Configuration Guide

## Custom Favicon Support

The application now supports custom favicon (window icon) configuration. The app will automatically search for and load a favicon from multiple locations in this order:

### Favicon Search Paths (Priority Order)

1. **Project root**: `favicon.ico` (next to main.py)
2. **App data folder**: the same OS-specific folder the app uses for logs and preferences (see below)
3. **Fallback**: Uses default Tkinter window icon

### How to Use

#### Option 1: Package with Application (Recommended for Distribution)
Place `favicon.ico` in the project root:
```
pdf_image_toolkit_1.0.0/
├── favicon.ico          ← Your custom favicon here
├── main.py
├── setup.py
└── pdf_image_toolkit/
    └── ...
```

#### Option 2: User Configuration (Recommended for End Users)
1. Locate the app data folder for your OS (see "Log File Location" in README.md)
2. Place `favicon.ico` in that directory
3. Restart the application

### Supported Formats
- `.ico` (recommended for Windows)
- `.png` (automatically converted)
- `.jpg` / `.jpeg`
- Any PIL-supported image format

### Creating a Custom Favicon

#### From an existing image:
```bash
# Using PIL/Pillow (recommended)
from PIL import Image
img = Image.open("my_icon.png")
img.save("favicon.ico")

# Or using ImageMagick (if installed)
convert my_icon.png favicon.ico
```

#### From scratch:
- Use online favicon generator: https://www.favicon-generator.org/
- Recommended size: 32x32 or 64x64 pixels
- Export as `.ico` format

### Logging

The app logs favicon loading attempts:
- Success: "Loaded favicon from: [path]"
- Failure: "Failed to load favicon from: [path]" (in debug mode)
- Default: "No custom favicon found, using default icon"

Check the app log for details: `~/AppData/Local/NOLTOfficeAssistant/logs/app.log`

---

## New Features Summary

### 1. **Cancel Button**
- Cancel long-running operations mid-task
- Becomes enabled when operation starts, disabled when complete
- Gracefully stops background worker thread

### 2. **File Count Display**
- Each file list shows count: "(5 files)" or "(1 file)"
- Updates in real-time as files are added/removed
- Helps with UI visibility and prevents accidental empty submissions

### 3. **Remember Last Output Folder**
- App remembers last output folder for each operation type
- File picker defaults to last used folder
- Speeds up workflows with repeating output locations
- Preferences stored in: `~/AppData/Local/NOLTOfficeAssistant/preferences.json`

### 4. **File Size Warnings**
- Warns before processing large batches
- Configurable threshold (default: 100 MB)
- Can be adjusted in preferences.json
- Prevents accidental processing of huge files

### 5. **Input Validation Enhancements**
- Validates that file lists are not empty before operations
- Shows clear error messages for user input errors
- Prevents operations with 0 files selected

### 6. **Thread-Safe Cancellation**
- Background worker now supports graceful cancellation
- Checks cancellation flag periodically during long operations
- Properly cleans up resources on cancel
