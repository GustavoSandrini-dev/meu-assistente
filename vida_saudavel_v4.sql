-- =====================================================================
--  VIDA SAUDÁVEL — parte 4: cardápios favoritos.
--  Rode inteiro no SQL Editor. Idempotente.
-- =====================================================================

alter table public.saude_plano add column if not exists nome     text;
alter table public.saude_plano add column if not exists favorito boolean default false;

-- um cardápio favoritado fica guardado com ativo=false e favorito=true,
-- então não concorre com o cardápio que está em uso.
create index if not exists saude_plano_fav_idx on public.saude_plano (user_id, favorito);
