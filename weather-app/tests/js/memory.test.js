const assert = require("assert");
const { makeEl, loadScript, fakeStorage } = require("./fakedom");

const IDS = ["recent", "recent-list", "recent-clear", "q"];
const SCRIPT = "app/static/js/memory.js";
const tick = () => new Promise((r) => setTimeout(r, 5));

function option(label, lat, lon) {
  const o = makeEl();
  o.dataset = { label, lat: String(lat), lon: String(lon) };
  o.matchers = ['[role="option"]'];
  return o;
}
const chipLabels = (env) => env.els["recent-list"].children.map((li) => li.children[0].textContent);
const stored = (store) => JSON.parse(store.data["weather.recent"]);

(async () => {
  // starts hidden when there is nothing stored
  let store = fakeStorage();
  let env = loadScript(SCRIPT, { ids: IDS, localStorage: store });
  assert.equal(env.els["recent"].hidden, true);

  // picks are remembered newest-first, capped at 5
  for (let i = 1; i <= 6; i++) {
    env.fireDoc("htmx:beforeRequest", { target: option(`City ${i}, Land`, i, -i) });
    await tick();
  }
  assert.deepEqual(chipLabels(env), ["City 6, Land", "City 5, Land", "City 4, Land", "City 3, Land", "City 2, Land"]);
  assert.equal(env.els["recent"].hidden, false);
  assert.equal(env.els["q"].value, "City 6, Land");
  assert(env.htmxCalls.process.length >= 1);

  // chip wiring for HTMX
  const chip = env.els["recent-list"].children[0].children[0];
  assert.equal(chip.attrs["hx-get"], "/partials/weather?lat=6&lon=-6&name=City+6%2C+Land");
  assert.equal(chip.attrs["hx-target"], "#weather");
  assert.equal(chip.attrs["hx-indicator"], "#weather-skeleton");
  assert.equal(chip.className, "chip");

  // re-picking an old one moves it to the front without duplicating; chips work as sources too
  const old = env.els["recent-list"].children[3].children[0];
  old.matchers = [".chip"];
  env.fireDoc("htmx:beforeRequest", { target: old });
  await tick();
  assert.deepEqual(chipLabels(env), ["City 3, Land", "City 6, Land", "City 5, Land", "City 4, Land", "City 2, Land"]);
  assert.equal(env.els["q"].value, "City 3, Land");

  // requests that are not suggestions/chips (like the location button) are not saved
  const before = store.data["weather.recent"];
  env.fireDoc("htmx:beforeRequest", { target: makeEl("locate") });
  env.fireDoc("htmx:beforeRequest", { target: {} });
  await tick();
  assert.equal(store.data["weather.recent"], before);

  // tampered storage is ignored safely
  const bad = [
    "not json", '{"a":1}', "null",
    JSON.stringify([{ label: "x", lat: 999, lon: 0 }, { label: "", lat: 1, lon: 1 }, { label: "y".repeat(201), lat: 1, lon: 1 },
                    { label: "ok", lat: "1", lon: 1 }, { label: "<img onerror=x>", lat: 10, lon: 20 }]),
  ];
  for (const raw of bad) {
    env = loadScript(SCRIPT, { ids: IDS, localStorage: fakeStorage({ "weather.recent": raw }) });
    const labels = chipLabels(env);
    assert(labels.every((l) => l === "<img onerror=x>"), raw);
  }
  // the markup-looking label is shown as plain text, never parsed as HTML
  assert.equal(env.els["recent-list"].children[0].children[0].textContent, "<img onerror=x>");

  // storage that throws (private mode) must not break anything
  env = loadScript(SCRIPT, { ids: IDS, localStorage: fakeStorage({}, { throws: true }) });
  env.fireDoc("htmx:beforeRequest", { target: option("A, B", 1, 2) });
  await tick();
  assert.equal(env.els["recent"].hidden, true);

  // clear button
  store = fakeStorage({ "weather.recent": JSON.stringify([{ label: "A, B", lat: 1, lon: 2 }]) });
  env = loadScript(SCRIPT, { ids: IDS, localStorage: store });
  assert.equal(env.els["recent"].hidden, false);
  env.els["recent-clear"].fire("click");
  assert.equal(store.data["weather.recent"], "[]");
  assert.equal(env.els["recent"].hidden, true);
  assert(env.els["q"].focused);

  // units are remembered and re-applied
  store = fakeStorage();
  env = loadScript(SCRIPT, { ids: IDS, localStorage: store });
  const cfg = (path) => { const d = { path, parameters: {} }; env.fireDoc("htmx:configRequest", { detail: d }); return d.parameters; };
  assert.deepEqual(cfg("/partials/weather?lat=1&lon=2&name=X"), {});              // nothing saved yet
  assert.deepEqual(cfg("/partials/weather?lat=1&lon=2&name=X&units=imperial"), {}); // explicit: saved, not injected
  assert.equal(store.data["weather.units"], "imperial");
  assert.deepEqual(cfg("/partials/weather?lat=3&lon=4&name=Y"), { units: "imperial" }); // other place keeps imperial
  assert.deepEqual(cfg("/partials/weather"), { units: "imperial" });                // location button (no query in path)
  assert.deepEqual(cfg("/partials/suggest?q=par"), {});                               // other routes untouched
  cfg("/partials/weather?lat=1&lon=2&name=X&units=metric");
  assert.equal(store.data["weather.units"], "metric");
  assert.deepEqual(cfg("/partials/weather?lat=3&lon=4&name=Y"), {});                  // back to default
  cfg("/partials/weather?units=bogus");
  assert.equal(store.data["weather.units"], "metric");                                // junk values are not stored

  console.log("memory: all checks passed");
})().catch((e) => { console.error(e); process.exit(1); });
