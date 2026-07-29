# PDF Image Toolkit 1.0.0v

A lightweight installable Python desktop software for PDF and image operations.

## What It Can Do

- Convert images to PDF
- Convert PDF to Word
- Convert PDF pages to images
- Merge PDFs
- Split PDFs

## Improvements in 1.0.0v

This version includes the improvement ideas from the planned 1.1.0 release, but renamed as `1.0.0v`.

### Added

- Better memory handling for large images and PDF pages
- Rotating app log file
- OS-compatible app data folder
- OS-compatible temporary folder
- Friendly error messages
- Progress bar while tasks are running
- Runtime and development requirements split
- Cleaner internal structure
- Central app configuration
- Safer background worker handling
- Output image DPI validation
- Optional image resizing for image-to-PDF conversion

## Project Structure

```text
pdf_image_toolkit_1.0.0v/
│
├── pdf_image_toolkit/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── operations.py
│   ├── paths.py
│   └── workers.py
│
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── build_windows.bat
├── build_windows_onefile.bat
├── setup.py
└── README.md
```

## Install for Development

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Build Windows Installer-Like Folder

Recommended for reliability:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
build_windows.bat
```

The app will be created inside:

```text
dist/PDF Image Toolkit 1.0.0v/
```

## Build Single EXE

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
build_windows_onefile.bat
```

The single `.exe` will be created inside:

```text
dist/
```

## Log File Location

The app writes logs to an OS-compatible app folder.

### Windows

```text
C:\Users\<User>\AppData\Local\NOLTOfficeAssistant\logs\app.log
```

### macOS

```text
/Users/<User>/Library/Application Support/NOLTOfficeAssistant/logs/app.log
```

### Linux

```text
/home/<user>/.local/share/NOLTOfficeAssistant/logs/app.log
```

## Important Note About PDF to Word

PDF-to-Word conversion works best with text-based PDFs.

Scanned PDFs or image-only PDFs may not convert into editable Word text unless OCR is added separately.