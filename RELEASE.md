## check-opencloud-security 1.24.0

### Documentation

- Rewrite frontend explanations and operator documentation for clearer,
  consistent wording in English, German, French and Spanish. Clarify scan
  coverage, temporary storage, alert timing and configuration instructions.
- Add German versions of all public guides under `docs/de/`, generated German
  frontend pages and German guide search content. Preserve section links across
  languages; French and Spanish continue to use English guide bodies.

### Added

- **The comparison page takes the earlier scan as an uploaded report.**
  `/compare` needed both scans to still exist, and the baseline worth
  comparing against is usually older than the hour a result lives. It now also
  accepts the JSON or CSV file from a result page's downloads: upload the
  report you kept, name a scan that has not expired, and the page answers the
  same question with the same arithmetic - `workflows.compare_documents`, which
  is the plugin's own `--baseline` comparison, so a reader, an agent and an
  operator's alerting still cannot disagree about one pair. The file is the
  only structure this service parses that it did not write, so it crosses one
  boundary: `webapp/imports.py` does not hand back what it was given but a
  result document rebuilt key by key from an allow-list, capped at 256 KB,
  strict UTF-8, with identifiers dropped and counted unless they are spelled
  the way this scanner spells its own. The file is read once in memory and
  written nowhere - not its contents, not its name, which nothing reads. What
  survives is the comparison, under a fresh uuid4 for at most five minutes so
  a reload and a shared link keep working; `COS_WEB_COMPARISON_TTL` can
  shorten that window and cannot widen it. Unknown, malformed and expired
  tokens are one 404, and nothing lists them, and `DELETE /api/purge` erases a
  cached comparison along with the scans of the instance it names rather than
  leaving it to its own clock. A browser feature only: no MCP
  tool and not in the OpenAPI schema, because an agent already has
  `compare_scans` and two uuids. See
  [ADR 0057](adr/0057-an-uploaded-report-is-evidence-not-a-scan.md).

- **`--format otlp` hands the scan's metrics to an OpenTelemetry collector.**
  The eight metrics the Prometheus exporter publishes, rendered as one
  OTLP/JSON `ExportMetricsServiceRequest` covering every scanned host - the
  body a collector accepts at `/v1/metrics`. Pipe it at `curl` from the timer
  that already runs the check: the plugin prints the document and never dials
  the collector itself, so where the metrics go and which credential reaches
  them stay out of a scan. Like `--format prometheus` it exits `0` whatever
  the instance scored and reports an unreachable one as
  `opencloud_security_scrape_success 0`, because a metrics pipeline has no
  other way to tell that apart from a scan that stopped running. The names,
  labels and values are the exporter's: both formats now render one reading of
  the scan rather than each deciding for itself what a waived measure counts
  as - see
  [ADR 0054](adr/0054-metrics-are-collected-once-and-rendered-twice.md).

- **A Helm chart installs the Kubernetes deployment this project documents.**
  [`contrib/helm/check-opencloud-security`](contrib/helm/check-opencloud-security)
  renders the scheduled scan as a `CronJob` and, when asked for, the shared
  scan service with a `NetworkPolicy` naming the instances it may reach.
  Four values have no default and an install that omits one is refused rather
  than rendered: the image tag, because the release schedule ships inside the
  image and `latest` would move the verdict under a running alert; the hosts,
  because a Job with no host scans nothing daily while looking like
  monitoring; the scan service's token, because an untokened one scans any
  host its callers name; and that policy's allowlist, because a policy with no
  egress rule is a different policy rather than an unfinished one. The chart
  writes no `Secret` and carries no version of its own - every credential is
  read from one you created and named. `tests/test_helm_chart.py` holds every
  flag it can emit against the plugin's own argument parser.

- **A finished scan can be shown as a grade badge.**
  `GET /api/scans/{uuid}/badge.svg` renders the letter as a small SVG this
  service draws itself - no badge service, no external font, no script,
  because an image fetched from somebody else's server would hand them the
  result URL in a referrer on every view, and that URL's uuid is the whole of
  the authorisation. It carries nothing the scanned instance chose: no
  hostname, no product, no version. It answers 404 for an unknown or expired
  uuid and 409 while the scan is running, like every other reading of one, and
  keeps the service-wide `no-store`. A badge therefore lives exactly as long
  as its scan - an hour by default - which makes it right for a ticket or a
  chat message and wrong for a README; there is deliberately no badge for a
  hostname, because that would be a permanent handle on somebody's instance.
  See [ADR 0055](adr/0055-a-badge-is-a-rendering-of-one-scan-not-a-handle-on-an-instance.md).

- **The reference data can be subscribed to.** `/advisories.atom` and
  `/release-schedule.atom` publish the advisory database and the release
  lifecycle as Atom feeds, built from the same functions `/catalogue` and the
  scan pipeline use. Both documents refresh themselves daily and may only gain
  knowledge, and until now noticing a new advisory meant reopening a page and
  remembering what had been there. The feeds name no instance, carry no uuid
  and take no parameter, which is what lets them be publicly cacheable under
  [ADR 0031](adr/0031-a-response-is-uncacheable-until-a-route-opts-in.md);
  advisory titles and descriptions come from a feed this project does not
  control and are carried as escaped text rather than markup. See
  [ADR 0056](adr/0056-the-reference-data-is-subscribable.md).

### Changed

- **The CSV export records two facts the findings table cannot carry.** A
  `Update available` row and an `HTTPS enforced` row now sit with the header
  block, because both are single measurements that live outside the per-finding
  table and a report read back without them cannot tell "no" from "never
  recorded". A file downloaded before this is still readable: the comparison
  leaves those two measurements out of *both* sides rather than guessing at
  them, and says on the page that it did. Anything parsing that CSV by row
  position rather than by label will need adjusting.

- **The bundled release schedule and advisory database were re-checked against
  their published sources.** Neither moved: the schedule still names OpenCloud
  7.2.4 as production and 8.0.0 as rolling, and the advisory database still
  holds the same two records. The generated frontend documentation and the
  public and operator search indexes were rebuilt so that the version they
  carry is this release's.
