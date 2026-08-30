-- =====================================================================
--  VIDA SAUDÁVEL — parte 6: acompanhamento do dia
--   · marcar refeição feita / pulada
--   · registrar treino
--   · meta de peso e prazo
--  Rode no SQL Editor. Idempotente. Requer public.set_user_id() da parte 1.
-- =====================================================================

-- meta de peso no perfil
alter table public.saude_perfil add column if not exists peso_meta       numeric;
alter table public.saude_perfil add column if not exists peso_meta_prazo date;
alter table public.saude_perfil add column if not exists peso_inicial    numeric;

-- um registro por dia: refeições marcadas, treino e observação
create table if not exists public.saude_dia (
  user_id    uuid not null references auth.users(id) on delete cascade,
  dia        date not null default current_date,
  feitas     jsonb default '{}'::jsonb,   -- {"cafe":true,"almoco":false,...}
  treinou    boolean,
  treino     text,                        -- musculacao | corrida | natacao | outro
  treino_min integer,
  obs        text,
  updated_at timestamptz default now(),
  primary key (user_id, dia)
);
create index if not exists saude_dia_idx on public.saude_dia (user_id, dia desc);

alter table public.saude_dia enable row level security;
drop policy if exists saude_dia_sel on public.saude_dia;
drop policy if exists saude_dia_ins on public.saude_dia;
drop policy if exists saude_dia_upd on public.saude_dia;
drop policy if exists saude_dia_del on public.saude_dia;
create policy saude_dia_sel on public.saude_dia for select using (user_id = auth.uid());
create policy saude_dia_ins on public.saude_dia for insert with check (user_id = auth.uid());
create policy saude_dia_upd on public.saude_dia for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy saude_dia_del on public.saude_dia for delete using (user_id = auth.uid());

drop trigger if exists trg_set_user_id on public.saude_dia;
create trigger trg_set_user_id before insert on public.saude_dia
  for each row execute function public.set_user_id();
