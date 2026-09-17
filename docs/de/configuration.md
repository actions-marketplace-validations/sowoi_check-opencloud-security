# Zugangsdaten in der Konfiguration

GitHub-Token, Webhook-URL und Dienst-Token müssen nicht im Klartext in der Konfiguration oder Prozessumgebung stehen. Stattdessen kannst du auf eine Datei, eine Umgebungsvariable oder eine andere Quelle verweisen. Das Plugin liest den Wert erst, wenn es ihn benötigt.

Wo das Plugin seine Konfigurationsdatei sucht und wie die Schlüssel den Umgebungsvariablen entsprechen, erklärt [Konfigurationsdatei und Zugangsdaten](../../README.md#configuration-file-and-secrets). Ein vollständig kommentiertes Beispiel liegt unter `config/check-opencloud-security.example.yml`.

## Unterstützte Verweise {#reference-forms}

Anstelle eines Werts kannst du eines dieser vier Präfixe verwenden:

| Verweis | Gelesener Wert |
|:--|:--|
| `secret://name` | Inhalt von `<secrets.dir>/name`, bei Docker- und Kubernetes-Secrets üblicherweise `/run/secrets/name` |
| `file:///path/to/file` | Inhalt der angegebenen Datei |
| `env://VARIABLE` | Wert der Umgebungsvariablen |
| `exec://command --arg` | Standardausgabe des Befehls; erfordert `secrets.allow_exec: true` |

Alternativ kannst du `_file` an einen Schlüssel oder eine Variable anhängen: `COS_RELEASES_TOKEN_FILE=/run/secrets/token` oder `token_file: /run/secrets/token`. Abschließende Zeilenumbrüche werden entfernt; eine mit `echo secret > file` erstellte Datei funktioniert daher ebenfalls.

## Außerhalb eines Containers {#outside-a-container}

`secret://name` sucht im Verzeichnis `secrets.dir` (`COS_SECRETS_DIR`). Der Standard `/run/secrets` entspricht dem üblichen Mountpfad von Docker und Kubernetes. Für eine native Installation gib dein eigenes Verzeichnis an:

```shell
mkdir -p /etc/check-opencloud-security/secrets
printf '%s' '<github-token>' > /etc/check-opencloud-security/secrets/releases_token
chmod 600 /etc/check-opencloud-security/secrets/*

export COS_SECRETS_DIR=/etc/check-opencloud-security/secrets
check-opencloud-security --host opencloud.example.com \
  --release-token 'secret://releases_token'
```

Vorlagen für die Secret-Dateien findest du unter [`secrets/`](../../secrets/README.md). Kopiere diese und ersetze die Platzhalter durch deine Werte.

## Marken und Unabhängigkeit

Dies ist ein unabhängiges Community-Projekt. Es ist nicht mit OpenCloud GmbH
verbunden und wird von ihr nicht unterstützt. OpenCloud und zugehörige Marken
gehören ihren jeweiligen Inhabern und benennen hier die geprüfte Software.
