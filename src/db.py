"""Conexão com o PostgreSQL do Supabase."""
import psycopg2
from config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não foi encontrada. Crie o arquivo .env (veja .env.example)."
        )
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)
