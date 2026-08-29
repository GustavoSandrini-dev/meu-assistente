// =====================================================================
//  Edge Function: cron-lembrete-agua
//  Roda de hora em hora e manda um Web Push SILENCIOSO ("beba água")
//  para quem ligou o lembrete e ainda não bateu a meta do dia.
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
//  Agendamento (SQL Editor, mesma ideia do cron-sync-games):
//    select cron.schedule('lembrete-agua','0 * * * *', $$
//      select net.http_post(
//        url := 'https://<PROJECT-REF>.supabase.co/functions/v1/cron-lembrete-agua',
//        headers := '{"Content-Type":"application/json","Authorization":"Bearer <SERVICE_ROLE_KEY>"}'::jsonb
//      ) $$);
// =====================================================================
import { createClient } from "jsr:@supabase/supabase-js@2";
import webpush from "npm:web-push@3.6.7";

const TZ = "America/Sao_Paulo";

function agoraBrasilia() {
  const f = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", hour12: false,
  }).formatToParts(new Date());
  const g = (t: string) => f.find((p) => p.type === t)!.value;
  return { dia: `${g("year")}-${g("month")}-${g("day")}`, hora: parseInt(g("hour"), 10) };
}

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

  // quem quer ser lembrado nesta hora
  const { data: perfis, error } = await sb
    .from("saude_perfil")
    .select("user_id, meta_agua_ml, copo_ml, lembrete_ini, lembrete_fim")
    .eq("lembrete_agua", true)
    .lte("lembrete_ini", hora)
    .gte("lembrete_fim", hora);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  if (!perfis?.length) return new Response(JSON.stringify({ hora, enviados: 0 }), { status: 200 });

  let enviados = 0, removidos = 0;

  for (const p of perfis) {
    // já bateu a meta hoje? então não incomoda
    const { data: goles } = await sb
      .from("saude_agua").select("ml").eq("user_id", p.user_id).eq("dia", dia);
    const tot = (goles ?? []).reduce((s, g) => s + (Number(g.ml) || 0), 0);
    const meta = p.meta_agua_ml ?? 2000;
    if (tot >= meta) continue;

    const { data: subs } = await sb
      .from("push_subs").select("id, endpoint, p256dh, auth").eq("user_id", p.user_id);
    if (!subs?.length) continue;

    const falta = Math.max(0, meta - tot);
    const payload = JSON.stringify({
      title: "💧 Hora de beber água",
      body: `Você está em ${tot} ml de ${meta} ml. Faltam ${falta} ml hoje.`,
      tag: "agua",
      url: `./vida-saudavel-web.html?agua=${p.copo_ml ?? 250}`,
    });

    for (const s of subs) {
      try {
        await webpush.sendNotification(
          { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
          payload,
          { TTL: 1800, urgency: "low" },
        );
        enviados++;
      } catch (e) {
        const code = (e as { statusCode?: number }).statusCode;
        if (code === 404 || code === 410) { // inscrição morta
          await sb.from("push_subs").delete().eq("id", s.id);
          removidos++;
        } else {
          console.error("push falhou", s.endpoint, code, String(e));
        }
      }
    }
  }

  return new Response(JSON.stringify({ dia, hora, enviados, removidos }), {
    headers: { "Content-Type": "application/json" },
  });
});
