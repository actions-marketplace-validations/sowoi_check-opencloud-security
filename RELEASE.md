## check-opencloud-security 1.23.1

### Changed

- **The bundled release schedule knows OpenCloud 8.0.** Regenerated from the
  published lifecycle page: the 8.0 line is the current rolling release
  (8.0.0), so 7.5 is now behind the rolling track. Production (7.2.4) and LTS
  (4.0.8) are unchanged, and the README release table follows. The advisory
  database was re-read from OSV and has nothing new. The frontend
  documentation and the search indexes are rebuilt to match.

### Documentation

- **Claude Code skills for the repetitive maintenance tasks.** `.claude/skills/`
  now carries step-by-step skills for patch, minor and major releases, opening
  the release pull request, refreshing the bundled data, adding a setting, a
  hardening check or a translated string, writing a security advisory record or
  an ADR, a local run of the pull request checks, fixing OpenCloud
  documentation links, and resolving conflicts in generated files. They follow
  `AGENTS.md`: none of them publishes an advisory, merges to `main` or bumps a
  version unless the maintainer invokes a release skill.
- **A skill to run and drive the project locally.**
  `.claude/skills/run-check-opencloud-security/` runs the scanner library,
  the plugin or the web app against the fake OpenCloud from the tests, with no
  Redis, Docker or real instance. The web app gets an in-process worker, so a
  submitted scan completes. Headless Chromium submits the form and takes
  screenshots.
- **`.claude/` stays out of images and source archives.** It is listed in
  `.dockerignore` and marked `export-ignore` in `.gitattributes`, like
  `.github/`.
