-- =====================================================================
--  VIDA SAUDÁVEL — parte 2: gerador de cardápio, preços, lembrete de
--  pesagem e Web Push. Rode inteiro no SQL Editor (idempotente).
--  Requer a função public.set_user_id() criada na parte 1.
-- =====================================================================

-- ------------------- novas colunas no perfil -------------------
alter table public.saude_perfil add column if not exists lembrete_peso_dias smallint default 0;
alter table public.saude_perfil add column if not exists ultimo_push_peso date;

-- --------------- cardápio gerado (plano do período) ---------------
create table if not exists public.saude_plano (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  ativo       boolean default true,
  inicio      date,
  semanas     integer,
  cfg         jsonb default '{}'::jsonb,   -- respostas do questionário
  plano       jsonb default '{}'::jsonb,   -- {"2026-09-01":{"almoco":{...}}}
  custo_total numeric,
  updated_at  timestamptz default now(),
  created_at  timestamptz default now()
);
create index if not exists saude_plano_user_idx on public.saude_plano (user_id, ativo);

-- --------------- preços do mercado de cada usuário ---------------
create table if not exists public.saude_precos (
  user_id    uuid not null references auth.users(id) on delete cascade,
  slug       text not null,
  rs_kg      numeric not null,
  updated_at timestamptz default now(),
  primary key (user_id, slug)
);

-- ------------------- inscrições de Web Push -------------------
create table if not exists public.push_subs (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  endpoint   text not null unique,
  p256dh     text not null,
  auth       text not null,
  user_agent text,
  created_at timestamptz default now()
);
create index if not exists push_subs_user_idx on public.push_subs (user_id);

-- ================== RLS + trigger de user_id ==================
do $$
declare t text;
begin
  foreach t in array array['saude_plano','saude_precos','push_subs'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists %I on public.%I', t||'_sel', t);
    execute format('drop policy if exists %I on public.%I', t||'_ins', t);
    execute format('drop policy if exists %I on public.%I', t||'_upd', t);
    execute format('drop policy if exists %I on public.%I', t||'_del', t);
    execute format('create policy %I on public.%I for select using (user_id = auth.uid())', t||'_sel', t);
    execute format('create policy %I on public.%I for insert with check (user_id = auth.uid())', t||'_ins', t);
    execute format('create policy %I on public.%I for update using (user_id = auth.uid()) with check (user_id = auth.uid())', t||'_upd', t);
    execute format('create policy %I on public.%I for delete using (user_id = auth.uid())', t||'_del', t);
    execute format('drop trigger if exists trg_set_user_id on public.%I', t);
    execute format('create trigger trg_set_user_id before insert on public.%I for each row execute function public.set_user_id()', t);
  end loop;
end $$;

-- =====================================================================
--  Agendamento do lembrete (depois de fazer o deploy da Edge Function
--  cron-lembrete-agua). Troque <PROJECT-REF> e <SERVICE_ROLE_KEY>.
-- =====================================================================
-- create extension if not exists pg_cron;
-- create extension if not exists pg_net;
--
-- select cron.unschedule('lembrete-saude') where exists
--   (select 1 from cron.job where jobname = 'lembrete-saude');
--
-- select cron.schedule('lembrete-saude', '0 * * * *', $$
--   select net.http_post(
--     url := 'https://<PROJECT-REF>.supabase.co/functions/v1/cron-lembrete-agua',
--     headers := '{"Content-Type":"application/json","Authorization":"Bearer <SERVICE_ROLE_KEY>"}'::jsonb
--   ) $$);
