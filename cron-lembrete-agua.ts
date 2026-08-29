// =====================================================================
//  Edge Function: cron-lembrete-agua
//  Roda de hora em hora e manda Web Push SILENCIOSO para:
//    1) beber água   — quem ligou o lembrete e ainda não bateu a meta
//    2) se pesar     — quem passou do intervalo escolhido (1/7/15/30/60/90 dias)
//
//  Deploy:
//    supabase functions deploy cron-lembrete-agua --no-verify-jwt
//
//  Secrets (supabase secrets set ...):
//    VAPID_PUBLIC_KEY   chave pública  (a mesma que vai no vida-saudavel-web.html)
//    VAPID_PRIVATE_KEY  chave privada  (NUNCA vai pro git / pro HTML)
//    VAPID_SUBJECT      mailto:sandrinigustavo@gmail.com
//  SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY já existem por padrão.
//
//  Agendamento: veja o rodapé de vida_saudavel_v2.sql.
// =====================================================================
import { createClient } from "jsr:@supabase/supabase-js@2";
import webpush from "npm:web-push@3.6.7";

const TZ = "America/Sao_Paulo";
const HORA_PESAGEM = 9; // manda o lembrete de pesagem uma vez por dia, às 9h

function agoraBrasilia() {
  const f = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", hour12: false,
  }).formatToParts(new Date());
  const g = (t: string) => f.find((p) => p.type === t)!.value;
  return { dia: `${g("year")}-${g("month")}-${g("day")}`, hora: parseInt(g("hour"), 10) };
}

type Sub = { id: string; endpoint: string; p256dh: string; auth: string };

Deno.serve(async () => {
  const sb = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );
  webpush.setVapidDetails(
    Deno.env.get("VAPID_SUBJECT") ?? "mailto:sandrinigustavo@gmail.com",
    Deno.env.get("VAPID_PUBLIC_KEY")!,
    Deno.env.get("VAPID_PRIVATE_KEY")!,
  );

  const { dia, hora } = agoraBrasilia();
  let enviados = 0, removidos = 0;

  const subsDe = async (uid: string): Promise<Sub[]> => {
    const { data } = await sb.from("push_subs")
      .select("id, endpoint, p256dh, auth").eq("user_id", uid);
    return (data ?? []) as Sub[];
  };

  const mandar = async (subs: Sub[], payload: unknown) => {
    for (const s of subs) {
      try {
        await webpush.sendNotification(
          { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
          JSON.stringify(payload),
          { TTL: 1800, urgency: "low" },
        );
        enviados++;
      } catch (e) {
        const code = (e as { statusCode?: number }).statusCode;
        if (code === 404 || code === 410) {
          await sb.from("push_subs").delete().eq("id", s.id);
          removidos++;
        } else {
          console.error("push falhou", s.endpoint, code, String(e));
        }
      }
    }
  };

  // ------------------------------------------------------------ água
  const { data: perfisAgua, error } = await sb
    .from("saude_perfil")
    .select("user_id, meta_agua_ml, copo_ml, lembrete_ini, lembrete_fim")
    .eq("lembrete_agua", true)
    .lte("lembrete_ini", hora)
    .gte("lembrete_fim", hora);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });

  for (const p of perfisAgua ?? []) {
    const { data: goles } = await sb
      .from("saude_agua").select("ml").eq("user_id", p.user_id).eq("dia", dia);
    const tot = (goles ?? []).reduce((s, g) => s + (Number(g.ml) || 0), 0);
    const meta = p.meta_agua_ml ?? 2000;
    if (tot >= meta) continue;
    const subs = await subsDe(p.user_id);
    if (!subs.length) continue;
    await mandar(subs, {
      title: "💧 Hora de beber água",
      body: `Você está em ${tot} ml de ${meta} ml. Faltam ${meta - tot} ml hoje.`,
      tag: "agua",
      url: `./vida-saudavel-web.html?agua=${p.copo_ml ?? 250}`,
    });
  }

  // --------------------------------------------------------- pesagem
  let pesagens = 0;
  if (hora === HORA_PESAGEM) {
    const { data: perfisPeso } = await sb
      .from("saude_perfil")
      .select("user_id, lembrete_peso_dias, ultimo_push_peso")
      .gt("lembrete_peso_dias", 0);

    for (const p of perfisPeso ?? []) {
      if (p.ultimo_push_peso === dia) continue; // já avisei hoje
      const { data: ult } = await sb
        .from("saude_peso").select("dia").eq("user_id", p.user_id)
        .order("dia", { ascending: false }).limit(1).maybeSingle();

      let venceu = true, passou = 0;
      if (ult?.dia) {
        passou = Math.floor(
          (Date.parse(dia + "T12:00:00Z") - Date.parse(ult.dia + "T12:00:00Z")) / 86400000,
        );
        venceu = passou >= p.lembrete_peso_dias;
      }
      if (!venceu) continue;

      const subs = await subsDe(p.user_id);
      if (!subs.length) continue;
      await mandar(subs, {
        title: "⚖️ Hora de se pesar",
        body: ult?.dia
          ? `Sua última pesagem foi há ${passou} dia(s). Registre para o gráfico continuar contando a história.`
          : "Registre sua primeira pesagem e comece a acompanhar sua evolução.",
        tag: "peso",
        url: "./vida-saudavel-web.html?aba=corpo",
      });
      await sb.from("saude_perfil").update({ ultimo_push_peso: dia }).eq("user_id", p.user_id);
      pesagens++;
    }
  }

  return new Response(JSON.stringify({ dia, hora, enviados, removidos, pesagens }), {
    headers: { "Content-Type": "application/json" },
  });
});
