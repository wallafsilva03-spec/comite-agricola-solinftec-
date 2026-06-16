-- Execute este script UMA VEZ no SQL Editor do Supabase.
-- Ele cria uma tabela "de rascunho" (staging) com os MESMOS cabeçalhos da sua planilha
-- original (em português, com acento, igualzinho ao Excel). Assim o importador de CSV
-- do Table Editor não reclama de cabeçalho incompatível.

create table if not exists public.stg_linha_do_tempo (
  "Descrição Regional" text,
  "Descrição da Unidade" text,
  "Descrição do Grupo de Equipamento" text,
  "Código Equipamento" text,
  "Descrição do Equipamento" text,
  "Código de Operador" text,
  "Nome" text,
  "Data Hora Local" text,
  "Hora Inicial" text,
  "Hora Final" text,
  "Código da Operação" text,
  "Descrição da Operação" text,
  "Descrição do Grupo da Operação" text,
  "Código da Fazenda" text,
  "Código da Zona" text,
  "Código do Talhão" text,
  "Descrição da Fazenda" text,
  "Horímetro/Odometro Inicial" text,
  "Horímetro/Odometro Final" text,
  "Horímetro/Odometro Secundário" text,
  "Velocidade Média" text
);

-- Como é só uma tabela de rascunho usada manualmente pelo painel administrativo, RLS
-- não precisa ficar habilitado (ela nunca é lida pelo HTML público).

-- Função que lê o que está em stg_linha_do_tempo, converte os tipos e copia para a
-- tabela definitiva linha_do_tempo. Depois de copiar, limpa a staging para a próxima
-- importação.
create or replace function public.importar_stg_linha_do_tempo()
returns integer
language plpgsql
as $$
declare
  total integer;
begin
  insert into public.linha_do_tempo (
    regional, unidade, frente, codigo_equipamento, equipamento,
    codigo_operador, operador, data, hora_inicial, hora_final,
    codigo_operacao, atividade, classificacao, codigo_fazenda,
    codigo_zona, codigo_talhao, fazenda,
    horimetro_inicial, horimetro_final, horimetro_secundario, velocidade_media
  )
  select
    "Descrição Regional",
    "Descrição da Unidade",
    "Descrição do Grupo de Equipamento",
    "Código Equipamento",
    "Descrição do Equipamento",
    "Código de Operador",
    "Nome",
    to_date("Data Hora Local", 'DD/MM/YYYY'),
    "Hora Inicial"::time,
    "Hora Final"::time,
    "Código da Operação",
    "Descrição da Operação",
    "Descrição do Grupo da Operação",
    "Código da Fazenda",
    "Código da Zona",
    "Código do Talhão",
    "Descrição da Fazenda",
    nullif(trim(replace("Horímetro/Odometro Inicial", ',', '.')), '')::numeric,
    nullif(trim(replace("Horímetro/Odometro Final", ',', '.')), '')::numeric,
    nullif(trim(replace("Horímetro/Odometro Secundário", ',', '.')), '')::numeric,
    nullif(trim(replace("Velocidade Média", ',', '.')), '')::numeric
  from public.stg_linha_do_tempo
  where "Data Hora Local" is not null
    and "Hora Inicial" is not null
    and "Hora Final" is not null
    and "Descrição da Operação" is not null
    and "Descrição do Grupo da Operação" is not null;

  get diagnostics total = row_count;

  truncate table public.stg_linha_do_tempo;

  return total;
end;
$$;
