-- =====================================================================
--  CADASTRO ABERTO (sem aprovação do admin)
--  Todo novo usuário já entra aprovado. Mantém só a trava de is_admin
--  (usuário comum não vira admin sozinho).
--  Rode no SQL Editor do Supabase.
-- =====================================================================

alter table public.profiles alter column approved set default true;
update public.profiles set approved = true where approved is not true;

create or replace function public.protect_profile_fields()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  if auth.role() is distinct from 'service_role' then
    if TG_OP = 'INSERT' then
      new.is_admin := false;
      new.approved := true;
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
