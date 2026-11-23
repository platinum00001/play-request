// Play Request API (edge function "play-request-api", verify_jwt = false).
// The function does its own JWT check. Queries run under RLS as anon or authenticated
// so we never bypass row security, even though we hold a database URL.
import postgres from "npm:postgres@3.4.5";

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, { prepare: false, max: 2, idle_timeout: 20 });
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY")!;

const ALLOWED = [
  /^https:\/\/platinum00001\.github\.io$/,
  /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/,
];
function cors(req: Request) {
  const o = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ALLOWED.some((r) => r.test(o)) ? o : "https://platinum00001.github.io",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

class UserError extends Error {}
const str = (v: unknown, max: number) => {
  if (v == null) return null;
  const s = String(v).trim().slice(0, max);
  return s === "" ? null : s;
};

function asRole<T>(role: "anon" | "authenticated", claims: Record<string, unknown>, fn: (tx: postgres.TransactionSql) => Promise<T>) {
  return sql.begin(async (tx) => {
    await tx`select set_config('request.jwt.claims', ${JSON.stringify({ ...claims, role })}, true)`;
    await tx.unsafe(role === "anon" ? "set local role anon" : "set local role authenticated");
    return await fn(tx);
  });
}

async function userFromToken(req: Request, required: boolean) {
  const auth = req.headers.get("authorization") ?? "";
  const token = auth.replace(/^Bearer\s+/i, "");
  if (!token || token.startsWith("sb_")) {
    if (required) throw new UserError("Please sign in.");
    return null;
  }
  const r = await fetch(SUPABASE_URL + "/auth/v1/user", { headers: { apikey: ANON_KEY, authorization: "Bearer " + token } });
  if (!r.ok) {
    if (required) throw new UserError("Please sign in again.");
    return null;
  }
  const u = await r.json();
  if (!u?.id) {
    if (required) throw new UserError("Please sign in again.");
    return null;
  }
  return { sub: u.id as string, email: u.email as string };
}
const claimsFor = (u: { sub: string; email: string }) => ({ sub: u.sub, email: u.email, aud: "authenticated" });

Deno.serve(async (req: Request) => {
  const headers = { ...cors(req), "content-type": "application/json" };
  if (req.method === "OPTIONS") return new Response(null, { headers });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers });
  try {
    const body = await req.json().catch(() => ({}));
    const action = String(body.action || "");
    if (action === "health") {
      const rows = await asRole("anon", { role: "anon" }, (tx) => tx`select play_request.health() as h`);
      return new Response(JSON.stringify(rows[0].h), { headers });
    }
    const user = await userFromToken(req, true);
    const claims = claimsFor(user!);
    if (action === "get_progress") {
      const out = await asRole("authenticated", claims, async (tx) => {
        const tastings = await tx`select combo_id, rating, note, example, restaurant_id, dish, tasted_at, updated_at from play_request.tastings where user_id = ${user!.sub}`;
        const profile = await tx`select display_name from play_request.profiles where id = ${user!.sub}`;
        return { tastings, profile: profile[0] || null };
      });
      return new Response(JSON.stringify(out), { headers });
    }
    if (action === "save_profile") {
      const name = str(body.display_name, 80);
      await asRole("authenticated", claims, async (tx) => {
        await tx`
          insert into play_request.profiles (id, display_name)
          values (${user!.sub}, ${name})
          on conflict (id) do update set display_name = excluded.display_name, updated_at = now()`;
      });
      return new Response(JSON.stringify({ ok: true }), { headers });
    }
    if (action === "upsert_tasting") {
      const combo = str(body.combo_id, 80);
      if (!combo) throw new UserError("Missing combo.");
      const rating = body.rating == null || body.rating === "" ? null : Number(body.rating);
      if (rating != null && (!Number.isInteger(rating) || rating < 1 || rating > 5)) throw new UserError("Rating must be 1–5.");
      await asRole("authenticated", claims, async (tx) => {
        await tx`
          insert into play_request.tastings (user_id, combo_id, rating, note, example, restaurant_id, dish, tasted_at, updated_at)
          values (
            ${user!.sub}, ${combo}, ${rating},
            ${str(body.note, 2000)}, ${str(body.example, 200)}, ${str(body.restaurant_id, 80)}, ${str(body.dish, 160)},
            coalesce(${body.tasted_at || null}::timestamptz, now()), now()
          )
          on conflict (user_id, combo_id) do update set
            rating = excluded.rating, note = excluded.note, example = excluded.example,
            restaurant_id = excluded.restaurant_id, dish = excluded.dish, updated_at = now()`;
      });
      return new Response(JSON.stringify({ ok: true }), { headers });
    }
    if (action === "delete_tasting") {
      const combo = str(body.combo_id, 80);
      if (!combo) throw new UserError("Missing combo.");
      await asRole("authenticated", claims, async (tx) => {
        await tx`delete from play_request.tastings where user_id = ${user!.sub} and combo_id = ${combo}`;
      });
      return new Response(JSON.stringify({ ok: true }), { headers });
    }
    if (action === "delete_my_data") {
      await asRole("authenticated", claims, async (tx) => {
        await tx`select play_request.delete_my_data()`;
      });
      return new Response(JSON.stringify({ ok: true }), { headers });
    }
    if (action === "admin_stats") {
      const rows = await asRole("authenticated", claims, (tx) => tx`select play_request.admin_stats() as s`);
      return new Response(JSON.stringify({ stats: rows[0].s }), { headers });
    }
    throw new UserError("Unknown action.");
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Error";
    const status = e instanceof UserError ? 400 : /42501|Admins only|Not signed in|Please sign in/i.test(msg) ? 401 : 500;
    return new Response(JSON.stringify({ error: msg }), { status, headers });
  }
});
