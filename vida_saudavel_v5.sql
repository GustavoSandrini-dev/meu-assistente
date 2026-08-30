-- =====================================================================
--  VIDA SAUDÁVEL — parte 5: como o lembrete chega no aparelho.
--  'silencioso' (padrão) · 'som' · 'vibrar'
--  Rode no SQL Editor. Idempotente.
-- =====================================================================
alter table public.saude_perfil
  add column if not exists lembrete_som text default 'silencioso';
