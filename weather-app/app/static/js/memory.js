/* Things the browser remembers: the last 5 searches and the °C/°F choice.
 * Everything lives in localStorage on this device. Nothing is sent to the server
 * except the coordinates of a place you pick, exactly as before. */
(function () {
  "use strict";

  const RECENT_KEY = "weather.recent";
  const UNITS_KEY = "weather.units";
  const MAX_RECENT = 5;

  const box = document.getElementById("recent");
  const list = document.getElementById("recent-list");
  const clearButton = document.getElementById("recent-clear");
  const input = document.getElementById("q");

  function read(key) {
    try { return window.localStorage.getItem(key); } catch (_) { return null; }
  }
  function write(key, value) {
    try { window.localStorage.setItem(key, value); } catch (_) { /* private mode or quota: ignore */ }
  }

  // Stored data can be edited by the user or other scripts, so validate it on every read.
  function isValid(r) {
    return Boolean(r) && typeof r.label === "string" && r.label.length > 0 && r.label.length <= 200 &&
      Number.isFinite(r.lat) && Number.isFinite(r.lon) && Math.abs(r.lat) <= 90 && Math.abs(r.lon) <= 180;
  }

  function loadRecent() {
    try {
      const parsed = JSON.parse(read(RECENT_KEY) || "[]");
      return Array.isArray(parsed) ? parsed.filter(isValid).slice(0, MAX_RECENT) : [];
    } catch (_) {
      return [];
    }
  }

  function remember(label, lat, lon) {
    const item = { label, lat, lon };
    if (!isValid(item)) return;
    const items = loadRecent().filter((r) => r.label !== label); // re-picking moves it to the front
    items.unshift(item);
    write(RECENT_KEY, JSON.stringify(items.slice(0, MAX_RECENT)));
  }

  function render() {
    if (!box || !list) return;
    const items = loadRecent();
    list.replaceChildren();
    box.hidden = items.length === 0;
    items.forEach((r) => {
      const li = document.createElement("li");
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = r.label; // textContent, never innerHTML
      chip.title = r.label;
      chip.dataset.label = r.label;
      chip.dataset.lat = String(r.lat);
      chip.dataset.lon = String(r.lon);
      chip.setAttribute("hx-get", "/partials/weather?" + new URLSearchParams({ lat: r.lat, lon: r.lon, name: r.label }));
      chip.setAttribute("hx-target", "#weather");
      chip.setAttribute("hx-indicator", "#weather-skeleton");
      li.append(chip);
      list.append(li);
    });
    if (window.htmx) window.htmx.process(list); // teach HTMX about the new buttons
  }

  // A suggestion or a recent chip was chosen: remember it. (The location button is not saved.)
  document.addEventListener("htmx:beforeRequest", (event) => {
    const el = event.target;
    const source = el && el.closest && (el.closest('[role="option"]') || el.closest(".chip"));
    if (!source) return;
    const label = source.dataset.label;
    remember(label, Number(source.dataset.lat), Number(source.dataset.lon));
    if (input && label) input.value = label;
    setTimeout(render, 0); // after HTMX has sent the request that this element triggered
  });

  // Keep the chosen units when a different place is picked.
  document.addEventListener("htmx:configRequest", (event) => {
    const path = event.detail.path || "";
    if (path.indexOf("/partials/weather") !== 0) return;
    let explicit = null;
    try { explicit = new URL(path, window.location.origin).searchParams.get("units"); } catch (_) { /* ignore */ }
    if (explicit === "metric" || explicit === "imperial") {
      write(UNITS_KEY, explicit); // the °C/°F buttons name their units explicitly
    } else if (read(UNITS_KEY) === "imperial") {
      event.detail.parameters.units = "imperial";
    }
  });

  if (clearButton) {
    clearButton.addEventListener("click", () => {
      write(RECENT_KEY, "[]");
      render();
      if (input) input.focus();
    });
  }

  render();
})();
