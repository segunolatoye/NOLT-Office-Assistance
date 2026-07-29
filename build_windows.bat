@echo off
echo Building PDF Image Toolkit 1.0.0v as folder app...

call .\.venv\Scripts\activate
pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name "NOLT_OA_1.0.0v" ^
  --icon "favicon.ico" ^
  --add-data "favicon.ico;." ^
  main.py

echo.
echo Build complete.
echo Check the dist folder.
pause