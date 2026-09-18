---
description: Work on a change in an isolated git worktree branched from the up-to-date release branch - create the worktree, work only inside it, rebase on origin/release/<version>, commit, push, and print the commands that remove the worktree afterwards.
argument-hint: "<branch-name> [release/<version>]"
disable-model-invocation: true
---

# Worktree session

Arguments: $ARGUMENTS

- First argument (required): the new branch, e.g. `fix/wizard-motion`.
  Refuse and ask if it is missing, is `main`, or starts with `release/`.
- Second argument (optional): the release branch to start from, e.g.
  `release/1.25.2`. Default: the highest `origin/release/*` by version.

Every shell call is a fresh shell, so after step 1 substitute the literal
values (`REL`, `BR`, `WT`) into each command instead of relying on variables.
Never skip a step, and never work around a hook refusal - report it.

## 1. Start from the up-to-date release branch

Run from the main checkout:

```bash
git fetch origin --prune
REL="<release branch argument, or empty>"
[ -n "$REL" ] || REL="$(git for-each-ref --format='%(refname:strip=3)' 'refs/remotes/origin/release/*' | sort -V | tail -n 1)"
REL="${REL#origin/}"; REL="release/${REL#release/}"
git rev-parse --verify --quiet "refs/remotes/origin/$REL" >/dev/null || { echo "no origin/$REL" >&2; exit 1; }
BR="<branch-name>"
WT="$(dirname "$(git rev-parse --show-toplevel)")/$(basename "$(git rev-parse --show-toplevel)")-wt-${BR//\//-}"
git worktree add -b "$BR" "$WT" "origin/$REL"
git -C "$WT" branch --set-upstream-to="origin/$REL" "$BR"
echo "REL=$REL BR=$BR WT=$WT"
```

Stop if the branch or the worktree path already exists - ask the user
whether to reuse it; never delete it yourself. Tell the user the three
values.

## 2. Work only inside the worktree

Every command from here on runs in `WT`: `cd "<WT>" && ...`, or
`git -C "<WT>" ...`; every file you read or edit is under `WT`. Never edit
the main checkout. `uv run ...` works in the worktree (it creates its own
`.venv` on first use). Make the change and its `## [Unreleased]` entry in
`CHANGELOG.md` as AGENTS.md requires; run `/preflight quick` before step 4.

## 3. Rebase on origin/<release> before committing

```bash
git -C "<WT>" fetch origin
git -C "<WT>" stash push --include-untracked -m worktree-session   # only if there are uncommitted changes
git -C "<WT>" rebase "origin/<REL>"
git -C "<WT>" stash pop                                            # only if you stashed
```

On a conflict stop: conflicts in generated files go to
`/resolve-generated-conflicts`; anything else is reported to the user.
Never `rebase --abort` on your own (a hook refuses it anyway).

## 4. Commit

```bash
git -C "<WT>" add -A
git -C "<WT>" status --short        # review: nothing unintended, no scan output
git -C "<WT>" commit -m "<type>: <summary>"
```

Conventional-commit subject as in `git log`, the attribution trailer from
the system reminder. If the privacy guard refuses, replace the value with
`opencloud.example.com` / `192.0.2.x` - never extend its allowlist.

Right before pushing, rebase once more so the push is based on the newest
release branch: `git -C "<WT>" fetch origin && git -C "<WT>" rebase "origin/<REL>"`.

## 5. Push with --force-with-lease

The project hook refuses every force-push by an agent, including
`--force-with-lease`. So:

- **Branch not yet on origin** (`git -C "<WT>" ls-remote --exit-code --heads origin "<BR>"`
  exits 2): a plain first push is no force, run it yourself:
  `git -C "<WT>" push -u origin "<BR>"`.
- **Branch already on origin** (a rebase rewrote it): do not run the push.
  Give the user this line to run with the `!` prefix:

  ```
  ! git -C "<WT>" push --force-with-lease="<BR>:origin/<BR>" origin "<BR>"
  ```

  The explicit `<BR>:origin/<BR>` lease makes the push fail instead of
  overwriting commits someone else pushed since your last fetch.

Never push to `main` or a tag, never bump the version.

## 6. Print the cleanup commands

After the push, output (do not run) the commands for the user, with the
literal values filled in:

```bash
cd "<main checkout>"
git worktree remove "<WT>"        # add --force only if you want to discard uncommitted files
git branch -D "<BR>"              # once the pull request is merged
git worktree prune
```

End with: the worktree path, the branch, the release branch it is based on,
the pushed commit (`git -C "<WT>" log -1 --oneline`), and whether the push
still waits on the user.
