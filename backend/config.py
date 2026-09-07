import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Load .env file
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

class Settings:
    def __init__(self):
        self.reload()

    def reload(self):
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.default_city = os.getenv("DEFAULT_CITY", "London")
        self.voice_persona = os.getenv("VOICE_PERSONA", "indian_boy")

    def update_gemini_key(self, new_key: str):
        self.gemini_api_key = new_key.strip()
        self._persist_env_var("GEMINI_API_KEY", self.gemini_api_key)
        self.reload()

    def update_persona(self, new_persona: str):
        self.voice_persona = new_persona.strip()
        self._persist_env_var("VOICE_PERSONA", self.voice_persona)
        self.reload()

    def _persist_env_var(self, key: str, value: str):
        env_lines = []
        key_found = False
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        env_lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        env_lines.append(line)
        if not key_found:
            env_lines.append(f"{key}={value}\n")

        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(env_lines)

settings = Settings()
