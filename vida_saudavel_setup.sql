-- =====================================================================
--  MÓDULO VIDA SAUDÁVEL — tabelas + RLS
--  Rode isto inteiro no SQL Editor do Supabase. É idempotente (pode
--  rodar de novo por cima sem quebrar nada).
--
--  Tabelas:
--    saude_perfil    -> 1 linha por usuário (altura, peso, metas, lembrete)
--    saude_peso      -> histórico de peso (para o gráfico de IMC)
--    saude_agua      -> cada gole/copo registrado no dia
--    saude_registro  -> diário alimentar (1 linha por alimento consumido)
--    saude_alimento  -> alimentos personalizados / salvos do usuário
--    saude_receita   -> receitas com ingredientes e modo de preparo
--    saude_cardapio  -> plano semanal de refeições
--    push_subs       -> inscrições de Web Push (lembrete de água)
-- =====================================================================

-- ---------------------------------------------------------------- perfil
create table if not exists public.saude_perfil (
  user_id         uuid primary key references auth.users(id) on delete cascade,
  sexo            text,                       -- 'M' | 'F' (usado só no cálculo de TMB)
  nascimento      date,
  altura_cm       numeric,
  peso_kg         numeric,
  atividade       text    default 'leve',     -- sedentario|leve|moderado|intenso|atleta
  objetivo        text    default 'manter',   -- perder|manter|ganhar
  meta_kcal       integer,
  meta_prot_g     integer,
  meta_carb_g     integer,
  meta_gord_g     integer,
  meta_agua_ml    integer default 2000,
  copo_ml         integer default 250,
  lembrete_agua   boolean default true,
  lembrete_ini    smallint default 8,         -- hora inicial (0-23, horário de Brasília)
  lembrete_fim    smallint default 22,        -- hora final
  updated_at      timestamptz default now()
);

-- ------------------------------------------------------------ histórico
create table if not exists public.saude_peso (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  dia        date not null default current_date,
  peso_kg    numeric not null,
  created_at timestamptz default now(),
  unique (user_id, dia)
);

-- ------------------------------------------------------------- água
create table if not exists public.saude_agua (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  dia        date not null default current_date,
  ml         integer not null,
  created_at timestamptz default now()
);
create index if not exists saude_agua_dia_idx on public.saude_agua (user_id, dia);

-- -------------------------------------------------------- diário alimentar
create table if not exists public.saude_registro (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  dia          date not null default current_date,
  refeicao     text not null,                 -- cafe|lanche1|almoco|lanche2|jantar|ceia
  alimento     text not null,
  quantidade_g numeric not null,
  kcal         numeric,
  prot_g       numeric,
  carb_g       numeric,
  gord_g       numeric,
  fibra_g      numeric,
  sodio_mg     numeric,
  fonte        text,                          -- taco | off | manual | receita
  ref_id       text,                          -- id na TACO / código de barras
  created_at   timestamptz default now()
);
create index if not exists saude_registro_dia_idx on public.saude_registro (user_id, dia);

-- --------------------------------------------------- alimentos do usuário
create table if not exists public.saude_alimento (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  nome           text not null,
  marca          text,
  porcao_g       numeric default 100,
  kcal           numeric, prot_g numeric, carb_g numeric, gord_g numeric,
  fibra_g        numeric, sodio_mg numeric,
  codigo_barras  text,
  fonte          text default 'manual',
  created_at     timestamptz default now()
);
create index if not exists saude_alimento_user_idx on public.saude_alimento (user_id);

-- ------------------------------------------------------------- receitas
create table if not exists public.saude_receita (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  nome          text not null,
  porcoes       integer default 1,
  ingredientes  jsonb default '[]'::jsonb,    -- [{nome, g, kcal, prot_g, carb_g, gord_g, ref_id}]
  preparo       text,
  url_fonte     text,
  tags          text[],
  created_at    timestamptz default now()
);
create index if not exists saude_receita_user_idx on public.saude_receita (user_id);

-- ------------------------------------------------------------- cardápio
create table if not exists public.saude_cardapio (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  nome       text not null default 'Meu cardápio',
  ativo      boolean default true,
  plano      jsonb default '{}'::jsonb,       -- {seg:{almoco:[{...}]}, ter:{...}}
  updated_at timestamptz default now()
);

-- ------------------------------------------------- inscrições de Web Push
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

-- =====================================================================
--  RLS — cada usuário só enxerga as próprias linhas
-- =====================================================================
do $$
declare t text;
begin
  foreach t in array array[
    'saude_perfil','saude_peso','saude_agua','saude_registro','saude_alimento',
    'saude_receita','saude_cardapio','push_subs'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists %I on public.%I', t||'_sel', t);
    execute format('drop policy if exists %I on public.%I', t||'_ins', t);
    execute format('drop policy if exists %I on public.%I', t||'_upd', t);
    execute format('drop policy if exists %I on public.%I', t||'_del', t);
    execute format('create policy %I on public.%I for select using (user_id = auth.uid())', t||'_sel', t);
    execute format('create policy %I on public.%I for insert with check (user_id = auth.uid())', t||'_ins', t);
    execute format('create policy %I on public.%I for update using (user_id = auth.uid()) with check (user_id = auth.uid())', t||'_upd', t);
    execute format('create policy %I on public.%I for delete using (user_id = auth.uid())', t||'_del', t);
  end loop;
end $$;

-- =====================================================================
--  Preenche user_id sozinho no insert (o app não precisa mandar)
-- =====================================================================
create or replace function public.set_user_id()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  if new.user_id is null then new.user_id := auth.uid(); end if;
  return new;
end $$;

do $$
declare t text;
begin
  foreach t in array array[
    'saude_perfil','saude_peso','saude_agua','saude_registro','saude_alimento',
    'saude_receita','saude_cardapio','push_subs'
  ] loop
    execute format('drop trigger if exists trg_set_user_id on public.%I', t);
    execute format('create trigger trg_set_user_id before insert on public.%I for each row execute function public.set_user_id()', t);
  end loop;
end $$;
