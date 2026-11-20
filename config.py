from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(__import__('os').environ.get("REXA_DB_PATH", str(ROOT / "rexa.db")).strip()).expanduser()
API_BASE_URL = __import__('os').environ.get("REXA_API_BASE", "https://api.openai.com/v1").strip()
API_KEY = __import__('os').environ.get("REXA_API_KEY", "").strip()
FAST_MODEL = __import__('os').environ.get("REXA_FAST_MODEL", "gpt-4o-mini").strip()
DEEP_REASONING_MODEL = __import__('os').environ.get("REXA_DEEP_MODEL", "gpt-4o").strip()
AGENT_NAME = __import__('os').environ.get("REXA_AGENT_NAME", "Rexa").strip() or "Rexa"
OWNER_NAME = __import__('os').environ.get("REXA_OWNER_NAME", "Pengguna").strip() or "Pengguna"
OWNER_PHONE = __import__('os').environ.get("REXA_OWNER_PHONE", "").strip()
SYSTEM_PROMPT = f"Kamu adalah {AGENT_NAME}, asisten AI untuk {OWNER_NAME}. Jawab akurat, jelas, dan sesuai permintaan pengguna."
