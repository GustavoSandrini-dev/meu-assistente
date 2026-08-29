// ============================================================
//  common.js — código compartilhado entre os módulos do assistente
//  (menu dinâmico + tema). Carregar DEPOIS do supabase-js.
// ============================================================

// ----- Menu dinâmico (lê os módulos ativos do perfil) -----
const NAVMODS = {
  financeiro: { name: "Financeiro", emoji: "💰", url: "painel-financeiro-web.html" },
  jogos:      { name: "Jogos",      emoji: "🎮", url: "biblioteca-jogos-web.html" },
  filmes:     { name: "Filmes",     emoji: "🎬", url: "filmes-web.html" },
  livros:     { name: "Livros",     emoji: "📚", url: "livros-web.html" },
  tarefas:    { name: "Tarefas",    emoji: "✅", url: "tarefas-web.html" },
  saude:      { name: "Vida Saudável", emoji: "🥗", url: "vida-saudavel-web.html" },
};

// Monta o menu no container que existir na página:
//  - #appNav   (financeiro/jogos, links com estilo inline)
//  - #navLinks (filmes/livros, links com classe .nav / .act)
async function buildNav(sb, currentKey) {
  try {
    const { data: { user } } = await sb.auth.getUser();
    const { data: p } = await sb.from("profiles").select("modules").eq("user_id", user.id).maybeSingle();
    const mods = (p && p.modules && p.modules.length) ? p.modules : ["financeiro", "jogos", "filmes", "livros"];

    const appNav = document.getElementById("appNav");
    const navLinks = document.getElementById("navLinks");

    if (appNav) {
      const base = "text-decoration:none;font-size:13px;font-weight:600;padding:7px 13px;border-radius:9px;border:1.5px solid var(--border);";
      let h = `<a href="index.html" style="${base}background:var(--card);color:var(--muted)">🏠 Início</a>`;
      mods.forEach(k => {
        const m = NAVMODS[k]; if (!m) return;
        const act = k === currentKey;
        h += `<a href="${m.url}" style="${base}${act ? 'background:var(--accent);color:var(--accent-t);border-color:var(--accent)' : 'background:var(--card);color:var(--muted)'}">${m.emoji} ${m.name}</a>`;
      });
      appNav.innerHTML = h;
    } else if (navLinks) {
      let h = `<a href="index.html">🏠 Início</a>`;
      mods.forEach(k => {
        const m = NAVMODS[k]; if (!m) return;
        h += `<a href="${m.url}" class="${k === currentKey ? 'act' : ''}">${m.emoji} ${m.name}</a>`;
      });
      navLinks.innerHTML = h;
    }
  } catch (e) { console.warn("nav", e); }
}
