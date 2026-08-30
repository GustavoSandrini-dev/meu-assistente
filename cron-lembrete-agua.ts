// =====================================================================
//  Edge Function: cron-lembrete-agua
//  Roda de hora em hora e manda Web Push SILENCIOSO para:
//    1) beber água — quem ligou o lembrete e ainda não bateu a meta do dia
//    2) se pesar   — quem passou do intervalo escolhido (1/7/15/30/60/90 dias)
//
//  O cron chama de 30 em 30 minutos; o intervalo de cada usuário
//  (30 min a 3 h) é respeitado pela coluna ultimo_push_agua.
//
//  Usa @negrel/webpush (nativa de Deno, sem depender de shims do Node).
//
//  Deploy:
//    supabase functions deploy cron-lembrete-agua --no-verify-jwt
//
//  Secrets:
//    VAPID_KEYS     JSON {"publicKey":{...},"privateKey":{...}} do gerar-vapid.js
//    VAPID_SUBJECT  mailto:sandrinigustavo@gmail.com
//  SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY já existem por padrão.
//
//  Agendamento do cron: rodapé de vida_saudavel_v2.sql.
// =====================================================================
import { createClient } from "jsr:@supabase/supabase-js@2";
import * as webpush from "jsr:@negrel/webpush@0.5";

const TZ = "America/Sao_Paulo";
const HORA_PESAGEM = 9; // lembrete de pesagem sai uma vez por dia, às 9h

function agoraBrasilia() {
  const f = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", hour12: false,
  }).formatToParts(new Date());
  const g = (t: string) => f.find((p) => p.type === t)!.value;
  return { dia: `${g("year")}-${g("month")}-${g("day")}`, hora: parseInt(g("hour"), 10) };
}

type Sub = { id: string; endpoint: string; p256dh: string; auth: string };

// as chaves são carregadas uma vez, no boot da função
const vapidKeys = await webpush.importVapidKeys(JSON.parse(Deno.env.get("VAPID_KEYS")!));
const appServer = await webpush.ApplicationServer.new({
  contactInformation: Deno.env.get("VAPID_SUBJECT") ?? "mailto:sandrinigustavo@gmail.com",
  vapidKeys,
});

Deno.serve(async () => {
  const sb = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  const { dia, hora } = agoraBrasilia();
  let enviados = 0, removidos = 0, pesagens = 0;

  const subsDe = async (uid: string): Promise<Sub[]> => {
    const { data } = await sb.from("push_subs")
      .select("id, endpoint, p256dh, auth").eq("user_id", uid);
    return (data ?? []) as Sub[];
  };

  const mandar = async (subs: Sub[], payload: unknown) => {
    const txt = JSON.stringify(payload);
    for (const s of subs) {
      try {
        const alvo = appServer.subscribe({
          endpoint: s.endpoint,
          keys: { p256dh: s.p256dh, auth: s.auth },
        });
        await alvo.pushTextMessage(txt, { ttl: 1800 });
        enviados++;
      } catch (e) {
        const gone = e instanceof webpush.PushMessageError &&
          (e.isGone() || e.response.status === 404);
        if (gone) {                       // inscrição morta: limpa
          await sb.from("push_subs").delete().eq("id", s.id);
          removidos++;
        } else {
          console.error("push falhou", s.endpoint.slice(0, 60), String(e));
        }
      }
    }
  };

  // ------------------------------------------------------------ água
  const { data: perfisAgua, error } = await sb
    .from("saude_perfil")
    .select("user_id, meta_agua_ml, copo_ml, lembrete_ini, lembrete_fim, lembrete_agua_min, ultimo_push_agua")
    .eq("lembrete_agua", true)
    .lte("lembrete_ini", hora)
    .gte("lembrete_fim", hora);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });

  const agora = Date.now();
  for (const p of perfisAgua ?? []) {
    // respeita o intervalo escolhido pelo usuário (30, 60, 90, 120 ou 180 min).
    // Esta função roda de 30 em 30 min; quem pediu 1h só recebe a cada 2 execuções.
    const intervalo = (p.lembrete_agua_min ?? 60) * 60000;
    if (p.ultimo_push_agua) {
      const desde = agora - Date.parse(p.ultimo_push_agua);
      if (desde < intervalo - 120000) continue;   // 2 min de folga
    }
    const { data: goles } = await sb
      .from("saude_agua").select("ml").eq("user_id", p.user_id).eq("dia", dia);
    const tot = (goles ?? []).reduce((s, g) => s + (Number(g.ml) || 0), 0);
    const meta = p.meta_agua_ml ?? 2000;
    if (tot >= meta) continue;            // já bateu a meta, não incomoda
    const subs = await subsDe(p.user_id);
    if (!subs.length) continue;
    const copo = p.copo_ml ?? 250;
    await mandar(subs, {
      title: "💧 Hora de beber água",
      body: `Você está em ${tot} ml de ${meta} ml. Um copo de ${copo} ml agora — faltam ${meta - tot} ml hoje.`,
      tag: "agua",
      url: `./vida-saudavel-web.html?agua=${copo}`,
    });
    await sb.from("saude_perfil")
      .update({ ultimo_push_agua: new Date().toISOString() }).eq("user_id", p.user_id);
  }

  // --------------------------------------------------------- pesagem
  if (hora === HORA_PESAGEM) {
    const { data: perfisPeso } = await sb
      .from("saude_perfil")
      .select("user_id, lembrete_peso_dias, ultimo_push_peso")
      .gt("lembrete_peso_dias", 0);

    for (const p of perfisPeso ?? []) {
      if (p.ultimo_push_peso === dia) continue;   // já avisei hoje
      const { data: ult } = await sb
        .from("saude_peso").select("dia").eq("user_id", p.user_id)
        .order("dia", { ascending: false }).limit(1).maybeSingle();

      let passou = 0, venceu = true;
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
