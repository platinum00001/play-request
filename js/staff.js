/* Staff counts. Admins only, via RPC or the edge function. */
(function () {
  const PR = window.PR;
  const esc = PR.esc;
  async function load() {
    const box = document.getElementById("staff-area");
    const { sb, user } = await PR.getUser();
    if (!sb || !user) { box.innerHTML = '<div class="notice info">Please <a href="account.html">sign in</a> with an admin account.</div>'; return; }
    let stats = null, err = null;
    try {
      const { data, error } = await sb.rpc("admin_stats");
      if (error) throw error;
      stats = data;
    } catch (e) {
      try { stats = (await PR.api("admin_stats")).stats; }
      catch (e2) { err = e; }
    }
    if (!stats) {
      box.innerHTML = '<div class="notice err">Staff only. If you should have access, run the admin SQL in docs/SETUP.md.<br>' + esc(PR.friendlyError(err)) + "</div>";
      return;
    }
    box.innerHTML = '<div class="card"><h2>Play Request counts</h2>' +
      "<p>Members: <strong>" + esc(stats.members) + "</strong></p>" +
      "<p>Tastings saved: <strong>" + esc(stats.tastings) + "</strong></p>" +
      (stats.popular && stats.popular.length ? "<h3>Most logged combos</h3><table class=\"data\"><thead><tr><th>Combo</th><th>Count</th></tr></thead><tbody>" +
        stats.popular.map(function (r) { return "<tr><td>" + esc(r.combo_id) + "</td><td>" + esc(r.n) + "</td></tr>"; }).join("") + "</tbody></table>" : "") +
      '<p style="margin-top:16px"><button class="btn btn-line" type="button" id="csv">Download tastings CSV</button></p></div>';
    const btn = document.getElementById("csv");
    if (btn) btn.addEventListener("click", async function () {
      try {
        let rows = [];
        const { data, error } = await sb.from("tastings").select("combo_id,rating,example,dish,restaurant_id,tasted_at");
        if (error) throw error;
        rows = data;
        const header = "combo_id,rating,example,dish,restaurant_id,tasted_at";
        const body = rows.map(function (r) {
          return [r.combo_id, r.rating, r.example, r.dish, r.restaurant_id, r.tasted_at].map(function (v) {
            return '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
          }).join(",");
        }).join("\n");
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([header + "\n" + body], { type: "text/csv" }));
        a.download = "play-request-tastings.csv";
        a.click();
      } catch (e) { alert("Could not download: " + PR.friendlyError(e)); }
    });
  }
  document.addEventListener("DOMContentLoaded", load);
})();
