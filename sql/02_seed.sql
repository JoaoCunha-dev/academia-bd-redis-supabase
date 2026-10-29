-- =====================================================
-- Dados de teste (só insere se a tabela de alunos estiver vazia)
-- 20.000 alunos e 200.000 check-ins, para o cache fazer diferença real.
-- =====================================================

insert into planos (nome, valor) values
    ('Mensal', 99.90),
    ('Trimestral', 269.90),
    ('Anual', 899.90)
on conflict (nome) do nothing;

do $$
begin
    if not exists (select 1 from alunos) then
        insert into alunos (nome, email, plano_id)
        select 'Aluno ' || g,
               'aluno' || g || '@teste.com',
               (select id from planos order by id offset (g % 3) limit 1)
        from generate_series(1, 20000) g;

        insert into checkins (aluno_id, data_hora)
        select (select min(id) from alunos) + floor(random() * 20000)::int,
               now() - (random() * interval '90 days')
        from generate_series(1, 200000);
    end if;
end;
$$;

analyze;
