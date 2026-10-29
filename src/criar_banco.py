"""
Cria as tabelas, view, function e procedure no Supabase e (opcionalmente)
insere dados de teste.

Uso:
    python src/criar_banco.py              # cria estrutura + dados de teste
    python src/criar_banco.py --sem-dados  # só a estrutura
"""
import sys
from pathlib import Path

from db import get_connection

SQL = Path(__file__).resolve().parent.parent / "sql"


def rodar(arquivo):
    print(f"Executando {arquivo.name} ...")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(arquivo.read_text(encoding="utf-8"))


if __name__ == "__main__":
    rodar(SQL / "01_schema.sql")
    if "--sem-dados" not in sys.argv:
        rodar(SQL / "02_seed.sql")
    print("Banco pronto!")
