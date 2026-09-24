/*
 * Narrowing the list of architecture decision records in the operator area.
 *
 * Somebody opening the list usually has a number from a comment, or a word
 * from a review, in mind; this lets them type it instead of scrolling past
 * seventy records. It matches the number, title and status the server wrote
 * into each row, already folded to lower case there. What a record *says* is
 * found by the site search, which indexes every record's text.
 *
 * It only ever sets `hidden`, and the field is revealed from here, so a reader
 * without scripting sees the whole list and never a field that cannot filter.
 */
(function () {
    "use strict";

    var field = document.querySelector("[data-decision-filter]");
    var rows = document.querySelectorAll("[data-decision]");
    var empty = document.getElementById("admin-decision-empty");
    if (!field || !rows.length) {
        return;
    }

    document.documentElement.setAttribute("data-decision-search", "true");

    function filter() {
        var terms = field.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
        var matches = 0;

        Array.prototype.forEach.call(rows, function (row) {
            var haystack = row.getAttribute("data-decision") || "";
            // Every word has to appear, in any order: "cache 0031" and
            // "superseded mcp" both narrow rather than widen.
            var hit = terms.every(function (term) {
                return haystack.indexOf(term) !== -1;
            });
            row.hidden = !hit;
            if (hit) {
                matches += 1;
            }
        });

        if (empty) {
            empty.hidden = matches !== 0;
        }
    }

    field.addEventListener("input", filter);
    // A search field's own clear button fires `search`, not `input`, in some
    // browsers; without this the list would stay narrowed after it was
    // emptied.
    field.addEventListener("search", filter);
}());
