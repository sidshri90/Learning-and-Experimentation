const assert = require("assert");
const { makeEl, loadScript } = require("./fakedom");

const IDS = ["locate", "locate-status", "geo-lat", "geo-lon", "geo-name", "q"];
const SCRIPT = "app/static/js/geolocate.js";

function geo() {
  const calls = [];
  return { calls, getCurrentPosition: (ok, err, opts) => calls.push({ ok, err, opts }) };
}
const click = (env) => env.els["locate"].fire("click");
const pos = (latitude, longitude) => ({ coords: { latitude, longitude } });

// unsupported browser
let env = loadScript(SCRIPT, { ids: IDS, navigator: {} });
assert.equal(env.els["locate"].disabled, true);
assert.match(env.els["locate-status"].textContent, /isn't supported/);

// insecure context
env = loadScript(SCRIPT, { ids: IDS, navigator: { geolocation: geo() }, secure: false });
assert.equal(env.els["locate"].disabled, true);
assert.match(env.els["locate-status"].textContent, /HTTPS/);

// success path
const g = geo();
env = loadScript(SCRIPT, { ids: IDS, navigator: { geolocation: g }, secure: true });
click(env);
assert.equal(g.calls.length, 1);
assert.deepEqual([g.calls[0].opts.enableHighAccuracy, g.calls[0].opts.timeout], [false, 10000]);
assert.equal(env.els["locate"].attrs["aria-busy"], "true");
assert.match(env.els["locate-status"].textContent, /Finding/);
click(env); // ignored while busy
assert.equal(g.calls.length, 1);
g.calls[0].ok(pos(25.594101, 85.137602));
assert.equal(env.els["geo-lat"].value, "25.5941");
assert.equal(env.els["geo-lon"].value, "85.1376");
assert.equal(env.els["geo-name"].value, "Your location (25.59, 85.14)");
assert.equal(env.els["q"].value, "Your location (25.59, 85.14)");
assert.equal(env.els["locate-status"].textContent, "");
assert(!("aria-busy" in env.els["locate"].attrs));
assert.deepEqual(env.htmxCalls.trigger, [[env.els["locate"], "located"]]);

// error messages, and the button works again afterwards
for (const [code, pattern] of [[1, /blocked/], [2, /couldn't be determined/], [3, /too long/]]) {
  const g2 = geo();
  env = loadScript(SCRIPT, { ids: IDS, navigator: { geolocation: g2 }, secure: true });
  click(env);
  g2.calls[0].err({ code });
  assert.match(env.els["locate-status"].textContent, pattern);
  assert(!("aria-busy" in env.els["locate"].attrs));
  assert.equal(env.htmxCalls.trigger.length, 0);
  click(env);
  assert.equal(g2.calls.length, 2);
}

// garbage coordinates are treated as an error, never sent
const g3 = geo();
env = loadScript(SCRIPT, { ids: IDS, navigator: { geolocation: g3 }, secure: true });
click(env);
g3.calls[0].ok(pos(NaN, 10));
assert.match(env.els["locate-status"].textContent, /couldn't be determined/);
assert.equal(env.htmxCalls.trigger.length, 0);

console.log("geolocate: all checks passed");
