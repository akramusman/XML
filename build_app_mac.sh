#!/bin/bash

echo "Building macOS application..."
echo ""

# Activate virtual environment
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate

# Install mutagen if not already installed
pip install mutagen pyinstaller

echo ""
echo "Building macOS application bundle..."
echo ""

# Build one-file executable
pyinstaller --onefile --windowed \
    --name="RekordboxGenerator" \
    --icon=NONE \
    --add-data "requirements.txt:." \
    rekordbox_generator.py

echo ""
echo ""
echo "Zipping app for distribution (release/RekordboxGenerator-mac.zip)..."
mkdir -p release
if [ -d "dist/RekordboxGenerator.app" ]; then
  ditto -c -k --sequesterRsrc --keepParent "dist/RekordboxGenerator.app" "release/RekordboxGenerator-mac.zip"
  echo "Created release/RekordboxGenerator-mac.zip"
else
  echo "Note: .app not found. If a CLI binary was produced, it will be in dist/."
fi

echo "Done! The app is in the 'dist' folder, and a zip is in 'release/'."
echo ""

