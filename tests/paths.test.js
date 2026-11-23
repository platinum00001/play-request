// Run: node tests/paths.test.js
const fs = require("fs"), path = require("path"), assert = require("assert");
const root = path.join(__dirname, "..");
const html = fs.readdirSync(root).filter((f) => f.endsWith(".html"));
const read = (f) => fs.readFileSync(path.join(root, f), "utf8");
let links = 0;
for (const f of html) {
  const s = read(f);
  if (f !== "404.html") {
    const bad = s.match(/(?:href|src|action)=["']\/(?!\/)[^"']*/g) || [];
    assert.deepStrictEqual(bad, [], f + " has root-absolute paths: " + bad.join(", "));
    assert.ok(!/url\(\s*["']?\/(?!\/)/.test(s), f + " has a root-absolute CSS url()");
    for (const m of s.matchAll(/(?:href|src)="([^"#?:]*)(?:[?#][^"]*)?"/g)) {
      if (!m[1] || /^(mailto|tel|https?|data)/.test(m[1])) continue;
      let t = path.join(root, path.dirname(f), m[1]);
      if (m[1].endsWith("/") || m[1] === "." || m[1] === "..") t = path.join(t, "index.html");
      assert.ok(fs.existsSync(t), f + " links to missing file " + m[1]);
      links++;
    }
  }
  assert.ok(/<title>[^<]{8,}<\/title>/.test(s) && /name="description" content="[^"]{10,}"/.test(s), f + " needs title + description");
  assert.ok(/og:image" content="https:\/\/[^"]+\/og[-\w]*\.jpg"/.test(s) && /twitter:card" content="summary_large_image"/.test(s), f + " missing share tags");
  if (f !== "404.html") {
    assert.ok(/privacy\.html/.test(s) && /terms\.html/.test(s), f + " missing privacy/terms links");
    assert.ok(/<link rel="canonical" href="https:\/\//.test(s), f + " canonical");
  }
}
assert.ok(!/href="(?!https?:|mailto:|tel:|#)[^"]+"/.test(read("404.html")), "404 must use absolute links");
for (const f of ["staff.html", "account.html", "404.html"]) {
  assert.ok(/name="robots" content="noindex/.test(read(f)), f + " must be noindex");
}
const robots = read("robots.txt"), sitemap = read("sitemap.xml");
for (const f of ["staff.html", "account.html"]) {
  assert.ok(robots.includes("Disallow: /" + f), "robots disallows " + f);
  assert.ok(!sitemap.includes(f), "sitemap excludes " + f);
}
assert.ok((sitemap.match(/<url>/g) || []).length >= 6, "sitemap lists public pages");
assert.ok(/id="data-deletion"/.test(read("privacy.html")), "privacy.html needs #data-deletion");
const cfg = read("config.js");
const code = cfg.replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, "");
assert.ok(!/service_role|sb_secret_/.test(code), "config.js must not contain a secret key");
assert.ok(/SUPABASE_ANON_KEY:\s*"sb_publishable_/.test(cfg), "only the publishable key belongs in config.js");
for (const f of ["sitemap.xml", "robots.txt", "og.jpg", "favicon.svg", "play-request-board-game.pdf"]) {
  assert.ok(fs.existsSync(path.join(root, f)), f + " missing");
}
for (const f of ["data/restaurants.json", "data/dishes.json", "data/combos.json", "css/styles.css"]) {
  assert.ok(fs.existsSync(path.join(root, f)), f + " missing");
}
const dishes = JSON.parse(read("data/dishes.json"));
const combos = JSON.parse(read("data/combos.json"));
assert.strictEqual(combos.length, 31);
const covered = new Set(dishes.map((d) => d.comboId));
for (const c of combos) assert.ok(covered.has(c.id), "no dish for " + c.id);
assert.ok(dishes.some((d) => d.source === "menu"), "need menu-sourced dishes");
assert.ok(dishes.some((d) => d.source === "suggested"), "need suggested dishes");
const css = read("css/styles.css");
assert.ok(!/url\(\s*["']?\/(?!\/)/.test(css), "css root-absolute url");
console.log("✓", html.length, "pages sub-path safe;", links, "local links resolve; 31 combos covered; no secret key");
