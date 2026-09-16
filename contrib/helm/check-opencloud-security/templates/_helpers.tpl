{{/* The chart's name, overridable, truncated to what a label accepts. */}}
{{- define "check-opencloud-security.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "check-opencloud-security.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "check-opencloud-security.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "check-opencloud-security.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "check-opencloud-security.selectorLabels" -}}
app.kubernetes.io/name: {{ include "check-opencloud-security.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
The image reference.

`tag` has no default: the release schedule and the newest known OpenCloud
version ship inside the image, so a chart that quietly fell back to `latest`
would let the verdict change under a scan somebody is alerting on.
*/}}
{{- define "check-opencloud-security.image" -}}
{{- $tag := required "image.tag is required: pin the release you want to run, because the release schedule ships inside the image" .Values.image.tag -}}
{{- printf "%s:%s" .Values.image.repository $tag -}}
{{- end -}}

{{- define "check-opencloud-security.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "check-opencloud-security.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
The plugin's arguments, built from values so that an operator writes YAML
rather than remembering flag names. Anything this does not cover goes in
cronJob.extraArgs verbatim.
*/}}
{{- define "check-opencloud-security.args" -}}
{{- $cron := .Values.cronJob -}}
{{- /* `required` passes an empty list through, which would render --host= */ -}}
{{- if not $cron.hosts }}{{ fail "cronJob.hosts must name at least one instance to scan" }}{{ end -}}
- --host={{ join "," $cron.hosts }}
{{- if $cron.port }}
- --port={{ $cron.port }}
{{- end }}
{{- if $cron.checkHardening }}
- --check-hardening
{{- end }}
{{- if $cron.updateWarning }}
- --update-warning
{{- end }}
{{- if $cron.releaseTrack }}
- --release-track={{ $cron.releaseTrack }}
{{- end }}
{{- range $cron.ignoreHardenings }}
- --ignore-hardening={{ . }}
{{- end }}
{{- if kindIs "float64" $cron.warning }}
- --warning={{ $cron.warning }}
{{- end }}
{{- if kindIs "float64" $cron.critical }}
- --critical={{ $cron.critical }}
{{- end }}
{{- if $cron.format }}
- --format={{ $cron.format }}
{{- end }}
{{- if $cron.webhook.enabled }}
- --webhook-url=$(COS_WEBHOOK_URL)
- --webhook-on={{ $cron.webhook.on }}
{{- if $cron.webhook.format }}
- --webhook-format={{ $cron.webhook.format }}
{{- end }}
{{- if $cron.webhook.secretKey }}
- --webhook-secret=$(COS_WEBHOOK_SECRET)
{{- end }}
{{- end }}
{{- range $cron.extraArgs }}
- {{ . | quote }}
{{- end }}
{{- end -}}

{{/*
The environment of the scheduled scan: the secret values it reads, and
whatever else the operator added. A key is only wired up when it was named,
so a deployment that wants none of them mounts none of them.
*/}}
{{- define "check-opencloud-security.cronEnv" -}}
{{- $cron := .Values.cronJob -}}
{{- if and $cron.releasesTokenKey $cron.existingSecret }}
- name: COS_RELEASES_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ $cron.existingSecret }}
      key: {{ $cron.releasesTokenKey }}
{{- end }}
{{- if $cron.webhook.enabled }}
- name: COS_WEBHOOK_URL
  valueFrom:
    secretKeyRef:
      name: {{ required "cronJob.existingSecret must name the Secret holding the webhook URL" $cron.existingSecret }}
      key: {{ $cron.webhook.urlKey }}
{{- if $cron.webhook.secretKey }}
- name: COS_WEBHOOK_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ $cron.existingSecret }}
      key: {{ $cron.webhook.secretKey }}
{{- end }}
{{- end }}
{{- with $cron.env }}
{{ toYaml . }}
{{- end }}
{{- end -}}
