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

# Only one update at a time.
if command -v flock >/dev/null; then
  exec 9>"$INSTALL_DIR/.update.lock"
  flock -n 9 || { echo "Another RogueMediaValidator update is already running." >&2; exit 1; }
fi

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

env_value() { awk -F= -v k="$1" '$1==k{sub(/^[^=]*=/,""); print}' .env | tail -n1 | tr -d '\r ' || true; }

set_env() {
  local key=$1 value=$2
  if grep -q "^${key}=" .env; then
    sed -i "s#^${key}=.*#${key}=${value}#" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

BASE="https://raw.githubusercontent.com/RogueAssassin/RogueMediaValidator/$REF"
IMAGE_REF="ghcr.io/rogueassassin/roguemediavalidator:$IMAGE_TAG"
STAMP=$(date +%Y%m%d-%H%M%S)
# Backups live next to the install (not /tmp, which is wiped on reboot). Last 10 are kept.
BACKUP_ROOT=${RMV_BACKUP_DIR:-${RMV_BACKUP_TMP:-$INSTALL_DIR/backups/update}}
mkdir -p "$BACKUP_ROOT"
BACKUP="$BACKUP_ROOT/$STAMP"
mkdir -p "$BACKUP"
cp -a compose.yaml .env "$BACKUP/"
[[ -f compose.override.yaml ]] && cp -a compose.override.yaml "$BACKUP/"
[[ -f update.sh ]] && cp -a update.sh "$BACKUP/"
(cd "$BACKUP_ROOT" && ls -1dt ./[0-9]*-[0-9]*/ 2>/dev/null | tail -n +11 | xargs -r rm -rf) || true

# RMV_RUNTIME=podman|docker in .env pins the engine; otherwise the first working one is used.
deploy_engine=$(env_value RMV_RUNTIME)
if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then
    deploy_engine=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then
    deploy_engine=docker
  else
    echo "Unable to detect a working Podman or Docker runtime." >&2
    exit 2
  fi
fi

compose_files=(-f "$INSTALL_DIR/compose.yaml")
# Local customisations belong in compose.override.yaml; it survives updates.
[[ -f "$INSTALL_DIR/compose.override.yaml" ]] && compose_files+=(-f "$INSTALL_DIR/compose.override.yaml")

if [[ $deploy_engine == podman ]]; then
  podman compose version >/dev/null 2>&1 || {
    echo "Podman Compose provider is unavailable." >&2
    exit 2
  }
  compose_cmd=(podman compose --env-file "$INSTALL_DIR/.env" "${compose_files[@]}")
else
  if docker compose version >/dev/null 2>&1; then
    compose_cmd=(docker compose --env-file "$INSTALL_DIR/.env" "${compose_files[@]}")
  elif command -v docker-compose >/dev/null; then
    compose_cmd=(docker-compose --env-file "$INSTALL_DIR/.env" "${compose_files[@]}")
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

PORT=$(env_value RMV_HTTP_PORT)
[[ $PORT =~ ^[0-9]+$ ]] || PORT=7811
BIND=$(env_value RMV_HTTP_BIND)
[[ -z $BIND || $BIND == 0.0.0.0 ]] && BIND=127.0.0.1
HEALTH_URL="http://$BIND:$PORT/healthz"

HEALTH_FILE="${TMPDIR:-/tmp}/roguemediavalidator-health.$$"
trap 'rm -f "$HEALTH_FILE"' EXIT

wait_for_health() {
  local attempt
  for attempt in {1..30}; do
    if curl -fsS --max-time 5 "$HEALTH_URL" >"$HEALTH_FILE" 2>/dev/null; then return 0; fi
    sleep 2
  done
  return 1
}

# --- 1. Download deployment files (nothing is installed yet) -----------------
curl -fsSL "$BASE/compose.yaml" -o "$BACKUP/compose.download" || {
  echo "RogueMediaValidator source ref '$REF' is unavailable." >&2
  exit 3
}
curl -fsSL "$BASE/update.sh" -o "$BACKUP/update.download" || {
  echo "RogueMediaValidator updater is unavailable on '$REF'." >&2
  exit 3
}

# --- 2. Pull FIRST so a missing tag cannot leave config half-updated ----------
RUNNING_IMAGE=$("$deploy_engine" inspect roguemediavalidator --format '{{.Image}}' 2>/dev/null || true)
"$deploy_engine" pull "$IMAGE_REF" || {
  echo "RogueMediaValidator image tag '$IMAGE_TAG' is not published in GHCR. Nothing was changed." >&2
  exit 4
}
EXPECTED_IMAGE=$("$deploy_engine" image inspect "$IMAGE_REF" --format '{{.Id}}' 2>/dev/null || true)

# Keep the image that is running now addressable so a failed update can return to it.
ROLLBACK_REF=""
if [[ -n $RUNNING_IMAGE && $RUNNING_IMAGE != "$EXPECTED_IMAGE" ]]; then
  ROLLBACK_REF="localhost/roguemediavalidator-rollback:$STAMP"
  "$deploy_engine" tag "$RUNNING_IMAGE" "$ROLLBACK_REF" 2>/dev/null || ROLLBACK_REF=""
fi

echo "Running image: ${RUNNING_IMAGE:-none}"
echo "Pulled image:  ${EXPECTED_IMAGE:-unknown}"

# --- 3. Install updated files ------------------------------------------------
if ! diff -q compose.yaml "$BACKUP/compose.download" >/dev/null 2>&1; then
  echo "compose.yaml will change (your previous copy is saved in $BACKUP)."
  echo "Put local customisations in compose.override.yaml so updates do not replace them."
fi
install -m 0644 "$BACKUP/compose.download" "$INSTALL_DIR/compose.yaml"
set_env RMV_IMAGE "$IMAGE_REF"

rollback() {
  local reason=$1
  echo "Update failed: $reason" >&2
  if [[ -z $RUNNING_IMAGE ]]; then
    echo "RogueMediaValidator was not running before the update, so automatic rollback is not possible. Backup: $BACKUP" >&2
    return 1
  fi
  echo "Rolling back to the previous deployment files and image..." >&2
  cp -a "$BACKUP/compose.yaml" "$BACKUP/.env" "$INSTALL_DIR/"
  # When the image itself changed, the restored tag may now resolve to the new image.
  [[ -n $ROLLBACK_REF ]] && set_env RMV_IMAGE "$ROLLBACK_REF"
  "$deploy_engine" rm -f roguemediavalidator >/dev/null 2>&1 || true
  if "${compose_cmd[@]}" up -d --remove-orphans && wait_for_health; then
    echo "Rollback succeeded. Backup: $BACKUP" >&2
    if [[ -n $ROLLBACK_REF ]]; then
      echo "RMV_IMAGE in .env now points at $ROLLBACK_REF (the version you were running)." >&2
      echo "Set RMV_IMAGE back to a published tag when you are ready to try again." >&2
    fi
  else
    echo "Rollback did not restore a healthy service. Backup: $BACKUP" >&2
    "${compose_cmd[@]}" ps >&2 || true
    "$deploy_engine" logs --tail 100 roguemediavalidator >&2 || true
  fi
  return 1
}

# --- 4. Recreate and verify --------------------------------------------------
if [[ -n "$EXPECTED_IMAGE" && -n "$RUNNING_IMAGE" && "$EXPECTED_IMAGE" != "$RUNNING_IMAGE" ]]; then
  echo "RogueMediaValidator image changed; replacing existing container..."
  "$deploy_engine" rm -f roguemediavalidator >/dev/null
fi

if ! "${compose_cmd[@]}" up -d --remove-orphans; then
  rollback "compose could not recreate the container" || true
  exit 5
fi

NEW_IMAGE=$("$deploy_engine" inspect roguemediavalidator --format '{{.Image}}' 2>/dev/null || true)
if [[ -n "$EXPECTED_IMAGE" && "$NEW_IMAGE" != "$EXPECTED_IMAGE" ]]; then
  echo "Expected image: $EXPECTED_IMAGE" >&2
  echo "Running image:  ${NEW_IMAGE:-missing}" >&2
  rollback "the running image is not the one that was pulled" || true
  exit 6
fi

if wait_for_health; then
  echo
  cat "$HEALTH_FILE"
  echo
  echo "RogueMediaValidator $CHANNEL update complete."
  [[ $CHANNEL == testing ]] && echo "TESTING BUILD ACTIVE: $REF ($IMAGE_TAG)"
  # The rollback tag is only needed while the update can still fail.
  [[ -n $ROLLBACK_REF ]] && "$deploy_engine" rmi "$ROLLBACK_REF" >/dev/null 2>&1 || true
  install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"
  echo "Updater refreshed for the next run."
  exit 0
fi

rollback "health check did not pass" || true
"$deploy_engine" logs --tail 100 roguemediavalidator >&2 || true
exit 1
