# CLI du scanner

Le paquet installe deux commandes.

- **`check-opencloud-security`** is the monitoring plugin. It scans an
  instance, *judges* the result against thresholds and exits `0`-`3` for
  Nagios or Icinga. Its flags are in the [CLI option reference](cli-reference.md).
- **`check-opencloud-scanner`** is everything else. It gives you the raw
  result document, compares two of them, explains a finding, refreshes the
  reference data, and runs the scan service. It never applies a warning or
  critical threshold.

This page is the reference for the second one.

<!-- TOC -->
* [The `check-opencloud-scanner` command](#the-check-opencloud-scanner-command)
  * [Global options](#global-options)
  * [`scan` - print the result document](#scan---print-the-result-document)
  * [`diff` - what changed between two saved results](#diff---what-changed-between-two-saved-results)
  * [`explain` - what a finding means and how to fix it](#explain---what-a-finding-means-and-how-to-fix-it)
  * [`refresh-data` - update the release schedule and advisories](#refresh-data---update-the-release-schedule-and-advisories)
  * [`serve` - the scan service](#serve---the-scan-service)
  * [`configure` - write a configuration file](#configure---write-a-configuration-file)
  * [Exit codes](#exit-codes)
<!-- TOC -->


## Global options

These go **before** the subcommand:

```bash
check-opencloud-scanner -c /etc/check-opencloud-security/config.yml -v scan opencloud.example.com
```

| Option | What it does |
|:--|:--|
| `-c, --config` | Configuration file. `.json` is read as JSON, anything else as YAML |
| `-v, --verbose` | More log output on stderr: `-v` for info, `-vv` for debug |

Without `-c`, the first file that exists is used, in this order:

1. `./.env.json`
2. `./check-opencloud-security.yml`
3. `./check-opencloud-security.yaml`
4. `~/.config/check-opencloud-security/.env.json`
5. `/etc/check-opencloud-security/.env.json`
6. `/etc/check-opencloud-security/config.yml`
7. `/etc/check-opencloud-security/config.yaml`

This is the same search the plugin does. `COS_` environment variables apply
on top of the file, and flags on top of both. See
[Secrets in the configuration](configuration.md).

## `scan` - print the result document

```bash
check-opencloud-scanner scan opencloud.example.com
check-opencloud-scanner scan --compact opencloud.example.com > result.json
check-opencloud-scanner scan cloud1.example.com cloud2.example.com | jq '.[].rating'
```

It prints the scanner's JSON result document: the rating and its
explanation, the lifecycle, every check, TLS and advisory matches, all with
camelCase keys. It prints no verdict. One host prints one object. Several
hosts print an array, in the order given.

| Option | What it does |
|:--|:--|
| `--compact` | Print the document on one line instead of indented |
| `--scheme {https,http}` | How to reach the instance |
| `--port` | Override the port |
| `--timeout` | Seconds allowed for each request |
| `--insecure` | Do not verify the instance's TLS certificate |
| `--ca-file` | PEM CA bundle to verify an internal certificate with |
| `--no-extra-checks` | Only product, version and headers |
| `--no-debug-ports` | Skip probing OpenCloud's debug ports |
| `--all-addresses` | Repeat the key checks on every address the name resolves to |
| `--concurrency` | Probes run in parallel within one scan. Default `1` |
| `--no-update-check` | Do not look up the newest OpenCloud release |

Waivers, the release track and the advisory sources come from the
configuration file or environment, exactly as for the plugin.

An instance that cannot be scanned does not abort the run. Its entry becomes
`{"host": ..., "error": ...}`, the other hosts are still scanned, and the
command exits `1`:

```json
{
  "host": "opencloud.example.com",
  "error": "https://opencloud.example.com/status.php is unreachable"
}
```

The document is what [CI pipelines](ci.md) and [Prometheus](prometheus.md)
consume, and what `diff` below compares. The
[scanner library README](../../opencloud_local_scan/README.md) describes its
fields.

## `diff` - what changed between two saved results

```bash
check-opencloud-scanner scan opencloud.example.com > before.json
# ... change something on the instance ...
check-opencloud-scanner scan opencloud.example.com > after.json
check-opencloud-scanner diff before.json after.json
```

```text
opencloud.example.com: 2026-09-15 17:42:21.524291 -> 2026-09-15 17:42:22.737103
New since last run (15): check:debugEndpoint:/config, check:debugEndpoint:/debug/pprof/, check:debugEndpoint:/metrics, check:demoUsersDisabled, check:directoryListing (+10 more)
Security check: + debugEndpoint:/config
Security check: + demoUsersDisabled
...
Hardening: + Content-Security-Policy
...
Rating: A+ (5) -> D (2)
```

It reads two files and scans nothing. `+` marks a finding that appeared, and
`-` one that was resolved. It also reports any movement in the rating, the
version and the support horizon. It answers "did the fix work?" and "what
did the upgrade change?" without keeping a baseline file. For a check that
remembers its last run by itself, see [Reporting only what changed](baseline.md).

| Option | What it does |
|:--|:--|
| `--format text` | Readable lines, as above. The default |
| `--format markdown` | A Markdown table, for a ticket or a pull request comment |
| `--format json` | The structured comparison the plugin's webhook carries |
| `--format slack` | Slack Block Kit JSON |
| `--exit-zero` | Always exit `0` |
| `--allow-different-hosts` | Compare results from two different instances |

**It exits `1` when the second result is worse**, so a pipeline can gate on
it. It exits `0` when nothing got worse, including when findings were only
resolved. `--exit-zero` turns the gate off.

It exits `2`, and compares nothing, when it cannot give an honest answer:

- **the two files describe different instances.** "Did the fix work" is a
  question about one instance, and two hosts compared by accident is a wrong
  answer nobody notices. Pass `--allow-different-hosts` if that is what you
  meant.
- **a file is not a result document** from `scan`. For example, it has no
  rating, or it is the error entry of an instance that could not be scanned.

## `explain` - what a finding means and how to fix it

```bash
check-opencloud-scanner explain basicAuthDisabled
```

```text
basicAuthDisabled: HTTP Basic authentication is enabled
    The instance answers with a 'WWW-Authenticate: Basic' challenge, so usernames and passwords can be replayed on every request without going through the identity provider, ...
    Setting: PROXY_ENABLE_BASIC_AUTH
    Fix: Set PROXY_ENABLE_BASIC_AUTH=false (the default) if nothing needs it. ...
    Docs: https://docs.opencloud.eu/docs/dev/server/services/proxy/environment-variables
```

It looks identifiers up in the catalogue built into the package. That is the
same text the plugin's `--debug` output, the scan result and the web
application show. It reads no configuration, needs no network and scans
nothing, so it works on any host where the package is installed.

```bash
check-opencloud-scanner explain cspWithoutUnsafeInline Referrer-Policy   # several at once
check-opencloud-scanner explain exposed:/config/opencloud.yaml          # parameterised ids too
check-opencloud-scanner explain --list                                  # every identifier, one per line
check-opencloud-scanner explain --list --category cookies               # one category
check-opencloud-scanner explain --format json cookieSecure              # for a script
check-opencloud-scanner explain                                         # the whole catalogue
```

| Option | What it does |
|:--|:--|
| `--list` | Print bare identifiers instead of explanations |
| `--category` | Only one category: `cookies`, `authentication`, `sharing`, `exposure`, `embedding`, `lifecycle`, `proxy`, `headers` or `transport` |
| `--format {text,json}` | JSON gives `id`, `category`, `title`, `meaning`, `remediation`, `reference`, `setting` and `actionable` for each entry |

An identifier the catalogue does not know exits `1` and suggests the nearest
ones:

```text
ERROR check_opencloud.cli: No catalogue entry for 'cookieSecur'. Did you mean: cookieSecure, cookieSameSite, cookiePrefix? Run `explain --list` for every identifier this build knows.
```

The identifiers are the ones findings carry in the alert line, in
`extraChecks[].id` and in `hardenings`, and the ones a waiver names. For the
longer, page-by-page treatment, see
[Hardening measures, one by one](hardening.md) and
[What the scanner reads](scanner-checks.md).

## `refresh-data` - update the release schedule and advisories

```bash
check-opencloud-scanner refresh-data --output-dir /var/lib/check-opencloud-security
```

It fetches the reviewed release schedule and advisory database from this
project's repository, verifies their signature, and writes them to
`--output-dir`. It prints the two paths and exits `0`. On any failure it
writes nothing and exits `1`.

| Option | Default | What it does |
|:--|:--|:--|
| `--output-dir` | `~/.cache/check-opencloud-security` | Where the two files go |
| `--timeout` | `30` | Seconds allowed for each request |
| `--schedule-url` | *(none)* | A lifecycle page or mirror, fetched unverified |
| `--advisory-url` | *(none)* | An OSV endpoint or mirror, fetched unverified |

The files have no effect until the configuration points at them. The
signature check needs the `signing` extra. One pitfall is easy to miss: a
schedule file the check cannot read turns the end-of-life check off. All of
this is covered in
[Keeping the release schedule and advisories current](reference-data.md).

## `serve` - the scan service

```bash
check-opencloud-scanner serve
check-opencloud-scanner serve --listen 0.0.0.0 --token "$(cat /run/secrets/scanner_token)"
```

It runs the scanner as a small HTTP service, so that several consumers share
one cached result per instance instead of each scanning it again.

| Option | Default | Setting |
|:--|:--|:--|
| `--listen` | `127.0.0.1` | `service.listen` / `COS_SERVICE_LISTEN` |
| `--port` | `8811` | `service.port` / `COS_SERVICE_PORT` |
| `--cache-ttl` | `900` seconds | `service.cache_ttl` / `COS_SERVICE_CACHE_TTL` |
| `--token` | *(none)* | `service.token` / `COS_SERVICE_TOKEN` |
| `--concurrency` | `1` | Probes in parallel within one scan |
| `--insecure` | off | Do not verify scanned instances' certificates |

**Binding anything but loopback without a token refuses to start.** It
prints `UNKNOWN: ...` on stderr and exits `3`, a code a supervisor will not
keep restarting through. The endpoints are listed in the
[main README](../README.md#running-the-scanner-as-a-service), and running it
in a container is covered in
[Running the scanner as a service](scan-service.md).

This is not the public web application. That one is
[the public scan service](../webapp.md).

## `configure` - write a configuration file

```bash
check-opencloud-scanner configure
check-opencloud-scanner -c /etc/check-opencloud-security/.env.json configure
```

It asks for the settings interactively, explains each one, and saves them as
JSON, readable by the owner only. It offers `./.env.json`,
`~/.config/check-opencloud-security/.env.json` and
`/etc/check-opencloud-security/.env.json`, all places the search above finds
automatically. `-c` names the path instead. It is the same wizard as
`check-opencloud-security --configure`.

| Option | What it does |
|:--|:--|
| `--all` | Go through the optional settings without asking first |
| `--force` | Replace an existing file without confirming |
| `--no-test-scan` | Do not offer a test scan of the host before saving |

## Exit codes

These are **not** the plugin's Nagios codes. A `scan` that finds an F-rated
instance still exits `0`, parce que c’est au plugin d’évaluer le résultat.

| Subcommand | `0` | `1` | `2` | `3` |
|:--|:--|:--|:--|:--|
| `scan` | Every host was scanned | At least one host could not be scanned | Invalid configuration | - |
| `diff` | Nothing got worse | The later result is worse | The files cannot be compared | - |
| `explain` | Printed | Unknown identifier or empty category | - | - |
| `refresh-data` | Both files written | Nothing written, see stderr | - | - |
| `serve` | Stopped normally | - | Invalid configuration | Refused to start, e.g. a wide bind without a token |

Invalid command-line arguments exit `2` for every subcommand, as usual for
argparse.
