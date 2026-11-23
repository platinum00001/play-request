/* Main Play Request board: pyramid, unlocks, tasting panel. */
(function () {
  const PR = window.PR;
  const esc = function (s) { return PR.esc(s); };
  let data = null;

  function stateOf(combo, tried) {
    if (tried.has(combo.id)) return "tried";
    if (PR.isUnlocked(combo, tried, data.combosById)) return "open";
    return "locked";
  }

  function renderProgress() {
    const state = PR.loadLocal();
    const tried = PR.triedSet(state);
    const n = tried.size;
    const pct = Math.round((n / 31) * 100);
    const bar = document.getElementById("progress-bar");
    const label = document.getElementById("progress-label");
    if (bar) bar.style.width = pct + "%";
    if (label) label.textContent = n + " of 31 tasted";
    const box = document.getElementById("badges");
    if (box) {
      box.innerHTML = PR.badges(data.combos, tried).map(function (b) {
        return '<span class="badge' + (b.on ? " on" : "") + '" title="' + esc(b.hint) + '">' + esc(b.name) + "</span>";
      }).join("");
    }
    const start = document.getElementById("start-cta");
    if (start) start.hidden = n > 0;
  }

  function renderBoard() {
    const state = PR.loadLocal();
    const tried = PR.triedSet(state);
    const root = document.getElementById("pyramid");
    if (!root) return;
    const levels = [1, 2, 3, 4, 5];
    root.innerHTML = levels.map(function (lv) {
      const items = data.combos.filter(function (c) { return c.level === lv; });
      const done = items.filter(function (c) { return tried.has(c.id); }).length;
      const names = { 1: "Level 1 — Singles", 2: "Level 2 — Pairs", 3: "Level 3 — Trios", 4: "Level 4 — Quads", 5: "Level 5 — The Peak" };
      return '<section class="level" data-level="' + lv + '"><div class="level-head"><h3>' + names[lv] + '</h3><span class="meta">' + done + " / " + items.length + ' tried</span></div><div class="nodes">' +
        items.map(function (c) {
          const st = stateOf(c, tried);
          const rating = (state.tastings[c.id] && state.tastings[c.id].rating) ? " · " + state.tastings[c.id].rating + "★" : "";
          const label = st === "tried" ? "Tried" + rating : st === "open" ? "Open — try this" : "Locked";
          const dots = c.colors.map(function (col) { return '<span class="dot" style="background:' + col + '"></span>'; }).join("");
          return '<button type="button" class="node is-' + st + '" data-id="' + esc(c.id) + '" aria-label="' + esc(c.name) + ', ' + label + '">' +
            (st === "locked" ? '<span class="lock" aria-hidden="true">🔒</span>' : "") +
            '<span class="dots">' + dots + "</span>" +
            '<span class="name">' + esc(c.name) + "</span>" +
            '<span class="state">' + label + "</span></button>";
        }).join("") + "</div></section>";
    }).join("");
    root.querySelectorAll(".node").forEach(function (btn) {
      btn.addEventListener("click", function () { openPanel(btn.getAttribute("data-id")); });
    });
    renderProgress();
    const q = new URLSearchParams(location.search).get("combo");
    const hash = (location.hash || "").replace(/^#/, "");
    if (q) openPanel(q);
    else if (hash && data.combosById[hash]) openPanel(hash);
  }

  function dishesFor(comboId) {
    return data.dishes.filter(function (d) { return d.comboId === comboId; })
      .sort(function (a, b) {
        if (a.featured !== b.featured) return a.featured ? -1 : 1;
        if (a.source !== b.source) return a.source === "menu" ? -1 : 1;
        return a.restaurantName.localeCompare(b.restaurantName);
      });
  }

  function openPanel(id) {
    const combo = data.combosById[id];
    if (!combo) return;
    const panel = document.getElementById("panel");
    const back = document.getElementById("backdrop");
    const state = PR.loadLocal();
    const tried = PR.triedSet(state);
    const st = stateOf(combo, tried);
    const tasting = state.tastings[id] || {};
    const parents = PR.unlockParents(combo, data.combosById);
    const next = PR.nextCombos(combo, data.combos);
    const chips = combo.tastes.map(function (t, i) {
      return '<span class="chip" style="background:' + combo.colors[i] + '">' + esc(t) + "</span>";
    }).join("");
    let lock = "";
    if (st === "locked") {
      const opts = parents.map(function (p) { return p.name; });
      lock = '<div class="lock-hint"><strong>Not open yet.</strong> Try any combo that this one extends by a single flavor — you only need one path, not every square. ' +
        (opts.length ? "Try one of: " + opts.map(esc).join("; ") + "." : "") + "</div>";
    }
    const classics = (combo.classics || []).map(function (x) { return '<div class="classic">' + esc(x) + "</div>"; }).join("") || "<p>Look for this combination in any kitchen you trust.</p>";
    const recs = dishesFor(id).map(function (d) {
      const tag = d.source === "menu" ? '<small class="tag tag-menu">From the menu</small>' : '<small class="tag tag-suggested">Suggested</small>';
      const link = d.website ? ' · <a href="' + esc(d.website) + '" target="_blank" rel="noopener">Website</a>' : "";
      return '<article class="dish"><b>' + esc(d.dish) + "</b>" + tag +
        "<div>" + esc(d.restaurantName) + " · " + esc(d.town) + (d.area && d.area !== d.town ? " (" + esc(d.area) + ")" : "") + link + "</div>" +
        (d.note ? "<p>" + esc(d.note) + "</p>" : "") + "</article>";
    }).join("") || "<p>No local dish mapped yet — use a classic example, or note whatever you tried.</p>";

    const options = data.restaurants.map(function (r) {
      return '<option value="' + esc(r.id) + '"' + (tasting.restaurantId === r.id ? " selected" : "") + ">" + esc(r.name) + " (" + esc(r.town) + ")</option>";
    }).join("");

    const form = st === "locked" ? "" : '<form class="taste" id="taste-form">' +
      '<p class="lab">How was it? (optional)</p><div class="stars" role="group" aria-label="Rating">' +
      [1,2,3,4,5].map(function (n) { return '<button type="button" data-n="' + n + '" class="' + ((tasting.rating || 0) >= n ? "on" : "") + '" aria-label="' + n + ' star">' + n + "★</button>"; }).join("") +
      '</div><input type="hidden" name="rating" value="' + (tasting.rating || "") + '">' +
      '<label for="example">What did you try? (food or drink)</label>' +
      '<input type="text" id="example" name="example" maxlength="200" value="' + esc(tasting.example || tasting.dish || "") + '" placeholder="e.g. Island Lime Cooler">' +
      '<label for="restaurant">Restaurant (optional)</label>' +
      '<select id="restaurant" name="restaurant"><option value="">—</option>' + options + "</select>" +
      '<label for="note">Note (optional)</label>' +
      '<textarea id="note" name="note" maxlength="2000" placeholder="Where you had it, who you were with, what surprised you…">' + esc(tasting.note || "") + "</textarea>" +
      '<div class="form-actions"><button class="btn" type="submit">' + (tasting.at ? "Update tasting" : "I tried this") + "</button>" +
      (tasting.at ? '<button class="btn btn-line" type="button" id="untaste">Remove tasting</button>' : "") +
      "</div></form>";

    const nextHtml = next.length ? "<h3>This unlocks</h3><p>Once you try it, these open — each adds just one flavor:</p><ul>" +
      next.map(function (c) { return "<li>" + esc(c.name) + "</li>"; }).join("") + "</ul>" : "";

    panel.innerHTML = '<header><div><p class="kicker">Level ' + combo.level + '</p><h2 id="panel-title">' + esc(combo.name) + "</h2></div>" +
      '<button type="button" class="close" aria-label="Close">&times;</button></header>' +
      '<div class="chips">' + chips + "</div>" +
      (combo.blurb ? "<p>" + esc(combo.blurb) + "</p>" : "") +
      lock + form +
      "<h3>Classic examples</h3>" + classics +
      "<h3>Around Falmouth &amp; Woods Hole</h3><p>Dishes marked <em>From the menu</em> use a name from a published menu or official site (checked 23 Nov 2026, America/New_York). <em>Suggested</em> items are informed guesses — confirm before you go.</p>" +
      recs + nextHtml;

    panel.classList.add("show");
    back.classList.add("show");
    back.hidden = false;
    panel.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    history.replaceState(null, "", "?combo=" + encodeURIComponent(id));

    panel.querySelector(".close").addEventListener("click", closePanel);
    const formEl = panel.querySelector("#taste-form");
    if (formEl) {
      formEl.querySelectorAll(".stars button").forEach(function (b) {
        b.addEventListener("click", function () {
          const n = Number(b.getAttribute("data-n"));
          formEl.rating.value = n;
          formEl.querySelectorAll(".stars button").forEach(function (x) {
            x.classList.toggle("on", Number(x.getAttribute("data-n")) <= n);
          });
        });
      });
      formEl.addEventListener("submit", async function (e) {
        e.preventDefault();
        const rest = formEl.restaurant.value;
        await PR.recordTasting(id, {
          rating: formEl.rating.value ? Number(formEl.rating.value) : null,
          note: formEl.note.value.trim(),
          example: formEl.example.value.trim(),
          restaurantId: rest,
          dish: formEl.example.value.trim()
        });
        closePanel();
        renderBoard();
      });
      const un = panel.querySelector("#untaste");
      if (un) un.addEventListener("click", async function () {
        if (!confirm("Remove this tasting? You can add it again later.")) return;
        await PR.clearTasting(id);
        closePanel();
        renderBoard();
      });
    }
  }

  function closePanel() {
    const panel = document.getElementById("panel");
    const back = document.getElementById("backdrop");
    panel.classList.remove("show");
    back.classList.remove("show");
    panel.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (/\?combo=/.test(location.search)) history.replaceState(null, "", location.pathname);
  }

  async function boot() {
    data = await PR.loadData();
    renderBoard();
    document.getElementById("backdrop").addEventListener("click", closePanel);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closePanel(); });
    document.getElementById("start-cta") && document.getElementById("start-cta").addEventListener("click", function () {
      document.querySelector('.level[data-level="1"]').scrollIntoView({ behavior: "smooth", block: "start" });
    });
    window.addEventListener("pr-progress", renderBoard);
    // If already signed in, merge cloud progress quietly.
    PR.getUser().then(function (u) { if (u.user) PR.syncOnLogin().then(renderBoard); });
  }
  document.addEventListener("DOMContentLoaded", boot);
})();
