// A tiny fake DOM, just enough to exercise the scripts in app/static/js without a browser.
const fs = require("fs");

function makeEl(id = "") {
  const el = {
    id, dataset: {}, attrs: {}, handlers: {}, children: [], hidden: false, disabled: false,
    textContent: "", value: "", className: "", title: "", type: "", focused: false, focusCount: 0, matchers: [],
    setAttribute(k, v) { el.attrs[k] = String(v); },
    getAttribute(k) { return el.attrs[k] ?? null; },
    removeAttribute(k) { delete el.attrs[k]; },
    addEventListener(t, f) { (el.handlers[t] ||= []).push(f); },
    fire(t, ev = {}) { (el.handlers[t] || []).forEach((f) => f(ev)); },
    append(child) { el.children.push(child); },
    replaceChildren() { el.children = []; },
    focus() { el.focused = true; el.focusCount++; },
    closest(sel) { return el.matchers.includes(sel) ? el : null; },
  };
  return el;
}

// Loads a script fresh, with new globals, and returns the pieces tests need.
function loadScript(path, { ids = [], localStorage, navigator, secure } = {}) {
  const els = Object.fromEntries(ids.map((id) => [id, makeEl(id)]));
  const docHandlers = {};
  const htmxCalls = { process: [], trigger: [] };
  global.document = {
    getElementById: (id) => els[id] || null,
    createElement: () => makeEl(),
    addEventListener: (t, f) => (docHandlers[t] ||= []).push(f),
  };
  global.window = {
    localStorage, isSecureContext: secure, location: { origin: "http://127.0.0.1:8000" },
    htmx: { process: (e) => htmxCalls.process.push(e), trigger: (e, n) => htmxCalls.trigger.push([e, n]) },
  };
  Object.defineProperty(globalThis, "navigator", { value: navigator || {}, configurable: true, writable: true });
  (0, eval)(fs.readFileSync(path, "utf8"));
  return { els, htmxCalls, fireDoc: (t, ev) => (docHandlers[t] || []).forEach((f) => f(ev)) };
}

function fakeStorage(initial = {}, { throws = false } = {}) {
  const data = { ...initial };
  return {
    data,
    getItem(k) { if (throws) throw new Error("denied"); return k in data ? data[k] : null; },
    setItem(k, v) { if (throws) throw new Error("denied"); data[k] = String(v); },
  };
}

module.exports = { makeEl, loadScript, fakeStorage };
