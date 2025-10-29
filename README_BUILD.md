# Rekordbox XML Generator - Build Instructions

## Building the Executable/App

### For Windows:
1. Run `build_exe_windows.bat` in PowerShell or Command Prompt
2. The executable will be created in the `dist` folder as `RekordboxGenerator.exe`

### For macOS:
1. Open Terminal
2. Navigate to this directory
3. Run: `bash build_app_mac.sh`
4. The app will be created in the `dist` folder as `RekordboxGenerator`

## Using the Built Application

### Windows:
- Run `RekordboxGenerator.exe`
- Select your CSV file with tags
- Click "Generate" to create the Rekordbox XML
- Import the generated XML into Rekordbox

### macOS:
- Run `RekordboxGenerator.app` (double-click in Finder)
- Select your CSV file with tags
- Click "Generate" to create the Rekordbox XML
- Import the generated XML into Rekordbox

## CSV Format

Your CSV file should have these headers (case-insensitive):
- composer
- remixer
- original artist
- mix name
- label
- year
- genre
- comments
- track title
- artist

## Notes:
- The CSV file will be automatically cleaned after processing (headers kept, data removed)
- MP3 files should be in the specified music directory
- The app will automatically find matching MP3 files based on title and artist

