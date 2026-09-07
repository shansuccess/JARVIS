import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

BANNER = r"""
  ___     _     ___   __   __  ___   ___ 
 | _ |   /_\   | _ \  \ \ / / |_ _| / __|
 |  _/  / _ \  |   /   \ V /   | |  \__ \
 |_|   /_/ \_\ |_|_\    \_/   |___| |___/
   JUST A RATHER VERY INTELLIGENT SYSTEM
        Stark Industries Mark VII
"""

def open_hud(url: str):
    time.sleep(1.2)
    print(f"\n[JARVIS] Engaging holographic HUD interface: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[JARVIS] Note: Could not auto-open browser: {e}")

def main():
    print(BANNER)
    from backend.config import settings
    
    url = f"http://{settings.host}:{settings.port}"
    print(f"[*] Starting J.A.R.V.I.S. Neural Hub on {url}...")
    print(f"[*] AI Mode: {'GEMINI ONLINE (' + settings.model + ')' if settings.gemini_api_key else 'LOCAL OFFLINE INTENT ENGINE'}")
    print("[*] Press Ctrl+C to shut down J.A.R.V.I.S.\n")

    # Launch browser in separate thread
    threading.Thread(target=open_hud, args=(url,), daemon=True).start()

    # Run Uvicorn server
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
