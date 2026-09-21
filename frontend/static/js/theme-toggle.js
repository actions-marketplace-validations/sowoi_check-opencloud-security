/*
 * The switch between the two schemes.
 *
 * `theme.js` has already applied whatever was stored, before the first paint.
 * This file does the other half: it turns a press into the opposite scheme,
 * remembers it, and keeps the browser's own chrome pointed at the same one.
 *
 * The first visit follows the operating system and nothing is stored. Only a
 * press writes anything down, and from then on this browser has an answer of
 * its own - which is the whole point of offering the control, and the reason
 * a system that changes at sunset no longer moves the page underneath
 * somebody who has said what they want.
 *
 * Which icon is on the button is decided in CSS, from the same two questions
 * the colour tokens ask, so nothing here draws anything. This file carries no
 * English either: the label was written by the server and does not change.
 */
(function () {
    "use strict";

    var button = document.querySelector("[data-theme-toggle]");
    if (!button) {
        return;
    }

    var root = document.documentElement;
    var night = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

    function stored() {
        try {
            var value = window.localStorage.getItem("theme");
            return value === "light" || value === "dark" ? value : null;
        } catch (_error) {
            return null;
        }
    }

    // The scheme on the document, which is the one thing here that is always
    // true: theme.js wrote it from storage before the first paint, and every
    // press since has written it again.
    function applied() {
        var value = root.getAttribute("data-theme");
        return value === "light" || value === "dark" ? value : null;
    }

    // What the reader is actually looking at: the scheme the document is
    // already in, their stored choice, and the system's answer last.
    //
    // The attribute has to come first because `apply` writes it whether or
    // not the write to storage succeeds. Asking storage instead, in a browser
    // that refuses to remember, answered with the system's scheme - the one
    // the first press had just moved away from - so the second press computed
    // the same scheme again and the button stopped switching after one go.
    function current() {
        return applied() || stored() || (night && night.matches ? "dark" : "light");
    }

    /*
     * The address bar and its neighbours read `theme-color`, and the two tags
     * are keyed to the system's preference - so under an override they would
     * frame a dark page in a light bar. Narrowing one to `all` and the other
     * to nothing points them at the scheme actually on screen.
     */
    function paintBrowserChrome(theme) {
        var light = document.getElementById("theme-color-light");
        var dark = document.getElementById("theme-color-dark");
        if (!light || !dark) {
            return;
        }
        light.setAttribute("media", theme === "dark" ? "not all" : "all");
        dark.setAttribute("media", theme === "dark" ? "all" : "not all");
    }

    function apply(theme) {
        root.setAttribute("data-theme", theme);
        paintBrowserChrome(theme);
        try {
            window.localStorage.setItem("theme", theme);
        } catch (_error) {
            // A browser that will not remember it still honours it for this
            // page, which is better than refusing to switch at all.
        }
    }

    // An override stored on an earlier visit was applied by theme.js, but the
    // meta tags were rendered before either script ran.
    if (stored()) {
        paintBrowserChrome(stored());
    }

    button.addEventListener("click", function () {
        apply(current() === "dark" ? "light" : "dark");
    });
}());
