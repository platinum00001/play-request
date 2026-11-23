/* Play Request — tastes, combos, unlock rules, and data loading. */
(function (root) {
  const PR = (root.PR = root.PR || {});
  const ORDER = ["bitter", "salty", "sour", "sweet", "umami"];

  PR.comboId = function (tastes) {
    return tastes.slice().sort().join("-");
  };

  PR.isUnlocked = function (combo, triedIds, byId) {
    if (!combo) return false;
    if (combo.level === 1) return true;
    const want = new Set(combo.tastes);
    const tried = triedIds instanceof Set ? triedIds : new Set(triedIds || []);
    for (const tid of tried) {
      const t = byId[tid];
      if (!t) continue;
      if (t.tastes.length !== combo.tastes.length - 1) continue;
      if (t.tastes.every(function (x) { return want.has(x); })) return true;
    }
    return false;
  };

  PR.unlockParents = function (combo, byId) {
    if (!combo || combo.level <= 1) return [];
    return combo.tastes.map(function (leaveOut) {
      return PR.comboId(combo.tastes.filter(function (t) { return t !== leaveOut; }));
    }).map(function (id) { return byId[id]; }).filter(Boolean);
  };

  PR.nextCombos = function (combo, all) {
    if (!combo) return [];
    return all.filter(function (c) {
      return c.level === combo.level + 1 && combo.tastes.every(function (t) { return c.tastes.indexOf(t) !== -1; });
    });
  };

  PR.triedSet = function (state) {
    const s = new Set();
    const t = (state && state.tastings) || {};
    Object.keys(t).forEach(function (k) { if (t[k] && t[k].at) s.add(k); });
    return s;
  };

  PR.levelCounts = function (combos, tried) {
    const out = { 1: { total: 0, tried: 0 }, 2: { total: 0, tried: 0 }, 3: { total: 0, tried: 0 }, 4: { total: 0, tried: 0 }, 5: { total: 0, tried: 0 } };
    combos.forEach(function (c) {
      out[c.level].total++;
      if (tried.has(c.id)) out[c.level].tried++;
    });
    return out;
  };

  PR.badges = function (combos, tried) {
    const n = tried.size;
    const lv = PR.levelCounts(combos, tried);
    const firstOf = function (level) { return lv[level].tried > 0; };
    const allOf = function (level) { return lv[level].tried === lv[level].total && lv[level].total > 0; };
    return [
      { id: "first-sip", name: "First sip", on: n >= 1, hint: "Try your first flavor." },
      { id: "pair", name: "Pair explorer", on: firstOf(2), hint: "Try a two-taste combo." },
      { id: "trio", name: "Trio", on: firstOf(3), hint: "Extend a pair by one flavor." },
      { id: "quad", name: "Quad", on: firstOf(4), hint: "Extend a trio by one flavor." },
      { id: "peak", name: "The Peak", on: firstOf(5), hint: "Taste all five in one dish." },
      { id: "singles-clean", name: "All five starts", on: allOf(1), hint: "Try every single flavor." },
      { id: "pairs-clean", name: "Every pair", on: allOf(2), hint: "Try all ten pairs." },
      { id: "complete", name: "Flavor master", on: n >= 31, hint: "Try all 31 combinations." }
    ];
  };

  let cache = null;
  PR.loadData = function () {
    if (cache) return cache;
    const base = new URL("../data/", document.currentScript ? document.currentScript.src : document.querySelector('script[src*="data.js"]').src);
    // data is loaded from pages via PR.dataUrl, set in common.js
    cache = Promise.all([
      fetch(PR.dataUrl("tastes.json")).then(function (r) { return r.json(); }),
      fetch(PR.dataUrl("combos.json")).then(function (r) { return r.json(); }),
      fetch(PR.dataUrl("restaurants.json")).then(function (r) { return r.json(); }),
      fetch(PR.dataUrl("dishes.json")).then(function (r) { return r.json(); })
    ]).then(function (arr) {
      const tastes = arr[0], combos = arr[1], restaurants = arr[2], dishes = arr[3];
      const combosById = {};
      combos.forEach(function (c) { combosById[c.id] = c; });
      const restaurantsById = {};
      restaurants.forEach(function (r) { restaurantsById[r.id] = r; });
      return { tastes: tastes, combos: combos, restaurants: restaurants, dishes: dishes, combosById: combosById, restaurantsById: restaurantsById };
    });
    return cache;
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { comboId: PR.comboId, isUnlocked: PR.isUnlocked, unlockParents: PR.unlockParents, nextCombos: PR.nextCombos, triedSet: PR.triedSet, badges: PR.badges, levelCounts: PR.levelCounts };
  }
})(typeof window !== "undefined" ? window : globalThis);
