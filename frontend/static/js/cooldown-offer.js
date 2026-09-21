/*
 * "Scanned too recently" - so here is the scan you already have.
 *
 * When the target cooldown refuses a submission, the page names the target
 * in [data-cooldown-offer]. If this tab has already shown a finished scan of
 * that target, this file opens it, with ?earlier=1 so the result page says
 * it is the earlier result and counts down to the next allowed scan.
 *
 * The history is compare-offer.js's: this tab's sessionStorage, uuids the
 * reader already held, never sent to the server. Nothing here can reach a
 * scan somebody else started (ADR 0002). An expired or malformed entry is
 * skipped; with nothing usable the refusal stays the answer.
 */
(function () {
    "use strict";

    var offer = document.querySelector("[data-cooldown-offer]");
    if (!offer) {
        return;
    }
    var target = offer.getAttribute("data-cooldown-target") || "";
    var UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    var history;
    try {
        history = JSON.parse(window.sessionStorage.getItem("cos-scan-history") || "{}");
    } catch (_error) {
        return;
    }
    if (!target || !history || typeof history !== "object" ||
            !Array.isArray(history[target])) {
        return;
    }

    var now = Date.now();
    var latest = null;
    history[target].forEach(function (entry) {
        if (entry && typeof entry.uuid === "string" && UUID.test(entry.uuid) &&
                typeof entry.expires === "number" && entry.expires > now &&
                typeof entry.seen === "number" &&
                (latest === null || entry.seen >= latest.seen)) {
            latest = entry;
        }
    });
    if (!latest) {
        return;
    }

    offer.hidden = false;
    window.location.replace("/scan/" + encodeURIComponent(latest.uuid) + "?earlier=1");
}());
