const fs = require("fs");
const assert = require("assert");

const dispatched = [];
function makeEl(id) {
  const attrs = {}, handlers = {};
  return {
    id, attrs, handlers, value: "", dataset: {}, textContent: "", children: [],
    setAttribute(k, v) { attrs[k] = String(v); }, removeAttribute(k) { delete attrs[k]; },
    addEventListener(t, f) { (handlers[t] ||= []).push(f); },
    fire(t, ev) { (handlers[t] || []).forEach((f) => f(ev)); },
    focus() { this.focused = true; }, scrollIntoView() {}, dispatchEvent(ev) { dispatched.push(ev.type); return true; },
    closest(sel) { return this.matches && this.matches(sel) ? this : null; },
  };
}
const input = makeEl("q"), container = makeEl("suggestions"), status = makeEl("combo-status");
const docHandlers = {};
global.document = {
  getElementById: (id) => ({ q: input, suggestions: container, "combo-status": status })[id] || null,
  addEventListener: (t, f) => (docHandlers[t] ||= []).push(f),
};
const fireDoc = (t, ev) => (docHandlers[t] || []).forEach((f) => f(ev));

let clicked = [];
function loadOptions(labels) {
  container.children = labels.map((label, i) => {
    const o = makeEl("opt-" + i);
    o.dataset.label = label; o.textContent = label;
    o.matches = (sel) => sel === '[role="option"]';
    o.click = () => { clicked.push(label); fireDoc("htmx:beforeRequest", { target: o }); };
    return o;
  });
  container.textContent = labels.join(" ");
  fireDoc("htmx:afterSwap", { target: container });
}
container.querySelectorAll = () => container.children;
container.replaceChildren = () => { container.children = []; container.textContent = ""; };

eval(fs.readFileSync("app/static/js/combobox.js", "utf8"));

const key = (k) => { const ev = { key: k, prevented: false, preventDefault() { this.prevented = true; } }; input.fire("keydown", ev); return ev; };
const sel = () => container.children.map((o) => o.attrs["aria-selected"]);

// opens: expanded, none highlighted, announced
loadOptions(["Paris, A", "Paris, B", "Paris, C"]);
assert.equal(input.attrs["aria-expanded"], "true");
assert.deepEqual(sel(), ["false", "false", "false"]);
assert.match(status.textContent, /3 suggestions/);

// ArrowDown / ArrowUp with wrap, aria-activedescendant follows
assert(key("ArrowDown").prevented); assert.deepEqual(sel(), ["true", "false", "false"]);
assert.equal(input.attrs["aria-activedescendant"], "opt-0");
key("ArrowDown"); key("ArrowDown"); key("ArrowDown"); // wraps back to first
assert.equal(input.attrs["aria-activedescendant"], "opt-0");
key("ArrowUp"); assert.equal(input.attrs["aria-activedescendant"], "opt-2"); // wraps to last

// Enter selects highlighted option, fills input, closes list
const e = key("Enter"); assert(e.prevented);
assert.deepEqual(clicked, ["Paris, C"]); assert.equal(input.value, "Paris, C");
assert.equal(container.children.length, 0);
assert.equal(input.attrs["aria-expanded"], "false"); assert(!("aria-activedescendant" in input.attrs));

// Enter with nothing highlighted -> first suggestion
clicked = []; loadOptions(["Paris, A", "Paris, B"]); key("Enter");
assert.deepEqual(clicked, ["Paris, A"]);

// Esc with open list: closes, keeps text, prevents browser clearing
input.value = "par"; loadOptions(["X", "Y"]);
assert(key("Escape").prevented); assert.equal(input.value, "par"); assert.equal(container.children.length, 0);
// Esc again with list closed: clears the text itself and notifies HTMX via an input event
assert(key("Escape").prevented); assert.equal(input.value, ""); assert.deepEqual(dispatched, ["input"]);
// Esc on an already-empty box does nothing further
assert(key("Escape").prevented); assert.deepEqual(dispatched, ["input"]);

// Enter / arrows with list closed do nothing special
assert(!key("Enter").prevented); assert(!key("ArrowDown").prevented);

// Tab closes without preventing; outside pointerdown closes; inside doesn't
loadOptions(["X"]); assert(!key("Tab").prevented); assert.equal(container.children.length, 0);
loadOptions(["X"]); fireDoc("pointerdown", { target: { closest: () => null } });
assert.equal(container.children.length, 0);
loadOptions(["X"]); fireDoc("pointerdown", { target: { closest: () => ({}) } });
assert.equal(container.children.length, 1);

// No-match notice is announced, list not "expanded"
container.children = []; container.textContent = "No places match “zz”.";
fireDoc("htmx:afterSwap", { target: container });
assert.equal(input.attrs["aria-expanded"], "false"); assert.match(status.textContent, /No places match/);

// Swaps into other targets (the weather panel) are ignored
status.textContent = "keep"; fireDoc("htmx:afterSwap", { target: makeEl("weather") });
assert.equal(status.textContent, "keep");
console.log("combobox behaviour: all checks passed");
