# ADR 0058: Public guides have reviewed German sources

- Status: Accepted
- Date: 2026-09-16
- Supersedes: ADR 0020 only for its English-only generated guide bodies

## Context

Translated navigation leaves German readers with English deployment instructions.
The public guides need German bodies as well as translated titles and summaries.
French and Spanish guide translations are outside the current scope.

## Decision

Maintain a German Markdown source in `docs/de/<slug>.md` for every public entry
in `webapp/documentation.py`. English continues to come from the existing
Markdown sources. Both are rendered by `build_frontend_documentation.py` into
checked-in templates. Requests with locale `de` select the German template at
the existing URL; all other locales select English. French and Spanish retain
a translated notice explaining the fallback.

German headings carry explicit IDs matching the English section IDs, so links
between guides remain valid in either language. Tests require matching heading
anchors and complete German coverage. Commands, option names and measured data
keep their technical spelling.

The search generator includes German guide bodies in the German overlay.
French and Spanish inherit English guide bodies. Index refreshes continue to
belong to pull-request and release automation under ADR 0050.

## Consequences

German readers can use the complete public documentation without switching to
English. Changes to a guide require reviewing its German counterpart and
regenerating both templates. An English section added or renamed without its
German counterpart fails the anchor check.

The running service still needs no Markdown parser, translation service or
source checkout. Locale negotiation, stable routes, response variation and
the treatment of API contracts and scan evidence remain as defined in ADR 0020.

## Alternatives considered

Runtime translation would add network or model dependencies and make instructions
vary between visits. Translating navigation alone leaves the main reading task
untranslated. Separate locale URLs would duplicate the existing routing scheme.
