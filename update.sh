#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MODE=${1:-latest}
TARGET=${MODE#v}

[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not root/sudo." >&2; exit 1; }
for cmd in curl awk; do
  command -v "$cmd" >/dev/null || { echo "Missing runtime: $cmd" >&2; exit 2; }
done

if [[ ! $TARGET =~ ^(latest|main|testing|[0-9]+\.[0-9]+\.[0-9]+(-testing|-rc[0-9]+)?)$ ]]; then
  echo "Usage: ./update.sh [latest|main|testing|X.Y.Z|X.Y.Z-testing|X.Y.Z-rcN]" >&2
  exit 2
fi

cd "$INSTALL_DIR"
[[ -f compose.yaml && -f .env ]] || {
  echo "Incomplete RogueMediaValidator installation at $INSTALL_DIR" >&2
  exit 2
}

REF=main
IMAGE_TAG=latest
CHANNEL=production

case "$TARGET" in
  latest|main)
    REF=main
    IMAGE_TAG=latest
    ;;
  testing)
    REF=testing
    IMAGE_TAG=testing
    CHANNEL=testing
    ;;
  *-testing)
    REF=testing
    IMAGE_TAG="$TARGET"
    CHANNEL=testing
    ;;
  *)
    REF=main
    IMAGE_TAG="$TARGET"
    ;;
esac

BASE="https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/$REF"
BACKUP_ROOT=${RMV_BACKUP_TMP:-${TMPDIR:-/tmp}/roguemediavalidator/update-backups}
mkdir -p "$BACKUP_ROOT"
BACKUP="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
cp -a compose.yaml .env "$BACKUP/"
[[ -f update.sh ]] && cp -a update.sh "$BACKUP/"

deploy_engine=""
if command -v podman >/dev/null && podman info >/dev/null 2>&1; then
  deploy_engine=podman
elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  deploy_engine=docker
else
  echo "Unable to detect a working Podman or Docker runtime." >&2
  exit 2
fi

if [[ $deploy_engine == podman ]]; then
  podman compose version >/dev/null 2>&1 || {
    echo "Podman Compose provider is unavailable." >&2
    exit 2
  }
  compose_cmd=(podman compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
else
  if docker compose version >/dev/null 2>&1; then
    compose_cmd=(docker compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
  elif command -v docker-compose >/dev/null; then
    compose_cmd=(docker-compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
  else
    echo "Docker Compose provider is unavailable." >&2
    exit 2
  fi
fi

echo "RogueMediaValidator update target: $TARGET"
echo "Channel: $CHANNEL"
echo "Source ref: $REF"
echo "Deployment runtime: $deploy_engine"
echo "Image tag: $IMAGE_TAG"
echo "Backup: $BACKUP"

curl -fsSL "$BASE/compose.yaml" -o "$BACKUP/compose.download" || {
  echo "RogueMediaValidator source ref '$REF' is unavailable." >&2
  exit 3
}
curl -fsSL "$BASE/update.sh" -o "$BACKUP/update.download" || {
  echo "RogueMediaValidator updater is unavailable on '$REF'." >&2
  exit 3
}
install -m 0644 "$BACKUP/compose.download" "$INSTALL_DIR/compose.yaml"

set_env() {
  local key=$1 value=$2
  if grep -q "^${key}=" .env; then
    sed -i "s#^${key}=.*#${key}=${value}#" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

set_env RMV_IMAGE "ghcr.io/rogueassassin/roguemediavalidator:$IMAGE_TAG"

IMAGE_REF="ghcr.io/rogueassassin/roguemediavalidator:$IMAGE_TAG"
"$deploy_engine" pull "$IMAGE_REF" || {
  echo "RogueMediaValidator image tag '$IMAGE_TAG' is not published in GHCR." >&2
  exit 4
}

EXPECTED_IMAGE=$("$deploy_engine" image inspect "$IMAGE_REF" --format '{{.Id}}' 2>/dev/null || true)
RUNNING_IMAGE=$("$deploy_engine" inspect roguemediavalidator --format '{{.Image}}' 2>/dev/null || true)

echo "Running image: ${RUNNING_IMAGE:-none}"
echo "Pulled image:  ${EXPECTED_IMAGE:-unknown}"

if [[ -n "$EXPECTED_IMAGE" && -n "$RUNNING_IMAGE" && "$EXPECTED_IMAGE" != "$RUNNING_IMAGE" ]]; then
  echo "RogueMediaValidator image changed; replacing existing container..."
  "$deploy_engine" rm -f roguemediavalidator >/dev/null
fi

if ! "${compose_cmd[@]}" up -d --remove-orphans; then
  echo "Compose recreate failed. Deployment backup remains at $BACKUP" >&2
  exit 5
fi

NEW_IMAGE=$("$deploy_engine" inspect roguemediavalidator --format '{{.Image}}' 2>/dev/null || true)
if [[ -n "$EXPECTED_IMAGE" && "$NEW_IMAGE" != "$EXPECTED_IMAGE" ]]; then
  echo "RogueMediaValidator update verification failed." >&2
  echo "Expected image: $EXPECTED_IMAGE" >&2
  echo "Running image:  ${NEW_IMAGE:-missing}" >&2
  exit 6
fi

PORT=$(awk -F= '$1=="RMV_HTTP_PORT"{print $2}' .env | tail -n1 | tr -d '\r ' || true)
[[ $PORT =~ ^[0-9]+$ ]] || PORT=7811

HEALTH_FILE="${TMPDIR:-/tmp}/roguemediavalidator-health.$$"
trap 'rm -f "$HEALTH_FILE"' EXIT

for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:$PORT/healthz" >"$HEALTH_FILE" 2>/dev/null; then
    echo
    cat "$HEALTH_FILE"
    echo
    echo "RogueMediaValidator $CHANNEL update complete."
    [[ $CHANNEL == testing ]] && echo "TESTING BUILD ACTIVE: $REF ($IMAGE_TAG)"
    install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"
    echo "Updater refreshed for the next run."
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Deployment backup remains at $BACKUP" >&2
"${compose_cmd[@]}" ps >&2 || true
"$deploy_engine" logs --tail 100 roguemediavalidator >&2 || true
exit 1
