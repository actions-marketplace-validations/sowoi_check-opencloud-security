#!/bin/sh
# The updater service of docker-compose.dockerhub.yml (ADR 0070).
#
# Watches the shared update directory for the request the operator's area
# writes, then pulls the published image and recreates the web and worker
# containers of this compose project - a short downtime. It is the only
# container with the Docker socket, and it takes nothing from the request but
# a version string it checks and logs: the image, the services and the
# command are fixed here.
set -eu

DIR="${UPDATE_DIR:-/var/lib/opencloud-scan/update}"
COMPOSE_FILE="${UPDATER_COMPOSE_FILE:-docker-compose.dockerhub.yml}"
SERVICES="web_app arq_worker"
INTERVAL="${UPDATER_INTERVAL:-15}"

# The project this container belongs to, so the recreated containers are the
# same ones rather than a second stack beside them.
PROJECT="$(docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' "$(hostname)")"

status() {
    printf '{"state": "%s", "version": "%s", "at": %s}\n' "$1" "$2" "$(date +%s)" \
        > "$DIR/.status.tmp"
    mv "$DIR/.status.tmp" "$DIR/status"
}

echo "updater: watching $DIR for project $PROJECT"
while :; do
    if [ -f "$DIR/request" ]; then
        version="$(sed -n 's/.*"version": *"\([0-9]*\.[0-9]*\.[0-9]*\)".*/\1/p' "$DIR/request")"
        rm -f "$DIR/request"
        if [ -z "$version" ]; then
            echo "updater: ignoring a request without a plain version"
            status "rejected" ""
        else
            echo "updater: updating to $version"
            status "running" "$version"
            # shellcheck disable=SC2086
            if docker compose -p "$PROJECT" -f "$COMPOSE_FILE" pull $SERVICES \
                && docker compose -p "$PROJECT" -f "$COMPOSE_FILE" up -d --no-deps $SERVICES; then
                status "done" "$version"
            else
                status "failed" "$version"
            fi
        fi
    fi
    sleep "$INTERVAL"
done
