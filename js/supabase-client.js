/* Supabase loader. Queries go to schema play_request; if the schema is not exposed, we use the edge function. */
(function () {
  const PR = (window.PR = window.PR || {});
  const CDN = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/dist/umd/supabase.js";
  let promise = null, settingsPromise = null;
  PR.supabaseConfigured = function () {
    const c = PR.cfg();
    return !!(c.SUPABASE_URL && c.SUPABASE_ANON_KEY && /^https:\/\//.test(c.SUPABASE_URL));
  };
  PR.getSupabase = function () {
    if (promise) return promise;
    if (!PR.supabaseConfigured()) return (promise = Promise.resolve(null));
    promise = new Promise(function (resolve) {
      const s = document.createElement("script");
      s.src = CDN; s.crossOrigin = "anonymous";
      s.onload = function () {
        try {
          const c = PR.cfg();
          resolve(window.supabase.createClient(c.SUPABASE_URL, c.SUPABASE_ANON_KEY, {
            db: { schema: c.SUPABASE_SCHEMA || "play_request" },
            auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
          }));
        } catch (e) { console.warn(e); resolve(null); }
      };
      s.onerror = function () { resolve(null); };
      document.head.appendChild(s);
    });
    return promise;
  };
  PR.getUser = async function () {
    const sb = await PR.getSupabase();
    if (!sb) return { sb: null, user: null, session: null };
    const { data } = await sb.auth.getSession();
    return { sb: sb, user: data && data.session ? data.session.user : null, session: data ? data.session : null };
  };
  PR.authSettings = function () {
    if (settingsPromise) return settingsPromise;
    const c = PR.cfg();
    if (!PR.supabaseConfigured()) return (settingsPromise = Promise.resolve(null));
    settingsPromise = fetch(c.SUPABASE_URL + "/auth/v1/settings", { headers: { apikey: c.SUPABASE_ANON_KEY } })
      .then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    return settingsPromise;
  };
  PR.schemaNotReady = function (error) {
    if (!error) return false;
    return /PGRST106|Invalid schema|schema must be one of/i.test(String(error.message || "") + " " + String(error.code || ""));
  };
  PR.friendlyError = function (error) {
    if (!error) return "";
    const m = String(error.message || error);
    if (PR.schemaNotReady(error)) return "Cloud saving is almost ready. Your progress is still saved on this device.";
    if (/JWT|not authenticated|sign in first/i.test(m)) return "Please sign in again.";
    if (/Failed to fetch|NetworkError/i.test(m)) return "We couldn't reach the server. Check your connection and try again.";
    return m;
  };
  PR.api = async function (action, body) {
    const c = PR.cfg();
    const { session } = await PR.getUser();
    const url = c.SUPABASE_URL + "/functions/v1/" + (c.API_FUNCTION || "play-request-api");
    const headers = { "content-type": "application/json", apikey: c.SUPABASE_ANON_KEY };
    if (session && session.access_token) headers.authorization = "Bearer " + session.access_token;
    const r = await fetch(url, { method: "POST", headers: headers, body: JSON.stringify(Object.assign({ action: action }, body || {})) });
    const data = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error(data.error || data.message || "Request failed");
    return data;
  };
})();
