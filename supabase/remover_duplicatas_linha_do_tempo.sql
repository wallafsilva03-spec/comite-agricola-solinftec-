-- Execute no SQL Editor do Supabase para remover linhas 100% duplicadas
-- (mesmo regional, unidade, frente, equipamento, operador, data, horários,
-- operação, fazenda, talhão, horímetros e velocidade) da tabela linha_do_tempo.
-- Mantém apenas 1 linha de cada grupo de duplicatas (a de menor id).

-- 1) Confira antes quantas linhas seriam removidas (não apaga nada ainda):
with duplicadas as (
  select id,
    row_number() over (
      partition by
        regional, unidade, frente, codigo_equipamento, equipamento,
        codigo_operador, operador, data, hora_inicial, hora_final,
        codigo_operacao, atividade, classificacao, codigo_fazenda,
        codigo_zona, codigo_talhao, fazenda,
        horimetro_inicial, horimetro_final, horimetro_secundario, velocidade_media
      order by id
    ) as linha
  from public.linha_do_tempo
)
select count(*) as linhas_que_serao_removidas
from duplicadas
where linha > 1;

-- 2) Depois de checar o número acima, rode este DELETE para remover de fato
--    (mantém sempre a linha com o menor id de cada grupo duplicado):
delete from public.linha_do_tempo
where id in (
  select id
  from (
    select id,
      row_number() over (
        partition by
          regional, unidade, frente, codigo_equipamento, equipamento,
          codigo_operador, operador, data, hora_inicial, hora_final,
          codigo_operacao, atividade, classificacao, codigo_fazenda,
          codigo_zona, codigo_talhao, fazenda,
          horimetro_inicial, horimetro_final, horimetro_secundario, velocidade_media
        order by id
      ) as linha
    from public.linha_do_tempo
  ) dup
  where linha > 1
);
