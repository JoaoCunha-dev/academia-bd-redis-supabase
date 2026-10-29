
from cache import buscar_com_cache, invalidar, incrementar_checkins_hoje
from config import CACHE_TTL
from db import get_connection

CHAVE_RANKING = "academia:ranking"


def listar_planos():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("select id, nome, valor from planos order by id")
        return cur.fetchall()


def ranking(limite=50):
    """Ranking por check-ins vindo da VIEW vw_resumo_alunos (cacheado no Redis)."""
    def consulta():
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """select id, nome, plano, total_checkins, ultimo_checkin
                   from vw_resumo_alunos
                   order by total_checkins desc, nome
                   limit %s""",
                (limite,),
            )
            return [list(l) for l in cur.fetchall()]

    return buscar_com_cache(f"{CHAVE_RANKING}:{limite}", CACHE_TTL, consulta)


def listar_alunos(busca="", limite=100):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """select a.id, a.nome, a.email, coalesce(p.nome, '-'), a.ativo
               from alunos a left join planos p on p.id = a.plano_id
               where a.nome ilike %s or a.email ilike %s
               order by a.id desc
               limit %s""",
            (f"%{busca}%", f"%{busca}%", limite),
        )
        return cur.fetchall()


def total_checkins(aluno_id):
    """Chama a FUNCTION fn_total_checkins do banco."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("select fn_total_checkins(%s)", (aluno_id,))
        return cur.fetchone()[0]


def _invalidar_ranking():
    from cache import cliente
    try:
        for chave in cliente().scan_iter(f"{CHAVE_RANKING}:*"):
            cliente().delete(chave)
    except Exception:
        pass


def cadastrar_aluno(nome, email, plano_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "insert into alunos (nome, email, plano_id) values (%s, %s, %s)",
            (nome, email, plano_id),
        )
    _invalidar_ranking()


def atualizar_aluno(aluno_id, nome, email, plano_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "update alunos set nome=%s, email=%s, plano_id=%s where id=%s",
            (nome, email, plano_id, aluno_id),
        )
    _invalidar_ranking()


def excluir_aluno(aluno_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("delete from alunos where id=%s", (aluno_id,))
    _invalidar_ranking()


def registrar_checkin(aluno_id):
    """Chama a PROCEDURE sp_registrar_checkin e atualiza o contador no Redis."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("call sp_registrar_checkin(%s)", (aluno_id,))
    _invalidar_ranking()
    return incrementar_checkins_hoje()
