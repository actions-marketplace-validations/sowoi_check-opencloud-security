"""
One finished scan as a badge: a grade somebody can put beside a link.

The same bargain `webapp.reports` makes for the PDF, for the same reason. The
SVG is written here, by hand, rather than fetched from a badge service: this
page has never caused a request the visitor did not ask for, and an `<img>`
pointing at somebody else's server would hand them the result URL - whose uuid
is the entire authorisation - in a referrer, on every view, forever.

Nothing here judges anything either. The grade is the plugin's `RATE_MAP` by
way of :func:`webapp.catalog.rating_label`, and the colour is
:func:`webapp.catalog.rating_tone`'s, so the badge, the dial on the result
page and the letter in an export cannot disagree.

**No text from the scanned instance reaches the badge** - not the hostname,
not the product string, not the version. A badge is a picture rendered from
three fixed words and one letter, which is what lets it be assembled without
any question of what somebody else's server put in a header.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .catalog import rating_label, rating_tone

#: The tone colours of `frontend/static/css/app.css`, in its light theme. A
#: badge is embedded in somebody else's page, so it cannot follow the reader's
#: colour scheme the way the site does - these read on white and on dark.
TONE_COLOURS = {
    "good": "#0f7a53",
    "fair": "#a75a00",
    "bad": "#cc2b3d",
}
UNKNOWN_COLOUR = "#5c5f6b"
LABEL_COLOUR = "#2b2d36"

LABEL = "OpenCloud security"

_HEIGHT = 20
_FONT_SIZE = 11
#: Verdana at 11px, averaged. Rendering the exact metrics would mean shipping
#: a font table for two fixed strings, one of which is a single letter.
_CHARACTER_WIDTH = 6.6
_PADDING = 9


def _segment_width(text: str) -> int:
    return int(round(len(text) * _CHARACTER_WIDTH)) + 2 * _PADDING


def colour_for(rating: object) -> str:
    """The badge colour for a rating, from the dashboard's own tones."""
    label = rating_label(rating)
    if label == "?":
        return UNKNOWN_COLOUR
    return TONE_COLOURS.get(rating_tone(rating), UNKNOWN_COLOUR)


def render(rating: object) -> str:
    """
    Render one rating as a self-contained SVG badge.

    Self-contained is the requirement, not a preference: no script, no
    external stylesheet, no font to fetch, nothing that turns an embedded
    image into a request somewhere else. It carries a title and an
    `aria-label` because it is read as an image in somebody else's document,
    where the grade is the only thing that was being said.
    """
    grade = rating_label(rating)
    label_width = _segment_width(LABEL)
    grade_width = _segment_width(grade)
    total = label_width + grade_width
    description = f"{LABEL}: {grade}"
    safe_label = escape(LABEL)
    safe_grade = escape(grade)
    safe_description = escape(description)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" '
        f'height="{_HEIGHT}" viewBox="0 0 {total} {_HEIGHT}" role="img" '
        f'aria-label="{safe_description}">'
        f"<title>{safe_description}</title>"
        f'<rect width="{total}" height="{_HEIGHT}" rx="3" fill="{LABEL_COLOUR}"/>'
        f'<path fill="{colour_for(rating)}" d="M{label_width} 0h{grade_width - 3}'
        f'a3 3 0 0 1 3 3v{_HEIGHT - 6}a3 3 0 0 1-3 3H{label_width}z"/>'
        f'<g fill="#ffffff" font-family="Verdana,DejaVu Sans,Geneva,sans-serif" '
        f'font-size="{_FONT_SIZE}" text-anchor="middle">'
        f'<text x="{label_width / 2:g}" y="14">{safe_label}</text>'
        f'<text x="{label_width + grade_width / 2:g}" y="14" '
        f'font-weight="bold">{safe_grade}</text>'
        f"</g></svg>"
    )
