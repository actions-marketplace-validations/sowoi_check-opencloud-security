## check-opencloud-security 1.27.0

### Added

- The web report lists an advertised HTTP/3 listener (with its UDP ports) and
  the upgrade path - what the recommended release fixes, what it leaves open
  and which release clears everything - in all four languages.

- `upgrade_path_complete` performance data (`1` when the recommended upgrade
  clears every known advisory, `0` when it does not), and with
  `--eol-warning` the `support_days_left` metric carries that window as its
  warning range and the end of life as critical. The webhook payload gains
  `eol_warning_days`, `eol_warning` and `upgrade_path`.

- `--login-throttling` (`COS_LOGIN_THROTTLING`, YAML
  `scanner.check_login_throttling`, also on `scan` and in the setup wizard)
  sends six failed sign-ins for a random, non-existent account to the
  built-in identity provider and records `loginThrottling` - whether an HTTP
  429 or `Retry-After` slowed them down. Off by default, never graded, run
  after every other probe, and never sent by the web service
  ([ADR 0069](adr/0069-login-throttling-is-observed-only-when-the-operator-asks.md)).
