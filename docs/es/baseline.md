# Notificar solo lo que ha cambiado entre análisis de OpenCloud

Utilice `--baseline` para guardar los hallazgos de cada análisis y compararlos
con la siguiente ejecución. Añada `--warn-on-new` para alertar solo cuando haya
hallazgos nuevos o que hayan empeorado. Los problemas existentes siguen
apareciendo en el informe.

El [README principal](../../README.md#reporting-only-what-changed) contiene la
versión breve. Esta página describe el comportamiento completo: los formatos de
comparación, qué cuenta como regresión y las reglas que impiden que una línea
base oculte algo.

<!-- TOC -->
* [Notificar solo lo que ha cambiado](#reporting-only-what-changed)
  * [Escribir y comparar una línea base](#writing-and-comparing-a-baseline)
  * [Qué cuenta como regresión](#what-counts-as-a-regression)
  * [Aspectos que conviene conocer](#points-worth-knowing)
<!-- TOC -->


## Escribir y comparar una línea base {#writing-and-comparing-a-baseline}

`--baseline` indica el archivo en el que se escriben los hallazgos de cada
ejecución y con el que se compara la siguiente:

```bash
check-opencloud-security -H opencloud.example.com \
    --check-hardening \
    --baseline /var/lib/check_opencloud/baseline.json
```

Por sí sola, esta opción solo añade una línea a la salida (`Baseline: ...`).
Añada `--warn-on-new` para actuar en consecuencia:

```bash
check-opencloud-security -H opencloud.example.com \
    --check-hardening \
    --baseline /var/lib/check_opencloud/baseline.json \
    --warn-on-new
```

La comprobación informa entonces `OK` mientras la situación no cambie, y su
estado normal en cuanto algo es nuevo o ha empeorado. El estado completo se
imprime en cualquier caso: solo se suprime la alerta, nunca la evidencia:

```
OK: nothing new since the last run (WARNING state unchanged).
OpenCloud 7.2.3 on opencloud.example.com, rating: C, last scanned: 2026-01-14
Missing hardening: cspWithoutUnsafeInline (run with --debug for what each means and how to fix it)
Baseline: No new findings since 2026-01-14T09:00:00+00:00 (1 known issue(s) unchanged)
Suppressed by --warn-on-new: this run would otherwise be WARNING (WARNING: 1 hardening measure(s) missing, but no known vulnerabilities.)
```

Cada comparación enumera además los CVE añadidos y resueltos, los cambios en
medidas de refuerzo y en comprobaciones adicionales, los cambios de nota, de
fin de vida y de horizonte de soporte, y los cambios de la versión instalada o
de destino. `text` es el formato predeterminado para los registros. Para el
resumen de un paso de GitHub Actions o un comentario en una pull request,
seleccione Markdown:

```shell
check-opencloud-security -H opencloud.example.com \
  --baseline /var/lib/check_opencloud/baseline.json \
  --diff-format markdown >> "$GITHUB_STEP_SUMMARY"
```

Utilice `--diff-format slack` (o `json`) para obtener JSON de Slack Block Kit.
Cuando hay un webhook configurado, cada comparación con la línea base se
incluye como `baseline_diff`; el formato de Slack coloca además los bloques y
la franja de color en el nivel superior para los webhooks entrantes:

```shell
check-opencloud-security -H opencloud.example.com \
  --baseline /var/lib/check_opencloud/baseline.json \
  --diff-format slack --webhook-url 'https://hooks.slack.com/services/<token>' \
  --webhook-on always
```


## Qué cuenta como regresión {#what-counts-as-a-regression}


- un hallazgo que no estaba la vez anterior: un nuevo aviso de seguridad, una
  medida de refuerzo que ha retrocedido, una comprobación adicional que ha
  empezado a fallar o una actualización recién disponible;
- una nota inferior a la registrada;
- **una versión que ha superado su fin de vida, siempre.** No recibe
  correcciones de seguridad, así que empeora cada día que sigue en producción
  y una línea base nunca puede darla por aceptada.

## Aspectos que conviene conocer {#points-worth-knowing}


- La primera ejecución no tiene nada con qué compararse, así que informa con
  normalidad y se convierte en la línea base. Empezar a usar la opción nunca
  oculta nada.
- Un archivo contiene una entrada por host, así que una lista de `--host`
  separada por comas puede compartirlo.
- Los hallazgos excluidos con `--ignore-hardening` y las medidas que OpenCloud
  tiene fijadas en el código se omiten, exactamente igual que en la línea de
  alerta.
- `--warn-on-new` sin `--baseline` se rechaza: sin un lugar donde recordar la
  ejecución anterior, informaría de "nada nuevo" para siempre.
- Una línea base que no se puede escribir se notifica con una línea de salida y
  nada más. La contabilidad nunca decide el veredicto sobre una instancia.
- El archivo se escribe de forma atómica y con permisos solo para el
  propietario. Guárdelo en un lugar que pertenezca al usuario de
  monitorización, p. ej. `/var/lib/check_opencloud/`.
