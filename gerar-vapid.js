// =====================================================================
//  Gera o par de chaves VAPID do Web Push. Sem dependência nenhuma:
//      node gerar-vapid.js
//
//  Ele imprime duas coisas:
//    1) VAPID_PUBLIC  -> vai no vida-saudavel-web.html (é pública, pode subir no git)
//    2) VAPID_KEYS    -> vai SÓ nos secrets do Supabase (NUNCA no git)
//
//  Rode uma vez só. Se gerar de novo, todos os aparelhos já inscritos
//  param de receber e precisam ativar a notificação outra vez.
// =====================================================================
const { generateKeyPairSync } = require("crypto");

const { publicKey, privateKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
const pub = publicKey.export({ format: "jwk" });   // { kty, crv, x, y }
const prv = privateKey.export({ format: "jwk" });  // { kty, crv, x, y, d }

// applicationServerKey do navegador = base64url( 0x04 || x || y )
const b = (s) => Buffer.from(s, "base64url");
const appServerKey = Buffer.concat([Buffer.from([4]), b(pub.x), b(pub.y)]).toString("base64url");

console.log("\n=== 1) VAPID_PUBLIC — cole no vida-saudavel-web.html ===\n");
console.log(`const VAPID_PUBLIC="${appServerKey}";`);
console.log("\n=== 2) VAPID_KEYS — cole nos secrets do Supabase (segredo!) ===\n");
console.log(JSON.stringify({ publicKey: pub, privateKey: prv }));
console.log("");
