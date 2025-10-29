# What to Share with Mac Users

## DO ZIP AND SHARE:
✅ rekordbox_generator.py - Main script
✅ build_app_mac.sh - Mac build script
✅ HOW_TO_USE_ON_MAC.md - Setup instructions
✅ requirements.txt - Dependencies
✅ README_BUILD.md - Build instructions
✅ tags.csv - Example CSV template
✅ sample_rekordbox.xml - Sample Rekordbox XML (optional)

## DON'T INCLUDE:
❌ dist/ folder - Windows executables won't work on Mac
❌ build/ folder - Build artifacts
❌ venv/ folder - Virtual environment (too large)
❌ *.exe files - Windows only
❌ __pycache__/ - Python cache

## Instructions for Creating the Zip:

### On Windows:
1. Select these files/folders:
   - rekordbox_generator.py
   - build_app_mac.sh
   - HOW_TO_USE_ON_MAC.md
   - README_BUILD.md
   - requirements.txt
   - tags.csv (your template)
   - sample_rekordbox.xml

2. Right-click → "Send to" → "Compressed (zipped) folder"

3. Share the zip file

### The Mac User Should:
1. Unzip the file
2. Open Terminal
3. Go to the folder: `cd ~/Downloads/XML`
4. Run: `bash build_app_mac.sh`
5. Use the app that gets created

## Quick Start for Mac Users:

After unzipping, run:
```bash
cd ~/Downloads/XML  # adjust path if needed
bash build_app_mac.sh
```

Then use the app from the dist folder or run:
```bash
python3 rekordbox_generator.py
```

