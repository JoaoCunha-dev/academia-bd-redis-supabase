"""
Camada de cache com Redis (padrão cache-aside).

Usos do Redis neste projeto:
  1. Cache do ranking de alunos (consulta agregada pesada na VIEW do Supabase),
     com TTL e invalidação sempre que os dados mudam.
  2. Contador de check-ins do dia (INCR), atualizado em tempo real.
"""
import json
import time
from datetime import date

import redis

from config import REDIS_URL

_cliente = None


def cliente():
    global _cliente
    if _cliente is None:
        _cliente = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _cliente


def redis_online():
    try:
        return bool(cliente().ping())
    except redis.RedisError:
        return False


def buscar_com_cache(chave, ttl_segundos, funcao_busca):
    """
    Tenta o Redis primeiro; se não houver (ou o Redis estiver fora), busca no
    Supabase e guarda o resultado. Retorna um dicionário com os dados e a origem.
    """
    inicio = time.perf_counter()
    redis_ok = True

    try:
        bruto = cliente().get(chave)
    except redis.RedisError:
        bruto, redis_ok = None, False

    if bruto is not None:
        dados = json.loads(bruto)
        ms = (time.perf_counter() - inicio) * 1000
        return {"dados": dados, "origem": "REDIS", "ms": round(ms, 1),
                "ttl": ttl_restante(chave), "redis_ok": True}

    dados = funcao_busca()

    if redis_ok:
        try:
            cliente().set(chave, json.dumps(dados, default=str), ex=ttl_segundos)
        except redis.RedisError:
            redis_ok = False

    ms = (time.perf_counter() - inicio) * 1000
    return {"dados": dados, "origem": "SUPABASE", "ms": round(ms, 1),
            "ttl": ttl_segundos if redis_ok else None, "redis_ok": redis_ok}


def ttl_restante(chave):
    try:
        t = cliente().ttl(chave)
        return t if t and t > 0 else None
    except redis.RedisError:
        return None


def invalidar(*chaves):
    """Apaga chaves do cache (chamado após cadastrar, editar, excluir ou check-in)."""
    try:
        cliente().delete(*chaves)
    except redis.RedisError:
        pass


def _chave_checkins_hoje():
    return f"checkins:hoje:{date.today().isoformat()}"


def incrementar_checkins_hoje():
    try:
        chave = _chave_checkins_hoje()
        valor = cliente().incr(chave)
        cliente().expire(chave, 60 * 60 * 48)
        return valor
    except redis.RedisError:
        return None


def checkins_hoje():
    try:
        valor = cliente().get(_chave_checkins_hoje())
        return int(valor) if valor else 0
    except redis.RedisError:
        return None
