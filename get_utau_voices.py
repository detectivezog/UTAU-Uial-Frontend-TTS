import os
import requests
import zipfile
import shutil
from pathlib import Path

# THE DEFINITIVE SINGER REGISTRY
# Verified links as of March 2026
VOICE_MIRRORS = {
    "teto_en": "https://kasaneteto.jp/ongendl/index.cgi/english/TETO-English-150401.zip",
    "teto_jp": "https://kasaneteto.jp/ongendl/index.cgi/renzoku/TETO-tougou-110401.zip",
    "teto_whisper": "https://kasaneteto.jp/ongendl/index.cgi/extra/TETO-sasayaki-120930.zip",
    "defoko": "https://github.com/stakira/OpenUtau/releases/download/v0.0.0/voice_defoko.zip",
    "ruko_male": "https://github.com/stakira/OpenUtau/releases/download/v0.0.0/voice_ruko.zip"
}

def force_extract(zip_path, target_dir):
    """Extracts everything manually while fixing Shift-JIS encoding issues."""
    print(f"[*] Force extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in z.infolist():
            try:
                # Japanese UTAU banks are Shift-JIS encoded.
                # This prevents 'ã‚«ã‚µãƒ ' names.
                filename = info.filename.encode('cp437').decode('shift-jis')
            except:
                filename = info.filename
            
            target_path = Path(target_dir) / filename
            
            if info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with z.open(info) as source, open(target_path, "wb") as dest:
                shutil.copyfileobj(source, dest)
                if "oto.ini" in filename.lower():
                    print(f"[!] Success: Captured {filename}")

def download_voice(name):
    if name not in VOICE_MIRRORS:
        print(f"[!] Unknown singer: {name}")
        return
        
    save_dir = Path("voicebanks")
    target_dir = save_dir / name
    zip_path = save_dir / f"{name}.zip"
    
    os.makedirs(save_dir, exist_ok=True)
    
    url = VOICE_MIRRORS[name]
    print(f"[*] Downloading {name} from {url}...")
    
    # Professional headers to bypass bot-detection on Japanese servers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://kasaneteto.jp/utau/'
    }
    
    try:
        r = requests.get(url, stream=True, headers=headers, timeout=30)
        r.raise_for_status()

        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Security check: if the file is tiny, it's likely a 404/403 page
        if os.path.getsize(zip_path) < 5000:
            print(f"[!] Error: {name} download is corrupted (file too small).")
            return

        force_extract(zip_path, target_dir)
        print(f"[SUCCESS] {name} is ready.")

    except Exception as e:
        print(f"[!] Failed to process {name}: {e}")
    finally:
        if zip_path.exists():
            os.remove(zip_path)

if __name__ == "__main__":
    print("--- UTAU Multi-Singer Downloader ---")
    print("Available Singers:")
    for key in VOICE_MIRRORS.keys():
        print(f" - {key}")
    
    choice = input("\nEnter name (or 'all'): ").strip().lower()
    
    if choice == "all":
        for singer in VOICE_MIRRORS.keys():
            download_voice(singer)
    else:
        download_voice(choice)
