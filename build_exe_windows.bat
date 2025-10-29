@echo off
echo Building Windows executable...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Install PyInstaller if not already installed
pip install pyinstaller

echo.
echo Building one-file executable...
pyinstaller --onefile --windowed --name="RekordboxGenerator" --icon=NONE --add-data "requirements.txt;." rekordbox_generator.py

echo.
echo Done! The executable is in the 'dist' folder.
echo.

