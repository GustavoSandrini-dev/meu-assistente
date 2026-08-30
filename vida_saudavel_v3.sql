-- =====================================================================
--  VIDA SAUDÁVEL — parte 3: intervalo do lembrete de água, composição
--  corporal (bioimpedância + circunferências) e meta de proteína.
--  Rode inteiro no SQL Editor. Idempotente.
--  Requer a função public.set_user_id() da parte 1.
-- =====================================================================

-- ------------------- novas colunas no perfil -------------------
alter table public.saude_perfil add column if not exists lembrete_agua_min smallint default 60;
alter table public.saude_perfil add column if not exists ultimo_push_agua  timestamptz;
alter table public.saude_perfil add column if not exists prot_g_kg         numeric  default 2;

-- ---------- composição corporal e medidas (1 linha por dia) ----------
create table if not exists public.saude_medidas (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id) on delete cascade,
  dia              date not null default current_date,
  -- da balança de bioimpedância
  gordura_pct      numeric,
  musculo_kg       numeric,
  agua_pct         numeric,
  massa_ossea_kg   numeric,
  gordura_visceral numeric,
  idade_metabolica numeric,
  -- circunferências em cm
  pescoco          numeric,
  cintura          numeric,
  quadril          numeric,
  peito            numeric,
  braco            numeric,
  coxa             numeric,
  obs              text,
  created_at       timestamptz default now(),
  unique (user_id, dia)
);
create index if not exists saude_medidas_user_idx on public.saude_medidas (user_id, dia);

alter table public.saude_medidas enable row level security;
drop policy if exists saude_medidas_sel on public.saude_medidas;
drop policy if exists saude_medidas_ins on public.saude_medidas;
drop policy if exists saude_medidas_upd on public.saude_medidas;
drop policy if exists saude_medidas_del on public.saude_medidas;
create policy saude_medidas_sel on public.saude_medidas for select using (user_id = auth.uid());
create policy saude_medidas_ins on public.saude_medidas for insert with check (user_id = auth.uid());
create policy saude_medidas_upd on public.saude_medidas for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy saude_medidas_del on public.saude_medidas for delete using (user_id = auth.uid());

drop trigger if exists trg_set_user_id on public.saude_medidas;
create trigger trg_set_user_id before insert on public.saude_medidas
  for each row execute function public.set_user_id();

-- =====================================================================
--  O lembrete de água agora pode ser de 30 em 30 minutos, então o cron
--  precisa rodar duas vezes por hora. Troque <SERVICE_ROLE_KEY>.
-- =====================================================================
select cron.unschedule('lembrete-saude')
where exists (select 1 from cron.job where jobname = 'lembrete-saude');

select cron.schedule('lembrete-saude', '0,30 * * * *', $$
  select net.http_post(
    url := 'https://ovpncggowjhualakjaug.supabase.co/functions/v1/cron-lembrete-agua',
    headers := '{"Content-Type":"application/json","Authorization":"Bearer <SERVICE_ROLE_KEY>"}'::jsonb
  ) $$);
