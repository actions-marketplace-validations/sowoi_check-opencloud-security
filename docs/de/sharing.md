# Öffentliche Freigabelinks prüfen

Bei einem öffentlichen Freigabelink kann bereits die URL den Zugriff ermöglichen. Der Scanner liest in den Capabilities, ob Links ein Passwort benötigen und ob eine automatische Ablaufregel gemeldet wird.

## 1. Passwortpflicht: `publicLinkPasswordEnforced` {#1-can-a-public-link-be-created-without-a-password-publiclinkpasswordenforced}

Die Felder `enforced_for` geben die Passwortpflicht je Freigabetyp an: schreibgeschützt, nur Upload und bearbeitbar. Die Prüfung besteht nur, wenn alle Typen ein Passwort verlangen.

OpenCloud verlangt standardmäßig Passwörter für schreibgeschützte Links, aber nicht für beschreibbare. Letztere können je nach Freigabetyp das Hochladen oder Ändern von Dateien ohne zusätzliche Anmeldung erlauben.

**Behebung:** Setze `OC_SHARING_PUBLIC_SHARE_MUST_HAVE_PASSWORD=true` und `OC_SHARING_PUBLIC_WRITEABLE_SHARE_MUST_HAVE_PASSWORD=true`. Verwende diese globalen Namen statt der veralteten `FRONTEND_OCS_*`-Varianten. Die Anforderungen an das Linkpasswort selbst prüft [`passwordPolicyEnforced`](../authentication.md#5-is-the-link-password-policy-strong-enough-passwordpolicyenforced).

## 2. Automatischer Ablauf: `publicLinkExpirationEnforced` {#2-do-public-links-expire-automatically-publiclinkexpirationenforced}

Der Scanner liest `files_sharing.public.expire_date.enabled`. OpenCloud legt diesen Wert im Frontend-Dienst fest auf `false`; eine Konfigurationsänderung kann ihn nicht beeinflussen.

**Dieser Wert löst keinen Alarm aus.** Er fehlt in „Missing hardening“, `hardenings_missing` und dem Webhook. Im Ergebnisdokument und in `--debug` bleibt er mit Erklärung erhalten. Siehe [Fest vorgegebene Werte](../hardening.md#measures-that-are-not-settings).

Der Wert bleibt im Katalog, damit eine spätere Änderung der Capability erkennbar wird. Für `userEnumerationRestricted` gilt derselbe Ansatz; siehe [Kontensuche](../authentication.md#4-is-account-search-restricted-to-shared-groups-userenumerationrestricted).

Wenn du einen verbindlichen Ablauf benötigst, lege ihn pro Freigabe fest oder setze einen gesonderten Prozess zur planmäßigen Rücknahme von Freigaben ein. Eine allgemeine Einstellung für den hier gemessenen Wert steht derzeit nicht zur Verfügung.

## Weitere Sharing-Capabilities {#what-else-is-in-that-document-and-why-none-of-it-is-checked}

Die folgenden Angaben werden nicht als eigene Prüfungen bewertet. Grundlage ist `services/frontend/pkg/revaconfig/config.go` in [opencloud-eu/opencloud](https://github.com/opencloud-eu/opencloud):

| Capability | Grund |
|:--|:--|
| `auto_accept_share`, `share_with_group_members_only`, `share_with_membership_groups_only`, `group_sharing`, `sharing_roles`, `api_enabled` | Fest im Code vorgegeben; liefern keine Aussage über die individuelle Konfiguration. |
| `public.upload`, `public.send_mail`, `public.social_share`, `public.alias`, `public.multiple`, `public.supports_upload_only`, `public.can_edit` | Ebenfalls fest vorgegeben. |
| `federation.incoming`, `federation.outgoing` | Über `OC_ENABLE_OCM` beeinflussbar, laut OpenCloud aber keine unterstützte Änderung des Backend-Verhaltens; die Angabe steuert die Information für Clients. |
| `public.default_permissions` | Über `FRONTEND_DEFAULT_LINK_PERMISSIONS` konfigurierbar: `0` intern, `1` öffentlicher Betrachter, Standard `1`. Wird derzeit nicht bewertet, da die Standardkonfiguration sonst einen weiteren allgemeinen Befund erhielte. |
| `deny_access`, `search_min_length` | Veraltetes Experiment beziehungsweise Einstellung der Suchoberfläche; daraus folgt kein eigener Nachweis über den Datenzugriff. |

Neue Prüfungen müssen sich auf Einstellungen beziehen, die Betreiber tatsächlich ändern können.

## Schweregrad und Bewertung {#severity-and-rating-impact}

Beide Werte gehören zu den Härtungsangaben und werden mit `--check-hardening` beziehungsweise im Webbericht angezeigt. Ein Fehler bei `publicLinkPasswordEnforced` kann einen sonst erfolgreichen Plugin-Status auf WARNING setzen, begrenzt für sich allein aber nicht die numerische Note. `publicLinkExpirationEnforced` ist aus der Alarmierung ausgeschlossen. Die vollständige Übersicht steht unter [Härtungsmaßnahmen](../hardening.md).

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
