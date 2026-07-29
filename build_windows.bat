@echo off
echo Building PDF Image Toolkit 1.0.0v as folder app...

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name "PDF Image Toolkit 1.0.0v" ^
  main.py

echo.
echo Build complete.
echo Check the dist folder.
pause