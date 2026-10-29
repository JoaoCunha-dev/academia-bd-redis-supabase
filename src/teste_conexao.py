
from cache import redis_online
from db import get_connection

try:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("select version()")
        print("Supabase OK:", cur.fetchone()[0])
except Exception as e:
    print("ERRO no Supabase:", e)

print("Redis OK" if redis_online() else "Redis OFFLINE (suba o Docker ou confira REDIS_URL)")
