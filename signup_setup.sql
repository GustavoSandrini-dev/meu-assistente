-- =====================================================================
--  CADASTRO COM APROVAÇÃO (fluxo novo)
--  - Pessoa se cadastra (nome/email/telefone) -> vira um "pedido".
--  - Você recebe e-mail e aprova -> o e-mail entra na lista de aprovados.
--  - Quando a pessoa fizer login, o perfil é criado JÁ aprovado.
--  Rode isto inteiro no SQL Editor do Supabase (pode rodar por cima do anterior).
-- =====================================================================

-- coluna de aprovação no perfil
alter table public.profiles add column if not exists approved boolean not null default false;

-- libera quem já existe (você) e marca admin
update public.profiles set approved = true where approved is not true;
update public.profiles p set is_admin = true, approved = true
from auth.users u
where p.user_id = u.id and u.email = 'sandrinigustavo@gmail.com';

-- pedidos de cadastro (pendentes) — sem policies = só service_role acessa
create table if not exists public.signup_requests (
  id uuid primary key default gen_random_uuid(),
  name text, email text not null, phone text,
  token text not null, status text not null default 'pending',
  created_at timestamptz not null default now()
);
alter table public.signup_requests enable row level security;

-- e-mails aprovados (allowlist) — sem policies = só service_role acessa
create table if not exists public.approved_emails (
  email text primary key,
  name text, phone text,
  added_at timestamptz not null default now()
);
alter table public.approved_emails enable row level security;

-- Ao criar o perfil: aprova automático se o e-mail está na allowlist,
-- e puxa o nome/telefone do cadastro. Usuário comum não muda approved/is_admin.
create or replace function public.protect_profile_fields()
returns trigger language plpgsql security definer set search_path=public as $$
declare rec record;
begin
  if auth.role() is distinct from 'service_role' then
    if TG_OP = 'INSERT' then
      new.is_admin := false;
      select a.name, a.phone into rec
        from public.approved_emails a
        join auth.users u on u.id = new.user_id
        where lower(a.email) = lower(u.email);
      if found then
        new.approved := true;
        if rec.name  is not null and length(trim(rec.name))  > 0 then new.name  := rec.name;  end if;
        if rec.phone is not null and length(trim(rec.phone)) > 0 then new.phone := rec.phone; end if;
      else
        new.approved := false;
      end if;
    else
      new.approved := old.approved;
      new.is_admin := old.is_admin;
    end if;
  end if;
  return new;
end $$;

drop trigger if exists trg_protect_profile on public.profiles;
create trigger trg_protect_profile
  before insert or update on public.profiles
  for each row execute function public.protect_profile_fields();
