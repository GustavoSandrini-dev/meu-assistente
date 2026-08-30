-- =====================================================================
--  Vida Saudável — v7
--  Meta calórica que se corrige sozinha pelo peso e pelas medidas,
--  e lembrete de bioimpedância a cada 3 meses.
--
--  Rode este arquivo inteiro no SQL Editor do Supabase.
--  É idempotente: pode rodar de novo sem quebrar nada.
-- =====================================================================

-- corrigir a meta e reajustar o cardápio automaticamente quando o
-- usuário registra peso ou medidas novas
alter table public.saude_perfil
  add column if not exists ajuste_auto boolean not null default true;

-- de quantos em quantos dias pedir bioimpedância (0 = não pedir)
alter table public.saude_perfil
  add column if not exists lembrete_bio_dias integer not null default 90;

-- último dia em que o push de bioimpedância foi enviado
alter table public.saude_perfil
  add column if not exists ultimo_push_bio date;

comment on column public.saude_perfil.ajuste_auto is
  'Quando true, a meta de calorias é corrigida pelo ritmo real de peso e o cardápio é reescalonado.';
comment on column public.saude_perfil.lembrete_bio_dias is
  'Intervalo em dias do lembrete de bioimpedância. Padrão 90 (3 meses).';

-- índice que a função de lembrete usa para achar a última medida de cada campo
create index if not exists saude_medidas_user_dia_idx
  on public.saude_medidas (user_id, dia desc);

-- confere que ficou tudo no lugar
select column_name, data_type, column_default
from information_schema.columns
where table_schema='public' and table_name='saude_perfil'
  and column_name in ('ajuste_auto','lembrete_bio_dias','ultimo_push_bio')
order by column_name;
