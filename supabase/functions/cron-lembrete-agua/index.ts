// =====================================================================
//  Edge Function: cron-lembrete-agua
//  Roda de 30 em 30 min e manda Web Push (silencioso, com som ou com
//  som e vibração, conforme a preferência de cada usuário) para:
//    1) beber água   — quem ligou o lembrete e ainda não bateu a meta do dia
//    2) se pesar     — quem passou do intervalo escolhido (1/7/15/30/60/90 dias);
//                      o mesmo aviso pede as circunferências quando elas estão
//                      mais velhas que o intervalo de pesagem
//    3) bioimpedância — calendário próprio, de 3 em 3 meses
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
const HORA_PESAGEM = 9;  // lembrete de pesagem sai uma vez por dia, às 9h
const HORA_BIO = 10;     // bioimpedância sai numa hora diferente, para não virar spam
const BIO_DIAS = 90;     // padrão: de 3 em 3 meses

function agoraBrasilia() {
  const f = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", hour12: false,
  }).formatToParts(new Date());
  const g = (t: string) => f.find((p) => p.type === t)!.value;
  return { dia: `${g("year")}-${g("month")}-${g("day")}`, hora: parseInt(g("hour"), 10) };
}

type Sub = { id: string; endpoint: string; p256dh: string; auth: string };

// Como o aviso chega no aparelho. A web não permite som personalizado:
// silent=false apenas libera o som padrão do canal de notificação do sistema.
function alerta(modo: string | null) {
  if (modo === "vibrar") return { silent: false, vibrate: [300, 150, 300] };
  if (modo === "som") return { silent: false };
  return { silent: true };
}

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
    .select("user_id, meta_agua_ml, copo_ml, lembrete_ini, lembrete_fim, lembrete_agua_min, ultimo_push_agua, lembrete_som")
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
      ...alerta(p.lembrete_som),
    });
    await sb.from("saude_perfil")
      .update({ ultimo_push_agua: new Date().toISOString() }).eq("user_id", p.user_id);
  }

  // ------------------------------------------- pesagem + circunferências
  // dias desde o último registro de uma coluna de saude_medidas
  const desdeMedida = async (uid: string, col: string) => {
    const { data } = await sb.from("saude_medidas").select("dia")
      .eq("user_id", uid).not(col, "is", null)
      .order("dia", { ascending: false }).limit(1).maybeSingle();
    if (!data?.dia) return null;
    return {
      dia: data.dia as string,
      dias: Math.floor(
        (Date.parse(dia + "T12:00:00Z") - Date.parse(data.dia + "T12:00:00Z")) / 86400000,
      ),
    };
  };

  if (hora === HORA_PESAGEM) {
    const { data: perfisPeso } = await sb
      .from("saude_perfil")
      .select("user_id, lembrete_peso_dias, ultimo_push_peso, lembrete_som")
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

      // a fita métrica anda junto com a balança: é dela que sai a estimativa
      // de gordura quando não há bioimpedância recente
      const fita = await desdeMedida(p.user_id, "cintura");
      const fitaVenceu = !fita || fita.dias >= p.lembrete_peso_dias;
      const base = ult?.dia
        ? `Sua última pesagem foi há ${passou} dia(s). Registre para o gráfico continuar contando a história.`
        : "Registre sua primeira pesagem e comece a acompanhar sua evolução.";
      const extra = fitaVenceu
        ? ` 📏 Aproveite e meça também pescoço, cintura e quadril${
          fita ? ` — a última medida foi há ${fita.dias} dia(s)` : ""
        }.`
        : "";

      await mandar(subs, {
        title: "⚖️ Hora de se pesar",
        body: base + extra,
        tag: "peso",
        url: "./vida-saudavel-web.html?aba=corpo",
        ...alerta(p.lembrete_som),
      });
      await sb.from("saude_perfil").update({ ultimo_push_peso: dia }).eq("user_id", p.user_id);
      pesagens++;
    }
  }

  // ---------------------------------------------------- bioimpedância
  // Calendário próprio: de 3 em 3 meses, independente do intervalo de pesagem.
  let bios = 0;
  if (hora === HORA_BIO) {
    const { data: perfisBio } = await sb
      .from("saude_perfil")
      .select("user_id, lembrete_bio_dias, ultimo_push_bio, lembrete_som");

    for (const p of perfisBio ?? []) {
      const intervalo = p.lembrete_bio_dias ?? BIO_DIAS;
      if (intervalo <= 0) continue;                       // desligado
      if (p.ultimo_push_bio) {                            // não repete antes de uma semana
        const d = Math.floor(
          (Date.parse(dia + "T12:00:00Z") - Date.parse(p.ultimo_push_bio + "T12:00:00Z")) / 86400000,
        );
        if (d < 7) continue;
      }
      const bio = await desdeMedida(p.user_id, "gordura_pct");
      if (bio && bio.dias < intervalo) continue;

      const subs = await subsDe(p.user_id);
      if (!subs.length) continue;
      await mandar(subs, {
        title: "🧪 Hora da bioimpedância",
        body: bio
          ? `Sua última bioimpedância foi há ${bio.dias} dia(s). Suba na balança em jejum e atualize gordura, músculo e água — é o que deixa o cálculo de calorias afiado.`
          : "Registre sua primeira bioimpedância: gordura, músculo, água e gordura visceral. Com ela a meta de calorias fica bem mais precisa.",
        tag: "bio",
        url: "./vida-saudavel-web.html?aba=corpo",
        ...alerta(p.lembrete_som),
      });
      await sb.from("saude_perfil").update({ ultimo_push_bio: dia }).eq("user_id", p.user_id);
      bios++;
    }
  }

  return new Response(JSON.stringify({ dia, hora, enviados, removidos, pesagens, bios }), {
    headers: { "Content-Type": "application/json" },
  });
});
