/* localStorage progress, with optional cloud sync after sign-in. */
(function () {
  const PR = (window.PR = window.PR || {});
  const KEY = "playRequest.v1";
  const COOKIE = "play_request_has_progress";

  function empty() { return { version: 1, displayName: "", tastings: {}, updatedAt: null }; }

  PR.loadLocal = function () {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return empty();
      const d = JSON.parse(raw);
      if (!d || typeof d !== "object") return empty();
      d.tastings = d.tastings || {};
      d.displayName = d.displayName || "";
      return d;
    } catch (e) { return empty(); }
  };

  function flagCookie(has) {
    const max = has ? "max-age=" + (60 * 60 * 24 * 400) : "max-age=0";
    document.cookie = COOKIE + "=" + (has ? "1" : "") + ";path=/;SameSite=Lax;" + max;
  }

  PR.saveLocal = function (state) {
    state.updatedAt = new Date().toISOString();
    localStorage.setItem(KEY, JSON.stringify(state));
    flagCookie(Object.keys(state.tastings || {}).length > 0);
    window.dispatchEvent(new CustomEvent("pr-progress", { detail: state }));
    return state;
  };

  PR.mergeStates = function (a, b) {
    const out = empty();
    out.displayName = (b && b.displayName) || (a && a.displayName) || "";
    const tastings = {};
    [a, b].forEach(function (src) {
      const t = (src && src.tastings) || {};
      Object.keys(t).forEach(function (id) {
        const cur = tastings[id], nxt = t[id];
        if (!nxt) return;
        if (!cur) { tastings[id] = Object.assign({}, nxt); return; }
        const ct = cur.updatedAt || cur.at || "";
        const nt = nxt.updatedAt || nxt.at || "";
        tastings[id] = nt >= ct ? Object.assign({}, cur, nxt) : Object.assign({}, nxt, cur);
      });
    });
    out.tastings = tastings;
    return out;
  };

  function rowsToState(rows, displayName) {
    const s = empty();
    s.displayName = displayName || "";
    (rows || []).forEach(function (r) {
      s.tastings[r.combo_id] = {
        at: r.tasted_at || r.updated_at,
        updatedAt: r.updated_at || r.tasted_at,
        rating: r.rating,
        note: r.note || "",
        example: r.example || "",
        restaurantId: r.restaurant_id || "",
        dish: r.dish || ""
      };
    });
    return s;
  }

  PR.pullCloud = async function () {
    const { sb, user } = await PR.getUser();
    if (!sb || !user) return null;
    // Prefer direct schema access; fall back to the edge function if the schema is not exposed.
    try {
      const { data, error } = await sb.from("tastings").select("combo_id,rating,note,example,restaurant_id,dish,tasted_at,updated_at");
      if (error) throw error;
      let name = "";
      const prof = await sb.from("profiles").select("display_name").eq("id", user.id).maybeSingle();
      if (!prof.error && prof.data) name = prof.data.display_name || "";
      return rowsToState(data, name);
    } catch (e) {
      if (!PR.schemaNotReady(e) && !/Failed to fetch/i.test(String(e.message || e))) {
        // try function anyway
      }
      try {
        const res = await PR.api("get_progress");
        return rowsToState(res.tastings || [], (res.profile && res.profile.display_name) || "");
      } catch (e2) {
        console.warn("Cloud pull failed", e, e2);
        return null;
      }
    }
  };

  PR.ensureProfile = async function (displayName) {
    const { sb, user } = await PR.getUser();
    if (!sb || !user) return;
    const name = displayName || (user.user_metadata && (user.user_metadata.display_name || user.user_metadata.full_name)) || "";
    try {
      await sb.from("profiles").upsert({ id: user.id, display_name: name, updated_at: new Date().toISOString() });
    } catch (e) {
      if (PR.schemaNotReady(e)) {
        try { await PR.api("save_profile", { display_name: name }); } catch (e2) {}
      }
    }
  };

  PR.pushTasting = async function (comboId, tasting) {
    const { sb, user } = await PR.getUser();
    if (!sb || !user) return;
    const row = {
      combo_id: comboId,
      rating: tasting.rating || null,
      note: tasting.note || null,
      example: tasting.example || null,
      restaurant_id: tasting.restaurantId || null,
      dish: tasting.dish || null,
      tasted_at: tasting.at,
      updated_at: tasting.updatedAt || tasting.at
    };
    try {
      const { error } = await sb.from("tastings").upsert(row, { onConflict: "user_id,combo_id" });
      if (error) throw error;
    } catch (e) {
      try { await PR.api("upsert_tasting", row); } catch (e2) { console.warn("Cloud save failed", e, e2); }
    }
  };

  PR.deleteTastingCloud = async function (comboId) {
    const { sb, user } = await PR.getUser();
    if (!sb || !user) return;
    try {
      const { error } = await sb.from("tastings").delete().eq("combo_id", comboId);
      if (error) throw error;
    } catch (e) {
      try { await PR.api("delete_tasting", { combo_id: comboId }); } catch (e2) { console.warn(e, e2); }
    }
  };

  PR.syncOnLogin = async function () {
    const local = PR.loadLocal();
    const cloud = await PR.pullCloud();
    if (!cloud) { await PR.ensureProfile(local.displayName); return local; }
    const merged = PR.mergeStates(local, cloud);
    PR.saveLocal(merged);
    await PR.ensureProfile(merged.displayName);
    // Push any local-only or newer rows
    const { sb, user } = await PR.getUser();
    if (sb && user) {
      for (const id of Object.keys(merged.tastings)) {
        await PR.pushTasting(id, merged.tastings[id]);
      }
    }
    return merged;
  };

  PR.recordTasting = async function (comboId, fields) {
    const state = PR.loadLocal();
    const now = new Date().toISOString();
    const prev = state.tastings[comboId] || {};
    state.tastings[comboId] = Object.assign({}, prev, fields, { at: prev.at || now, updatedAt: now });
    PR.saveLocal(state);
    await PR.pushTasting(comboId, state.tastings[comboId]);
    return state;
  };

  PR.clearTasting = async function (comboId) {
    const state = PR.loadLocal();
    delete state.tastings[comboId];
    PR.saveLocal(state);
    await PR.deleteTastingCloud(comboId);
    return state;
  };
})();
