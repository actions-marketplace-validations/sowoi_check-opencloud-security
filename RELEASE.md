## check-opencloud-security 1.26.0

### Added

- `--eol-warning DAYS` (`COS_EOL_WARNING`, YAML `eol_warning`, and a setup
  wizard question) turns an otherwise `OK` result into `WARNING` once the
  running release line has `DAYS` or fewer days of support left, naming the
  end-of-life date and the upgrade target. Off (`0`) by default; past end of
  life stays `CRITICAL` as before.

- The scan result records `upgradePath` when the installed release carries
  known advisories: which of them the recommended release fixes, which it is
  still affected by, and `safeVersion`, the lowest release past every missing
  fix. The plugin prints it as a detail line, so an update that would leave an
  advisory open no longer reads as the whole answer.

- The scan result records `alternativeServices`, what the instance advertises
  in its `Alt-Svc` header, and the plugin prints a detail line when it
  advertises HTTP/3 - a UDP listener a firewall written for TCP 443 may not
  cover. It is an observation, never graded, and the advertised address is
  never probed.

### Changed

- The "On this page" contents list of a scan report groups its up to twelve
  entries into three labelled columns - *Fix*, *Details* and *Keep* - instead
  of one long row of links, so the sections worth acting on stand apart from
  the reference material and the export and share cards.

- The Docker setup wizard opens each section with a two-column card: the step
  counter, progress and the section's purpose on the left, and every section
  of the walk on the right, marked done, skipped or still ahead, with the
  current one highlighted. A terminal narrower than the card, a pipe or
  `NO_COLOR` keeps the plain heading lines.
