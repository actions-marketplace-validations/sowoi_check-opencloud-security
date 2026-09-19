# Release-Kanäle, Supportende und Updates

OpenCloud pflegt Rolling-, Production- und LTS-Releases parallel. Ob eine Version noch unterstützt wird, hängt deshalb auch von ihrem Kanal ab. Der Scanner bewertet Versionslinien, berücksichtigt den Release-Zeitplan und empfiehlt ein Update passend zum gewählten Kanal.

Den aktuellen Stand der Kanäle und die Einstellungen zur End-of-Life-Prüfung findest du im [Haupt-README](../../README.md#end-of-life-detection). Die folgenden älteren Versionsnummern dienen als Beispiele.

## Warum die Versionsnummer allein nicht genügt {#why-a-version-number-is-not-an-answer}

Alle Kanäle verwenden dieselbe Versionsfolge. Im Beispiel ist `7.2.3` auf Production aktuell, während Rolling bereits `7.4.0` erreicht hat. Das höhere `7.3.0` ist auf Rolling schon abgelöst und erhält dort keine Korrekturen mehr.

Der Scanner arbeitet deshalb mit **Versionslinien** (`MAJOR.MINOR`): `7.2.3` gehört zur Linie `7.2`. Eine Linie kann mehreren Kanälen angehören, etwa nach einer Übernahme von Rolling nach Production. Ohne ausdrückliche Kanalwahl verwendet der Scanner den Kanal, der diese Linie am längsten unterstützt.

Der mitgelieferte Zeitplan liegt in `opencloud_local_scan/data/release_schedule.json`. Er wird aus der OpenCloud-Lebenszyklusdokumentation gewonnen, die im Gegensatz zur allgemeinen GitHub-Release-Liste auch den Release-Typ nennt. Der [Zeitplan-Workflow](../../.github/workflows/release-schedule.yml) und der Release-Workflow aktualisieren die Datei sowie die zugehörige Tabelle im Haupt-README. Die Beispiele auf dieser Seite werden nicht automatisch ersetzt.

## Aussagekraft des mitgelieferten Zeitplans {#what-the-bundled-schedule-can-and-cannot-tell-you}

Beachte diese Grenzen:

- **LTS-Releases erfordern ein Abonnement.** Die Dokumentation nennt die Linien, auch wenn einzelne Releases nicht öffentlich erscheinen. Bei einem abweichenden vertraglichen Supportzeitraum kannst du mit `release_schedule` einen eigenen Zeitplan vorgeben.
- **Eine neuere als die bekannte Version führt allein nicht zu F.** Der Zeitplan kann zwischen Paketupdates veralten. Eine zügig aktualisierte Instanz wird deshalb nicht allein wegen fehlender Referenzdaten als nicht unterstützt bewertet und erhält keine rückwärts gerichtete Empfehlung.
- **Veraltete Daten werden kenntlich gemacht.** Liegt die Version über der neuesten bekannten Version ihrer Linie oder auf einer neueren Linie als im Zeitplan, setzt das Ergebnis `lifecycle.scheduleStale` und ergänzt `scheduleNote`, `scheduleUpdated` und `scheduleSource`. Die Plugin-Ausgabe enthält dann beispielsweise:

  ```
  Release schedule: 7.4.1 is newer than anything in the bundled release schedule (generated 2026-08-12), so that schedule is probably out of date. This is not counted against the instance. Check the current support window at https://docs.opencloud.eu/docs/admin/resources/lifecycle/, and regenerate the schedule with scripts/update_release_schedule.py.
  ```

  Prüfe in diesem Fall die [veröffentlichte Lebenszyklusdokumentation][lifecycle] und aktualisiere Paket oder Zeitplan. Ein bereits bekanntes Supportende bleibt wirksam: Ein neuer Patch innerhalb einer abgelaufenen Linie verlängert deren Support nicht.

## Updates folgen dem gewählten Kanal {#the-recommended-release-follows-your-track}

Die insgesamt höchste Release-Version ist bei OpenCloud in der Regel ein Rolling-Release. Ein Production- oder LTS-System soll durch eine Update-Empfehlung nicht auf dessen kürzeren Supportzyklus wechseln.

Der Scanner verwendet daher den [Release-Zeitplan](../../README.md#end-of-life-detection), um ein Ziel im passenden Kanal zu wählen:

| Installiert | Kanal | Empfehlung | Grund |
|:--|:--|:--|:--|
| `7.2.3` | production | keine | Im Beispiel aktuelles Production-Release, obwohl Rolling bereits `7.4.0` bietet |
| `7.2.0` | production | `7.2.3` | Neuester Patch derselben Linie |
| `7.3.0` | rolling | `7.4.0` | Nächstes Rolling-Release |
| `4.0.0` | LTS | `4.0.8` | Patch mit Rückportierungen für die LTS-Linie |

`newestRelease` nennt im JSON und Webhook weiterhin die insgesamt neueste Version. Sie wird dadurch aber nicht automatisch zum empfohlenen Update. Meldet der Feed einen neueren Patch derselben Linie als der gebündelte Zeitplan, wird diese neuere Information verwendet.

## Den Release-Kanal festlegen {#declaring-your-release-track}

Ohne Vorgabe wählt der Scanner den längsten bekannten Support für die Versionslinie. Im Beispiel gilt `7.2.3` daher als unterstütztes Production-Release, obwohl diese Linie auch auf Rolling erschienen ist.

Wenn du dem Rolling-Kanal folgst, gilt dieselbe Version nach Erscheinen des Nachfolgers als abgelöst. Lege den Kanal dafür mit `--release-track` fest:

```bash
check-opencloud-security --host opencloud.example.com --release-track rolling
```

`--release-track auto` entspricht dem Weglassen der Option. Der Scanner leitet den Kanal aus dem Zeitplan ab:

```bash
check-opencloud-security --host opencloud.example.com --release-track auto
```

| Installiert | Vorgabe | Ergebnis im Beispiel |
|:--|:--|:--|
| `7.2.3` | keine oder `auto` | Unterstützt als aktuelles Production-Release |
| `7.2.3` | `production` | Unterstützt als aktuelles Production-Release |
| `7.2.3` | `rolling` | End of Life; durch `7.4.0` abgelöst, Update auf `7.4.0` |
| `7.4.0` | `production` | Dem Production-Kanal mit aktuellem `7.2.3` voraus; nicht als End of Life bewertet |
| `2.3.0` | `production` | End of Life; hinter Production zurück, Update auf `7.2.3` |
| `4.0.8` | `lts` | Bis zum Ende des zweijährigen Zeitraums unterstützt |

Dabei gelten zwei Regeln:

- **Dem Kanal voraus zu sein ist kein eigener Fehler.** Eine neuere Version wird entsprechend gekennzeichnet und nicht allein wegen der Kanalabweichung mit F bewertet.
- **Es wird kein Downgrade empfohlen.** Gibt es im gewählten Kanal keine höhere Zielversion, bleibt die Empfehlung leer. Die Begründung beschreibt die Situation.

Die Ausgabe kennzeichnet eine ausdrücklich gesetzte Kanalwahl:

```
Release lifecycle: 7.2 (rolling track declared), out of support since 2026-07-14, upgrade to 7.4.0
```

Ein unbekannter Wert wird ignoriert. Der Scanner fällt auf die automatische Zuordnung zurück, statt die Prüfung wegen eines Tippfehlers abzubrechen.

[lifecycle]: https://docs.opencloud.eu/docs/admin/resources/lifecycle/

## Warnung vor dem Supportende {#warning-before-the-end-of-life}

Das Supportende ist an dem Tag `CRITICAL`, an dem es eintritt - zu spät, um
ein Update zu planen. `--eol-warning TAGE` (`COS_EOL_WARNING`, YAML
`eol_warning`) macht aus einem sonst `OK`-Ergebnis ein `WARNING`, sobald die
laufende Linie höchstens noch `TAGE` Tage unterstützt wird:

```text
WARNING: The 7.2 release line reaches end of life on 2026-10-14 (20 days left). Upgrade to 7.4.0.
```

Es hebt nur `OK` an; ein Ergebnis, das schon `WARNING` oder `CRITICAL` ist,
behält seine eigene Zeile. Eine Linie ohne veröffentlichtes Supportende warnt
nie. `0`, der Standard, schaltet es ab.

## Behebt das Update die Sicherheitshinweise? {#does-the-upgrade-clear-the-advisories}

Hat die installierte Version bekannte Sicherheitshinweise, hält der Scan
`upgradePath` fest: was das empfohlene Update an jedem davon ändert.

```json
{"upgradePath": {"target": "7.2.4", "fixes": ["GHSA-aaaa"],
  "stillAffected": ["GHSA-bbbb"], "safeVersion": "7.3.0"}}
```

Jeder Bereich eines Hinweises wird gegen das Ziel geprüft, ein auf eine
andere Linie zurückportierter Fix zählt also mit. `safeVersion` ist die
niedrigste Version, die jeden noch fehlenden Fix enthält, oder `null`, wenn es
für einen davon noch keinen gibt. Das Plugin gibt das als Detailzeile aus.

## Jedes Upgrade vorab durchspielen {#rehearse-every-upgrade}

`upgradePath` beschreibt die eine Version, die der Scan empfiehlt.
`upgradeRehearsal` beschreibt jede Version, auf die sich ein Wechsel lohnt:
den neuesten Patch der installierten Linie und die neueste Version jeder
späteren Linie (nur Linien des festgelegten Release-Kanals, wenn die
Instanz einen Kanal vorgibt). Für jede Version werden die Hinweise genannt,
die sie `fixes`, von denen sie noch `stillAffected` ist, sowie neu eingeführte
Hinweise (`introduces`), ob sie `endOfLife` ist und welches `rating` der Scan
für sie vergeben würde.

```json
{"upgradeRehearsal": [
  {"version": "7.2.4", "line": "7.2", "recommended": false,
   "fixes": ["GHSA-aaaa"], "stillAffected": ["GHSA-bbbb"], "introduces": [],
   "endOfLife": false, "versionRating": 2, "rating": 2}
]}
```

Die Bewertung verwendet dieselben Versionsregeln wie der Scan. Fehlende
Prüfungen der Instanz begrenzen sie weiterhin (`versionRating` zeigt, was
allein aufgrund der Version möglich wäre), denn ein Upgrade ändert die
Version, nicht den Proxy davor. Das Plugin gibt eine Detailzeile mit seinen
eigenen Bewertungsbuchstaben aus:

```text
Upgrade rehearsal: 7.2.4 fixes 1 finding, leaves 1, reaches rating D; 7.3.0 fixes 2 findings, leaves 0, reaches rating A+.
```

Die Vorabprüfung kennt nur den gebündelten oder aktualisierten Zeitplan und
die Beratungsdatenbank. Eine später veröffentlichte Version oder ein später
veröffentlichter Hinweis kann das Ergebnis ändern.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
