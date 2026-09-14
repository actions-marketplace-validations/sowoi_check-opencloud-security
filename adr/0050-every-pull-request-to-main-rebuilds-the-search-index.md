# ADR 0050: Every pull request to main rebuilds the search index

- Status: Accepted
- Date: 2026-09-14
- Supersedes: the release-only refresh in ADR 0019

## Context

ADR 0019 made the browser search index a checked-in file that only the
release workflow rebuilds, so that "documentation changes intentionally do
not appear in search until the next release". In practice that meant `main`
nearly always carried an index describing pages as they read one release
ago: a pull request that renamed a page, edited its copy or added a guide
merged with search still pointing at the old text, and anything built from
`main` between releases - an image, a web bundle, a local
`docker compose up --build` - was reported by the operator area as out of
date for a reason nobody working on it could see in the diff.

The boundary ADR 0019 actually protects is what the generator may read, not
when it runs. `scripts/build_search_index.py` reads the public-page manifest,
the templates and the catalogues and nothing else; running it more often does
not widen that.

## Decision

`.github/workflows/search-index.yml` runs the generator on every pull request
to `main`, unconditionally - no path filter, because the index also depends
on the version and the catalogues, and a filter that forgets one input is how
a stale index merges. When the result differs from the branch, the workflow
commits it back to the pull request branch as `chore: rebuild the search
index`.

- It pushes only to a branch in this repository. A fork's pull request or a
  Dependabot branch gets a read-only token; there the index is rebuilt and a
  stale one is reported as a warning.
- The generator runs before any credential is placed in the checkout, and the
  token is used only by the push that follows, with the branch passed through
  the environment rather than the script text.
- A push made with `GITHUB_TOKEN` starts no workflow, so the bot's commit
  cannot trigger another rebuild.

The release workflow keeps rebuilding the index before it builds artefacts, so
a published release still ships an index built for exactly that version. The
generator's inputs are unchanged: no store, API, result template, export, UUID
or network input. The operator area still reports the index and never
rebuilds it (ADR 0035).

## Consequences

Search on `main` describes `main`. A reviewer sees the regenerated index in
the pull request, next to the change that caused it, instead of in a release
commit nobody reviews.

The bot's commit does not re-run the other checks on the new head, because a
`GITHUB_TOKEN` push starts no workflow; the index is generated, so the checks
on the preceding commit still describe everything a person wrote. A branch
protection rule that requires checks on the exact head commit would need a
new push, or the workflow switched to a token that does start workflows.

Two open pull requests that both change the index still conflict with each
other once one merges. The merge driver from
`scripts/setup_git_merge_drivers.py` settles that locally; the workflow
settles it on the next push to the branch.

## Alternatives considered

**Failing the pull request with `--check` instead of committing** was
rejected: it turns a generated file into a chore every contributor has to run
by hand, which is the friction the merge driver was added to remove.

**A path filter on templates, catalogues and `pyproject.toml`** was rejected
because the inputs are easy to under-list and an omission is silent.

**`pull_request_target`, to push to forks as well**, was rejected: it runs with
a write token in the context of code a stranger wrote.
