-- =====================================================
-- Academia BD - Estrutura (tabelas, view, function, procedure)
-- Compatível com PostgreSQL / Supabase. Pode ser rodado várias vezes.
-- =====================================================

create table if not exists planos (
    id    serial primary key,
    nome  text not null unique,
    valor numeric(10,2) not null check (valor >= 0)
);

create table if not exists alunos (
    id        serial primary key,
    nome      text not null,
    email     text not null unique,
    plano_id  int references planos(id),
    ativo     boolean not null default true,
    criado_em timestamptz not null default now()
);

create table if not exists checkins (
    id        bigserial primary key,
    aluno_id  int not null references alunos(id) on delete cascade,
    data_hora timestamptz not null default now()
);

create index if not exists idx_checkins_aluno on checkins(aluno_id);

-- VIEW: resumo por aluno (consulta agregada pesada, é ela que vai para o Redis)
create or replace view vw_resumo_alunos as
select a.id,
       a.nome,
       a.email,
       p.nome as plano,
       count(c.id)      as total_checkins,
       max(c.data_hora) as ultimo_checkin
from alunos a
left join planos p   on p.id = a.plano_id
left join checkins c on c.aluno_id = a.id
where a.ativo
group by a.id, a.nome, a.email, p.nome;

-- FUNCTION: total de check-ins de um aluno
create or replace function fn_total_checkins(p_aluno_id int)
returns bigint
language sql
stable
as $$
    select count(*) from checkins where aluno_id = p_aluno_id;
$$;

-- PROCEDURE: registra um check-in validando se o aluno existe e está ativo
create or replace procedure sp_registrar_checkin(p_aluno_id int)
language plpgsql
as $$
begin
    if not exists (select 1 from alunos where id = p_aluno_id and ativo) then
        raise exception 'Aluno % não existe ou está inativo', p_aluno_id;
    end if;
    insert into checkins (aluno_id) values (p_aluno_id);
end;
$$;
