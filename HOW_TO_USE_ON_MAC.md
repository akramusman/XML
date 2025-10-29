# How to Use on Mac

## For Mac Users - Setup Instructions

### Step 1: Get the Files
- Share the entire folder (not just the .exe file) to your Mac
- Unzip the folder

### Step 2: Open Terminal
- Press `Cmd + Space` to open Spotlight
- Type "Terminal" and press Enter

### Step 3: Navigate to the Folder
In Terminal, type:
```bash
cd Downloads  # or wherever you unzipped the folder
cd XML  # or whatever the folder name is
```

### Step 4: Build the Mac App (optional if you downloaded the zip artifact)
If you already have `RekordboxGenerator-mac.zip` (from the provided release/artifact), just unzip and skip to Step 5.

Otherwise, to build locally run this command in Terminal:
```bash
bash build_app_mac.sh
```

This will:
- Install Python dependencies
- Create a Mac app in the `dist` folder

### Step 5: Run the App
After unzipping or building, run the app:
```bash
./dist/RekordboxGenerator.app/Contents/MacOS/RekordboxGenerator
```

Or find it in Finder and double-click to open.

If macOS shows “App is from an unidentified developer”: Right-click the app → Open → Open.

## Alternative: Run Without Building
If you don't want to build an app, you can run it directly:

```bash
# Make sure you have Python 3 installed
python3 rekordbox_generator.py
```

The GUI will open automatically.

## What Each File Does

- `rekordbox_generator.py` - The main Python script
- `build_app_mac.sh` - Script to build Mac app
- `tags.csv` - Your CSV file with track metadata
- `requirements.txt` - Python dependencies list
- `README_BUILD.md` - Detailed build instructions

## Using the Application

1. Double-click the app (or run from Terminal)
2. Select your CSV file with track tags
3. Choose your music folder where MP3 files are located
4. Click "Generate"
5. The CSV will be automatically cleaned
6. Import the generated XML into Rekordbox

## Important Notes

- The app will automatically find MP3 files by matching title/artist in your CSV
- The CSV file is cleaned after each run (headers kept, data removed)
- Make sure your MP3 files are in the selected music directory
- The generated XML will be named `generated_rekordbox.xml`

