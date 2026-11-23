// Run: node tests/unlock.test.js
const assert = require("assert");
const path = require("path");
const { isUnlocked, comboId, nextCombos, triedSet } = require(path.join(__dirname, "..", "js", "data.js"));

const tastes = ["sweet", "sour", "salty", "bitter", "umami"];
function combo(tastesArr) {
  const id = comboId(tastesArr);
  return { id, tastes: tastesArr.slice().sort(), level: tastesArr.length };
}
const all = [];
function rec(prefix, start) {
  if (prefix.length) all.push(combo(prefix));
  for (let i = start; i < tastes.length; i++) rec(prefix.concat(tastes[i]), i + 1);
}
rec([], 0);
const byId = Object.fromEntries(all.map((c) => [c.id, c]));
assert.strictEqual(all.length, 31);

const sweet = byId.sweet;
assert.ok(isUnlocked(sweet, new Set(), byId), "singles start unlocked");

const ss = byId["sour-sweet"];
assert.ok(!isUnlocked(ss, new Set(), byId), "pairs start locked");
assert.ok(isUnlocked(ss, new Set(["sweet"]), byId), "trying Sweet unlocks Sweet+Sour");
assert.ok(isUnlocked(ss, new Set(["sour"]), byId), "trying Sour also unlocks Sweet+Sour");
assert.ok(!isUnlocked(ss, new Set(["salty"]), byId), "unrelated single does not unlock Sweet+Sour");

const trio = byId["salty-sour-sweet"];
assert.ok(!isUnlocked(trio, new Set(["sweet"]), byId), "a single does not unlock a trio");
assert.ok(isUnlocked(trio, new Set(["sour-sweet"]), byId), "Sweet+Sour unlocks Sweet+Sour+Salty");
assert.ok(!isUnlocked(trio, new Set(["bitter-sweet"]), byId), "a pair missing a needed taste does not unlock the trio");

const peak = byId["bitter-salty-sour-sweet-umami"];
assert.ok(!isUnlocked(peak, new Set(["salty-sour-sweet"]), byId), "a trio does not unlock the peak");
assert.ok(isUnlocked(peak, new Set(["bitter-salty-sour-sweet"]), byId), "any matching quad unlocks the peak");

// You can reach the peak in five tastings
const pathIds = ["sweet", "sour-sweet", "salty-sour-sweet", "bitter-salty-sour-sweet", "bitter-salty-sour-sweet-umami"];
const tried = new Set();
for (const id of pathIds) {
  assert.ok(isUnlocked(byId[id], tried, byId), "path step should be open: " + id);
  tried.add(id);
}
assert.strictEqual(tried.size, 5);
assert.ok(!isUnlocked(byId["salty-umami"], tried, byId), "a side branch you didn't walk stays locked");

const nxt = nextCombos(byId.sweet, all);
assert.strictEqual(nxt.length, 4);
assert.ok(nxt.every((c) => c.level === 2 && c.tastes.includes("sweet")));

const state = { tastings: { sweet: { at: "2026-11-23" } } };
assert.ok(triedSet(state).has("sweet"));
console.log("✓ unlock rules: singles open, extend-by-one, five-step peak path, side branches stay locked");
