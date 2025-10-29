"""
Rekordbox XML Generator (rekordbox_generator.py)

What it does:
- Reads a sample Rekordbox XML (optional — used to preserve structure or playlist metadata).
- Reads a CSV of new tags (fields described below).
- Scans a default music folder to try to find matching mp3 files (or uses a filename pattern based on title/artist).
- Builds a Rekordbox-compatible XML COLLECTION with TRACK entries for import into Rekordbox.
- Outputs a Rekordbox XML file and an XSD (XML Schema) that describes the subset used.
- Provides a simple Tkinter UI so a user can select: sample XML (optional), tags CSV, then click Generate.

Dependencies:
- Python 3.8+
- mutagen (for reading existing mp3 tags; optional but recommended)

Install dependency:
    pip install mutagen

Create an executable (Mac) suggestions:
- Run directly: python3 rekordbox_generator.py
- Or use PyInstaller: pip install pyinstaller
    pyinstaller --onefile --windowed rekordbox_generator.py
  Note: on macOS you may prefer py2app for producing a .app bundle.

CSV format (header required). Header names must match one of these keys (case-insensitive):
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

Each row corresponds to one track.

Default location (used as base path for all files):
- Change DEFAULT_MUSIC_DIR variable, or use the UI to change.

Behavior when locating files:
1. Try to find an exact matching file in DEFAULT_MUSIC_DIR recursively by reading ID3 tags (Artist + Title).
2. If not found, attempt to find by filename patterns (artist - title).mp3 (and some fuzzy variants).
3. If not found, produce a LOCATION URI based on default dir + sanitized filename "{artist} - {title}.mp3"; that works for Rekordbox import if the files exist at that location.

Outputs:
- generated_rekordbox.xml
- rekordbox_subset.xsd

-------------------------
Implementation follows.
"""

import os
import sys
import csv
import urllib.parse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Callable, List, Dict, Optional

try:
    from mutagen.easyid3 import EasyID3
    MUTAGEN_AVAILABLE = True
except Exception:
    MUTAGEN_AVAILABLE = False

# ---------- Configuration ----------
DEFAULT_MUSIC_DIR = r'C:\Users\DELL\XML'  # change if needed
OUTPUT_XML = 'generated_rekordbox.xml'
OUTPUT_XSD = 'rekordbox_subset.xsd'

# Allowed CSV headers mapping (lowercase) -> internal field name
FIELD_MAP: Dict[str, str] = {
    'composer': 'COMPOSER',
    'remixer': 'REMIXER',
    'original artist': 'ORIGINAL_ARTIST',
    'original_artist': 'ORIGINAL_ARTIST',
    'mix name': 'MIXNAME',
    'mix_name': 'MIXNAME',
    'label': 'LABEL',
    'year': 'YEAR',
    'genre': 'GENRE',
    'comments': 'COMMENTS',
    'track title': 'TITLE',
    'track_title': 'TITLE',
    'title': 'TITLE',
    'artist': 'ARTIST'
}

# XSD describing the subset of Rekordbox XML used by this generator
REKORDBOX_XSD = r'''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           elementFormDefault="qualified">
  <xs:element name="DJ_PLAYLISTS">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="COLLECTION">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="TRACK" maxOccurs="unbounded">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="PRIMARYKEY" minOccurs="0"/>
                    <xs:element name="LOCATION" type="xs:string" minOccurs="1"/>
                    <xs:element name="TITLE" type="xs:string" minOccurs="0"/>
                    <xs:element name="ARTIST" type="xs:string" minOccurs="0"/>
                    <xs:element name="ALBUM" type="xs:string" minOccurs="0"/>
                    <xs:element name="LABEL" type="xs:string" minOccurs="0"/>
                    <xs:element name="COMPOSER" type="xs:string" minOccurs="0"/>
                    <xs:element name="REMIXER" type="xs:string" minOccurs="0"/>
                    <xs:element name="ORIGINAL_ARTIST" type="xs:string" minOccurs="0"/>
                    <xs:element name="MIXNAME" type="xs:string" minOccurs="0"/>
                    <xs:element name="YEAR" type="xs:string" minOccurs="0"/>
                    <xs:element name="GENRE" type="xs:string" minOccurs="0"/>
                    <xs:element name="COMMENTS" type="xs:string" minOccurs="0"/>
                  </xs:sequence>
                  <xs:attribute name="TrackID" type="xs:integer" use="optional"/>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="Version" type="xs:string" use="optional"/>
    </xs:complexType>
  </xs:element>
 </xs:schema>
'''

# ---------- Utility functions ----------

def prettify_xml(elem: ET.Element) -> bytes:
    raw = ET.tostring(elem, encoding='utf-8')
    parsed = minidom.parseString(raw)
    return parsed.toprettyxml(indent='  ', encoding='utf-8')


def to_file_uri(path: str) -> str:
    # Rekordbox expects file://localhost/... format
    p = Path(path).expanduser().resolve()
    
    # Convert Windows path to Unix-style for the URI
    if sys.platform == 'win32':
        # C:\Users\DELL\XML\track.mp3 -> C:/Users/DELL/XML/track.mp3
        unix_path = str(p).replace('\\', '/')
        # file://localhost/C:/Users/DELL/XML/track.mp3
        return f"file://localhost/{unix_path}"
    else:
        # macOS/Linux: file://localhost/Users/...
        return f"file://localhost{str(p)}"


def sanitize_filename(s: str) -> str:
    s = s.strip()
    bad = '<>:"/\\|?*'
    for c in bad:
        s = s.replace(c, '_')
    return s


def find_file_by_tags(default_dir: str, title: str, artist: str, log_func: Callable[[str], None] = print) -> Optional[str]:
    """Try to find an existing file in default_dir that matches title+artist.
       Returns absolute path or None.
    """
    title_l = (title or '').lower().strip()
    artist_l = (artist or '').lower().strip()

    # First pass: filename matching
    for root, dirs, files in os.walk(default_dir):
        for f in files:
            if not f.lower().endswith(('.mp3', '.m4a', '.wav', '.flac')):
                continue
            name = os.path.splitext(f)[0].lower()
            if title_l and artist_l and title_l in name and artist_l in name:
                candidate = os.path.join(root, f)
                log_func(f'Found by filename: {candidate}')
                return candidate

    # Second pass: read tags (if mutagen available)
    if MUTAGEN_AVAILABLE:
        for root, dirs, files in os.walk(default_dir):
            for f in files:
                if not f.lower().endswith(('.mp3', '.m4a')):
                    continue
                candidate = os.path.join(root, f)
                try:
                    tags = EasyID3(candidate)
                    t = ' '.join(tags.get('title', [])).lower()
                    a = ' '.join(tags.get('artist', [])).lower()
                    if title_l and title_l in t and artist_l and artist_l in a:
                        log_func(f'Found by ID3: {candidate}')
                        return candidate
                except Exception:
                    # not all files have ID3; continue
                    pass

    # Third: common filename pattern
    if artist and title:
        guess = os.path.join(default_dir, f"{sanitize_filename(artist)} - {sanitize_filename(title)}.mp3")
        if os.path.exists(guess):
            log_func(f'Found by guess exact path: {guess}')
            return guess

    return None

# ---------- XML builder ----------

def build_rekordbox_xml(tracks: List[Dict[str, Optional[str]]], sample_xml_root: Optional[ET.Element] = None) -> ET.Element:
    # Create root
    root = ET.Element('DJ_PLAYLISTS')
    root.set('Version', '1.0.0')
    
    # Add PRODUCT element (standard Rekordbox format)
    product = ET.SubElement(root, 'PRODUCT')
    product.set('Name', 'rekordbox')
    product.set('Version', '7.2.3')
    product.set('Company', 'AlphaTheta')

    # If sample XML provided, try to copy playlists and other nodes (simple copy)
    # But keep our own COLLECTION built from 'tracks'
    if sample_xml_root is not None:
        # Copy all children except COLLECTION
        for child in list(sample_xml_root):
            if child.tag.upper() == 'COLLECTION':
                continue
            root.append(child)

    # COLLECTION
    collection = ET.SubElement(root, 'COLLECTION')
    collection.set('Entries', str(len(tracks)))
    
    track_id = 1
    for t in tracks:
        tr = ET.SubElement(collection, 'TRACK')
        tr.set('TrackID', str(track_id))

        # Set attributes from track data
        if t.get('TITLE'):
            tr.set('Name', str(t['TITLE']))
        if t.get('ARTIST'):
            tr.set('Artist', str(t['ARTIST']))
        if t.get('ALBUM'):
            tr.set('Album', str(t['ALBUM']))
        if t.get('COMPOSER'):
            tr.set('Composer', str(t['COMPOSER']))
        if t.get('LABEL'):
            tr.set('Label', str(t['LABEL']))
        if t.get('GENRE'):
            tr.set('Genre', str(t['GENRE']))
        if t.get('YEAR'):
            tr.set('Year', str(t['YEAR']))
        if t.get('REMIXER'):
            tr.set('Remixer', str(t['REMIXER']))
        if t.get('MIXNAME'):
            tr.set('Mix', str(t['MIXNAME']))
        if t.get('COMMENTS'):
            tr.set('Comments', str(t['COMMENTS']))
        
        # Default attributes that Rekordbox expects
        tr.set('Grouping', '')
        tr.set('DiscNumber', '0')
        tr.set('TrackNumber', '0')
        tr.set('AverageBpm', '0.00')
        tr.set('DateAdded', '')
        tr.set('SampleRate', '44100')
        tr.set('PlayCount', '0')
        tr.set('Rating', '0')
        tr.set('Tonality', '')
        
        # Use actual file info if available
        tr.set('Kind', t.get('KIND', 'Unknown Format'))
        tr.set('Size', t.get('FILE_SIZE', '0'))
        tr.set('TotalTime', t.get('TOTAL_TIME', '0'))
        tr.set('BitRate', t.get('BITRATE', '0'))
        
        # LOCATION attribute (most important!)
        loc = t.get('LOCATION', '')
        tr.set('Location', loc)

        track_id += 1

    return root

# ---------- CSV parsing and track assembly ----------

def parse_csv_tags(csv_path: str, log_func: Callable[[str], None] = print) -> List[Dict[str, Optional[str]]]:
    tracks: List[Dict[str, Optional[str]]] = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError('CSV has no header row')
        headers = [h.lower().strip() for h in reader.fieldnames]
        # Validate headers
        mapped_headers: Dict[str, str] = {}
        for h in headers:
            if h in FIELD_MAP:
                mapped_headers[h] = FIELD_MAP[h]
            else:
                log_func(f'Warning: CSV header "{h}" not recognized and will be ignored')

        for row in reader:
            out: Dict[str, Optional[str]] = {v: None for v in FIELD_MAP.values()}
            for raw_h, mapped in mapped_headers.items():
                value = row.get(raw_h)
                out[mapped] = (value or '').strip() or None
            tracks.append(out)
    return tracks

# ---------- Putting it together ----------

def get_audio_info(file_path: str) -> Dict[str, str]:
    """Get audio file information like size, duration, etc."""
    info = {
        'Size': '0',
        'TotalTime': '0',
        'BitRate': '0',
        'Kind': 'Unknown Format'
    }
    
    if not os.path.exists(file_path):
        return info
    
    # Get file size
    try:
        file_size = os.path.getsize(file_path)
        info['Size'] = str(file_size)
    except Exception:
        pass
    
    # Try to get audio info from mutagen if available
    if MUTAGEN_AVAILABLE:
        try:
            from mutagen import File as MutagenFile
            from mutagen.mp3 import MP3
            
            # Try MP3 specifically
            try:
                mp3_file = MP3(file_path)
                if mp3_file:
                    info['Kind'] = 'MP3 File'
                    if hasattr(mp3_file, 'info'):
                        if hasattr(mp3_file.info, 'length'):
                            duration = int(mp3_file.info.length)
                            info['TotalTime'] = str(duration)
                        if hasattr(mp3_file.info, 'bitrate'):
                            bitrate = mp3_file.info.bitrate
                            if bitrate:
                                info['BitRate'] = str(bitrate)
            except Exception:
                pass
            
            # Fallback to generic mutagen File
            if info['Kind'] == 'Unknown Format':
                try:
                    audio_file = MutagenFile(file_path)
                    if audio_file is not None:
                        # Get duration
                        if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                            duration = int(audio_file.info.length)
                            info['TotalTime'] = str(duration)
                        
                        # Get bitrate
                        if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'bitrate'):
                            bitrate = audio_file.info.bitrate
                            if bitrate:
                                info['BitRate'] = str(bitrate)
                        
                        # Get file type
                        mime_type = str(audio_file.mime).lower()
                        if 'mp3' in mime_type or 'mpeg' in mime_type:
                            info['Kind'] = 'MP3 File'
                        elif 'm4a' in mime_type or 'mp4' in mime_type:
                            info['Kind'] = 'MPEG-4 audio file'
                        elif 'wav' in mime_type:
                            info['Kind'] = 'WAVE File'
                        elif 'flac' in mime_type:
                            info['Kind'] = 'FLAC File'
                except Exception as e:
                    pass
        except Exception:
            pass
    
    # Fallback: try to detect by file extension
    if info['Kind'] == 'Unknown Format':
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp3':
            info['Kind'] = 'MP3 File'
        elif ext == '.m4a':
            info['Kind'] = 'MPEG-4 audio file'
        elif ext == '.wav':
            info['Kind'] = 'WAVE File'
        elif ext == '.flac':
            info['Kind'] = 'FLAC File'
    
    return info


def generate(xml_sample_path: Optional[str], csv_path: str, default_dir: str, out_xml: str, out_xsd: str, log_func: Callable[[str], None] = print) -> None:
    log_func(f'Loading CSV: {csv_path}')
    tracks = parse_csv_tags(csv_path, log_func=log_func)

    sample_root: Optional[ET.Element] = None
    if xml_sample_path:
        try:
            sample_tree = ET.parse(xml_sample_path)
            sample_root = sample_tree.getroot()
            log_func(f'Loaded sample Rekordbox XML from {xml_sample_path}')
        except Exception as e:
            log_func(f'Could not parse sample XML: {e}')
            sample_root = None

    # For each track, resolve LOCATION and get file info
    for t in tracks:
        title = t.get('TITLE')
        artist = t.get('ARTIST')
        found: Optional[str] = None
        try:
            found = find_file_by_tags(default_dir, title or '', artist or '', log_func=log_func)
        except Exception as e:
            log_func('Error while searching files: ' + str(e))

        if found:
            t['LOCATION'] = to_file_uri(found)
            t['FILE_PATH'] = found
        else:
            # fallback path based on filename pattern
            guessed = os.path.join(default_dir, f"{sanitize_filename(artist or 'Unknown')} - {sanitize_filename(title or 'Unknown')}.mp3")
            t['LOCATION'] = to_file_uri(guessed)
            t['FILE_PATH'] = guessed if os.path.exists(guessed) else None
            log_func(f'Using guessed location: {guessed}')
        
        # Get audio file info
        file_path = t.get('FILE_PATH')
        if file_path and os.path.exists(file_path):
            audio_info = get_audio_info(file_path)
            t['FILE_SIZE'] = audio_info['Size']
            t['TOTAL_TIME'] = audio_info['TotalTime']
            t['BITRATE'] = audio_info['BitRate']
            t['KIND'] = audio_info['Kind']
        else:
            t['FILE_SIZE'] = '0'
            t['TOTAL_TIME'] = '0'
            t['BITRATE'] = '0'
            t['KIND'] = 'Unknown Format'

    # Build XML
    root = build_rekordbox_xml(tracks, sample_root)
    xml_bytes = prettify_xml(root)
    with open(out_xml, 'wb') as f:
        f.write(xml_bytes)
    log_func(f'Wrote XML: {out_xml}')

    # Write XSD
    with open(out_xsd, 'w', encoding='utf-8') as f:
        f.write(REKORDBOX_XSD)
    log_func(f'Wrote XSD: {out_xsd}')
    
    # Clean CSV - clear the data but keep headers
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        if headers:
            # Write back just the headers
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
            log_func(f'Cleaned CSV file: {csv_path}')
    except Exception as e:
        log_func(f'Could not clean CSV file: {e}')


# ---------- UI ----------

class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Rekordbox XML Generator')

        # State
        self.sample_xml_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.music_dir = tk.StringVar(value=DEFAULT_MUSIC_DIR)

        # Layout
        frm = tk.Frame(root)
        frm.pack(fill='both', expand=True, padx=10, pady=10)

        # Sample XML
        tk.Label(frm, text='Sample Rekordbox XML (optional):').grid(row=0, column=0, sticky='w')
        tk.Entry(frm, textvariable=self.sample_xml_path, width=60).grid(row=0, column=1, sticky='we', padx=(6, 6))
        tk.Button(frm, text='Browse', command=self.browse_sample_xml).grid(row=0, column=2)

        # CSV
        tk.Label(frm, text='Tags CSV:').grid(row=1, column=0, sticky='w', pady=(6, 0))
        tk.Entry(frm, textvariable=self.csv_path, width=60).grid(row=1, column=1, sticky='we', padx=(6, 6), pady=(6, 0))
        tk.Button(frm, text='Browse', command=self.browse_csv).grid(row=1, column=2, pady=(6, 0))

        # Music dir
        tk.Label(frm, text='Default music directory:').grid(row=2, column=0, sticky='w', pady=(6, 0))
        tk.Entry(frm, textvariable=self.music_dir, width=60).grid(row=2, column=1, sticky='we', padx=(6, 6), pady=(6, 0))
        tk.Button(frm, text='Browse', command=self.browse_music_dir).grid(row=2, column=2, pady=(6, 0))

        # Actions
        tk.Button(frm, text='Generate', command=self.on_generate).grid(row=3, column=0, pady=(10, 6), sticky='w')
        tk.Button(frm, text='Quit', command=root.quit).grid(row=3, column=2, pady=(10, 6), sticky='e')

        # Log
        tk.Label(frm, text='Log:').grid(row=4, column=0, sticky='nw')
        self.log = scrolledtext.ScrolledText(frm, width=80, height=18, state='disabled')
        self.log.grid(row=4, column=1, columnspan=2, sticky='nsew', pady=(6, 0))

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(4, weight=1)

    def append_log(self, text: str) -> None:
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def browse_sample_xml(self) -> None:
        path = filedialog.askopenfilename(title='Select sample Rekordbox XML', filetypes=[('XML files', '*.xml'), ('All files', '*.*')])
        if path:
            self.sample_xml_path.set(path)

    def browse_csv(self) -> None:
        path = filedialog.askopenfilename(title='Select tags CSV', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
        if path:
            self.csv_path.set(path)

    def browse_music_dir(self) -> None:
        path = filedialog.askdirectory(title='Select music root directory')
        if path:
            self.music_dir.set(path)

    def on_generate(self) -> None:
        csv_path = self.csv_path.get().strip()
        if not csv_path:
            messagebox.showerror('Missing CSV', 'Please select a CSV file.')
            return
        sample_xml = self.sample_xml_path.get().strip() or None
        music_dir = self.music_dir.get().strip() or os.getcwd()

        def logger(msg: str) -> None:
            self.append_log(msg)

        try:
            logger('Starting generation...')
            generate(sample_xml, csv_path, music_dir, OUTPUT_XML, OUTPUT_XSD, log_func=logger)
            messagebox.showinfo('Success', f'Generated:\n{OUTPUT_XML}\n{OUTPUT_XSD}')
            logger('Done.')
        except Exception as e:
            logger(f'Error: {e}')
            messagebox.showerror('Error', str(e))


def main(argv: List[str]) -> int:
    if len(argv) > 1:
        # CLI mode
        import argparse
        parser = argparse.ArgumentParser(description='Generate Rekordbox XML from CSV tags.')
        parser.add_argument('--sample-xml', type=str, default=None, help='Optional sample Rekordbox XML to preserve playlists/structure')
        parser.add_argument('--csv', type=str, required=True, help='CSV file with tags')
        parser.add_argument('--music-dir', type=str, default=DEFAULT_MUSIC_DIR, help='Root music directory to search')
        parser.add_argument('--out-xml', type=str, default=OUTPUT_XML, help='Output Rekordbox XML path')
        parser.add_argument('--out-xsd', type=str, default=OUTPUT_XSD, help='Output XSD path')
        args = parser.parse_args(argv[1:])

        def logger(msg: str) -> None:
            print(msg)

        generate(args.sample_xml, args.csv, args.music_dir, args.out_xml, args.out_xsd, log_func=logger)
        print('Done.')
        return 0

    # GUI mode
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))


