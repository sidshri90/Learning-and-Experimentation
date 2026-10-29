/* "Use my location": ask the browser for coordinates, then let HTMX load the weather.
 * The button carries the HTMX attributes (hx-get, hx-trigger="located", hx-include);
 * this file only gets the position, fills the hidden fields and fires the "located" event. */
(function () {
  "use strict";

  const button = document.getElementById("locate");
  const status = document.getElementById("locate-status");
  const latField = document.getElementById("geo-lat");
  const lonField = document.getElementById("geo-lon");
  const nameField = document.getElementById("geo-name");
  const input = document.getElementById("q");
  if (!button || !latField || !lonField || !nameField) return;

  const say = (message) => { if (status) status.textContent = message; };

  if (!("geolocation" in navigator)) {
    button.disabled = true;
    say("Location isn't supported by this browser. Search for a city instead.");
    return;
  }
  if (window.isSecureContext === false) {
    button.disabled = true;
    say("Location needs a secure (HTTPS) connection. Search for a city instead.");
    return;
  }

  const ERRORS = {
    1: "Location access is blocked. Allow it in your browser's site settings, or search for a city.",
    2: "Your position couldn't be determined. Try again, or search for a city.",
    3: "Finding your location took too long. Try again, or search for a city.",
  };

  let busy = false; // not disabled: a disabled button would drop keyboard focus

  function finish(message) {
    busy = false;
    button.removeAttribute("aria-busy");
    say(message);
  }

  function onSuccess(position) {
    const { latitude, longitude } = position.coords;
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return onError({ code: 2 });
    const label = `Your location (${latitude.toFixed(2)}, ${longitude.toFixed(2)})`;
    latField.value = latitude.toFixed(4);
    lonField.value = longitude.toFixed(4);
    nameField.value = label;
    if (input) input.value = label;
    finish("");
    window.htmx.trigger(button, "located");
  }

  function onError(error) {
    finish(ERRORS[error && error.code] || ERRORS[2]);
  }

  button.addEventListener("click", () => {
    if (busy) return;
    busy = true;
    button.setAttribute("aria-busy", "true");
    say("Finding your location…");
    navigator.geolocation.getCurrentPosition(onSuccess, onError, {
      enableHighAccuracy: false, // city-level accuracy is enough and faster
      timeout: 10000,
      maximumAge: 10 * 60 * 1000,
    });
  });
})();
