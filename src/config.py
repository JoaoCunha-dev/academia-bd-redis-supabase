
import os
from pathlib import Path
from dotenv import load_dotenv

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent

for caminho in (RAIZ / ".env", AQUI / ".env"):
    if caminho.exists():
        load_dotenv(caminho, encoding="utf-8-sig")

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))
