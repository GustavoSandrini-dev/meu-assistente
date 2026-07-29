# Notas do projeto — meu assistente

## Regras de deploy (IMPORTANTE)
- **TUDO FICA NA RAIZ DO PROJETO.** Todos os arquivos (HTML, sw.js, common.js, .sql, .ts) ficam em
  `C:\Users\Usuario\Desktop\meu assistente` (a raiz do repositório git). Não usar subpastas para os
  arquivos que sobem no git. Se algum dia precisar de uma pasta, avisar o Gustavo qual é.
- Deploy é por `git add … && git commit && git push` a partir dessa raiz (GitHub Pages).
- Ao mexer em HTML/JS, **subir a versão do cache** em `sw.js` (`const C = "ma-vN"`) pra forçar atualização.

## Backend
- Supabase (Postgres + Auth + Edge Functions). Isolamento por usuário via RLS + filtro `user_id` no código.
- `app_state` (key/user_id/value): usado por Financeiro (key "fin") e Jogos (key "games", dados manuais/notas).
- `game_data` (id = user_id): catálogo de jogos sincronizado da Steam, por usuário.
- `user_keys` (user_id, steam_key, steam_id, sync_hour): chave da Steam de cada usuário (RLS, privada).
- Edge Functions: `sync-my-games` (sync sob demanda do usuário logado) e `cron-sync-games`
  (roda de hora em hora, sincroniza quem tem sync_hour == hora atual de Brasília). Diário, não em tempo real.

## Privacidade
- Financeiro é **privado** (não compartilhável por enquanto).
- Jogos/Filmes/Livros podem ser compartilhados opt-in no futuro.
