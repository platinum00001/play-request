/* Restaurant directory + per-restaurant dish list. */
(function () {
  const PR = window.PR;
  const esc = function (s) { return PR.esc(s); };
  let data = null, filterTown = "all", filterSource = "all";

  function dishesFor(id) {
    return data.dishes.filter(function (d) { return d.restaurantId === id; });
  }

  function render() {
    const q = (document.getElementById("q") && document.getElementById("q").value || "").trim().toLowerCase();
    const list = data.restaurants.filter(function (r) {
      if (filterTown !== "all" && r.town !== filterTown) return false;
      const ds = dishesFor(r.id);
      if (filterSource === "menu" && !ds.some(function (d) { return d.source === "menu"; })) return false;
      if (q) {
        const blob = (r.name + " " + r.town + " " + r.area + " " + r.category + " " + ds.map(function (d) { return d.dish; }).join(" ")).toLowerCase();
        if (blob.indexOf(q) === -1) return false;
      }
      return true;
    });
    const el = document.getElementById("rgrid");
    const count = document.getElementById("rcount");
    if (count) count.textContent = list.length + " place" + (list.length === 1 ? "" : "s");
    el.innerHTML = list.map(function (r) {
      const ds = dishesFor(r.id);
      const menuN = ds.filter(function (d) { return d.source === "menu"; }).length;
      const sub = ds.length
        ? (menuN ? menuN + " from the menu" : ds.length + " suggested") + (ds.length !== menuN && menuN ? ", " + (ds.length - menuN) + " suggested" : "")
        : "No mapped dishes yet";
      return '<a class="rcard" href="restaurants.html?id=' + encodeURIComponent(r.id) + '">' +
        (r.featured ? '<span class="feat-flag">Featured</span>' : "") +
        '<span class="where">' + esc(r.town) + (r.area && r.area !== r.town ? " · " + esc(r.area) : "") + "</span>" +
        "<h3>" + esc(r.name) + "</h3>" +
        "<p>" + esc(r.category || "") + (r.description ? " — " + esc(r.description) : "") + "</p>" +
        "<p><small>" + esc(sub) + "</small></p></a>";
    }).join("") || "<p>No places match those filters.</p>";
  }

  function showOne(id) {
    const r = data.restaurantsById[id];
    const box = document.getElementById("one");
    const dir = document.getElementById("directory");
    if (!r || !box) return;
    dir.hidden = true;
    box.hidden = false;
    const ds = dishesFor(r.id);
    const maps = r.lat
      ? "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(r.name + " " + r.address)
      : "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(r.address || r.name);
    box.innerHTML = '<p><a class="back-link" href="restaurants.html">← All restaurants</a></p>' +
      (r.featured ? '<span class="feat-flag">Featured</span>' : "") +
      '<p class="kicker">' + esc(r.town) + (r.area ? " · " + esc(r.area) : "") + "</p>" +
      "<h1>" + esc(r.name) + "</h1>" +
      "<p>" + esc(r.description || r.category || "") + "</p>" +
      "<p>" + esc(r.address || "") + (r.phone ? " · " + esc(r.phone) : "") + (r.hours ? "<br>" + esc(r.hours) : "") + "</p>" +
      "<p>" + (r.website ? '<a href="' + esc(r.website) + '" target="_blank" rel="noopener">Website</a> · ' : "") +
      '<a href="' + maps + '" target="_blank" rel="noopener">Map</a></p>' +
      "<h2>Dishes for Play Request</h2>" +
      (ds.length ? ds.map(function (d) {
        const combo = data.combosById[d.comboId];
        const tag = d.source === "menu" ? '<small class="tag tag-menu">From the menu</small>' : '<small class="tag tag-suggested">Suggested</small>';
        return '<article class="dish"><b>' + esc(d.dish) + "</b> " + tag +
          "<div>For <a href=\"index.html?combo=" + encodeURIComponent(d.comboId) + '">' + esc(combo ? combo.name : d.comboId) + "</a></div>" +
          (d.note ? "<p>" + esc(d.note) + "</p>" : "") + "</article>";
      }).join("") : "<p>We have not mapped dishes here yet. If you try something that fits a combo, log it on the board and mention this restaurant.</p>");
  }

  document.addEventListener("DOMContentLoaded", async function () {
    data = await PR.loadData();
    const id = new URLSearchParams(location.search).get("id");
    if (id && data.restaurantsById[id]) { showOne(id); return; }
    document.querySelectorAll("[data-town]").forEach(function (b) {
      b.addEventListener("click", function () {
        filterTown = b.getAttribute("data-town");
        document.querySelectorAll("[data-town]").forEach(function (x) { x.classList.toggle("on", x === b); });
        render();
      });
    });
    document.querySelectorAll("[data-source]").forEach(function (b) {
      b.addEventListener("click", function () {
        filterSource = b.getAttribute("data-source");
        document.querySelectorAll("[data-source]").forEach(function (x) { x.classList.toggle("on", x === b); });
        render();
      });
    });
    const q = document.getElementById("q");
    if (q) q.addEventListener("input", render);
    render();
  });
})();
