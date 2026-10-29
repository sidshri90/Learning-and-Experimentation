/* Keyboard + ARIA behaviour for the city search combobox.
 * HTMX fetches and swaps the suggestion list; this file only manages focus,
 * highlighting and announcements. Follows the WAI-ARIA "editable combobox
 * with list autocomplete" pattern. */
(function () {
  "use strict";

  const input = document.getElementById("q");
  const container = document.getElementById("suggestions");
  const status = document.getElementById("combo-status");
  if (!input || !container) return;

  let active = -1; // index of the highlighted option, -1 = none

  const options = () => Array.from(container.querySelectorAll('[role="option"]'));

  function setActive(index) {
    const opts = options();
    opts.forEach((o, i) => o.setAttribute("aria-selected", i === index ? "true" : "false"));
    active = index;
    if (index >= 0 && opts[index]) {
      input.setAttribute("aria-activedescendant", opts[index].id);
      opts[index].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function closeList() {
    container.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    setActive(-1);
    if (status) status.textContent = "";
  }

  // After HTMX swaps in a new suggestion list: reset highlight and announce it.
  document.addEventListener("htmx:afterSwap", (event) => {
    if (event.target !== container) return;
    const n = options().length;
    input.setAttribute("aria-expanded", n > 0 ? "true" : "false");
    setActive(-1);
    if (status) {
      status.textContent =
        n > 0
          ? `${n} suggestion${n === 1 ? "" : "s"} available. Use up and down arrows to browse, Enter to select.`
          : container.textContent.trim();
    }
  });

  // When an option is chosen (mouse click or Enter), HTMX fires beforeRequest on it.
  // Put its full label in the box and close the list. Same timing as before: the
  // request is already built, so removing the list here is safe.
  document.addEventListener("htmx:beforeRequest", (event) => {
    const option = event.target.closest && event.target.closest('[role="option"]');
    if (!option) return;
    input.value = option.dataset.label || option.textContent.trim();
    closeList();
    input.focus();
  });

  input.addEventListener("keydown", (event) => {
    const opts = options();
    switch (event.key) {
      case "ArrowDown":
        if (!opts.length) return;
        event.preventDefault();
        setActive((active + 1) % opts.length);
        break;
      case "ArrowUp":
        if (!opts.length) return;
        event.preventDefault();
        setActive(active <= 0 ? opts.length - 1 : active - 1);
        break;
      case "Enter":
        if (!opts.length) return;
        event.preventDefault();
        (opts[active] || opts[0]).click(); // nothing highlighted -> first suggestion
        break;
      case "Escape":
        event.preventDefault(); // also stops the browser's own (inconsistent) clearing of search inputs
        if (opts.length) {
          closeList(); // first Esc closes the list and keeps the text
        } else if (input.value) {
          input.value = ""; // second Esc clears the text
          input.dispatchEvent(new Event("input", { bubbles: true })); // let HTMX refresh the list
        }
        break;
      case "Tab":
        closeList();
        break;
    }
  });

  // Keep focus in the input when clicking an option (otherwise blur would race the click).
  container.addEventListener("mousedown", (event) => event.preventDefault());

  // Click or tap outside the search area closes the list.
  document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest(".search")) closeList();
  });
})();
