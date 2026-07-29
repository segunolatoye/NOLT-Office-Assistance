@echo off
echo Building PDF Image Toolkit 1.0.0v as single EXE...

pyinstaller ^
  --noconfirm ^
  --windowed ^
  --onefile ^
  --name "PDF Image Toolkit 1.0.0v" ^
  main.py

echo.
echo Build complete.
echo Check the dist folder.
pause