# Deploy — Vida Saudável v52

Três coisas mudam de lugar: **SQL**, **Edge Function** e **arquivos do site**.
Faça na ordem abaixo. Leva uns 10 minutos.

---

## 1. Banco de dados (SQL Editor do Supabase)

Abra o projeto `ovpncggowjhualakjaug` → **SQL Editor** → **New query**,
cole o conteúdo inteiro de `vida_saudavel_v7.sql` e rode.

Ele adiciona três colunas em `saude_perfil` (`ajuste_auto`, `lembrete_bio_dias`,
`ultimo_push_bio`) e um índice em `saude_medidas`. É idempotente — pode rodar
duas vezes sem problema.

No fim ele mesmo mostra uma tabelinha com as três colunas. Se elas aparecerem,
essa parte está feita.

---

## 2. Edge Function (PowerShell, na pasta do projeto)

```powershell
cd C:\Users\Usuario\meu-assistente
supabase functions deploy cron-lembrete-agua --no-verify-jwt
```

> O arquivo já foi gravado nos dois lugares:
> `cron-lembrete-agua.ts` na raiz (referência) e
> `supabase\functions\cron-lembrete-agua\index.ts`, que é de onde o CLI publica.
> Se essa pasta não existia antes, ela foi criada agora — inclua-a no `git add`.

Se ele pedir login:

```powershell
supabase login
supabase link --project-ref ovpncggowjhualakjaug
```

O cron já está agendado de 30 em 30 minutos e continua igual — **não precisa
mexer no `cron.schedule` de novo**. A função nova só ganhou dois blocos a mais
(circunferências e bioimpedância) dentro da mesma execução.

Para testar sem esperar o horário, no SQL Editor:

```sql
select net.http_post(
  url     := 'https://ovpncggowjhualakjaug.supabase.co/functions/v1/cron-lembrete-agua',
  headers := jsonb_build_object(
    'Content-Type','application/json',
    'Authorization','Bearer ' || 'COLE_AQUI_A_SERVICE_ROLE_KEY')
) as id;
```

Depois confira a resposta:

```sql
select id, status_code, content
from net._http_response
order by id desc
limit 5;
```

O `content` agora traz também o campo `bios`.

> Os lembretes de pesagem saem às **9h** e o de bioimpedância às **10h**
> (horário de Brasília). Fora dessas horas o retorno mostra `pesagens: 0` e
> `bios: 0` — é o esperado, não é erro.

---

## 3. Site (PowerShell, na pasta do projeto)

Os arquivos novos já estão em `C:\Users\Usuario\meu-assistente`. Só falta subir:

```powershell
cd C:\Users\Usuario\meu-assistente
git add vida-saudavel-web.html sw.js cron-lembrete-agua.ts supabase/functions/cron-lembrete-agua/index.ts vida_saudavel_v7.sql DEPLOY-v52.md
git commit -m "Vida Saudavel v52: meta calorica dinamica pelo peso e medidas, cardapio reescalonado, lembrete de circunferencias e bioimpedancia"
git push origin main
```

O GitHub Pages leva de 1 a 3 minutos para publicar.

---

## 4. No celular

O service worker subiu para `ma-v52`. Para pegar a versão nova:

- feche o app (deslize para fora dos recentes) e abra de novo, **ou**
- abra no navegador e recarregue duas vezes.

Depois, em **Corpo & IMC**, confira se apareceu a caixa
**"Como cheguei na meta de hoje"** e o checkbox
**"Corrigir a meta e o cardápio sozinho…"** — se aparecerem, o cache virou.

---

## Checklist rápido

- [ ] `vida_saudavel_v7.sql` rodou e mostrou as três colunas
- [ ] `supabase functions deploy` terminou sem erro
- [ ] `git push origin main` foi aceito
- [ ] App recarregado no celular, caixa da meta aparecendo
- [ ] Registrei um peso e vi a meta se mexer
