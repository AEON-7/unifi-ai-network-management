#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_DIR="${OPENCLAW_DIR:-$HOME/.openclaw}"
SKILL_DST="$OPENCLAW_DIR/workspace/skills/unifi-api"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
ENV_FILE="$OPENCLAW_DIR/unifi.env"
STAMP="$(date +%Y%m%d-%H%M%S)"
SHELL_RC="${SHELL_RC:-$HOME/.bashrc}"

say() { printf '%s\n' "$*"; }

usage() {
  cat <<USAGE
Usage: ./setup.sh [--no-aliases] [--force-env]

Installs:
  Skill:   $SKILL_DST
  Scripts: $BIN_DIR
  Env:     $ENV_FILE

Options:
  --no-aliases  Install files but do not modify shell rc.
  --force-env   Replace existing env file after backing it up.
USAGE
}

ADD_ALIASES=1
FORCE_ENV=0
for arg in "$@"; do
  case "$arg" in
    --no-aliases) ADD_ALIASES=0 ;;
    --force-env) FORCE_ENV=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -d "$REPO_DIR/skill/unifi-api" ]]; then
  echo "Missing skill/unifi-api. Run setup from the repo root." >&2
  exit 1
fi

mkdir -p "$OPENCLAW_DIR/workspace/skills" "$BIN_DIR"
chmod 700 "$OPENCLAW_DIR" 2>/dev/null || true

if [[ -e "$SKILL_DST" ]]; then
  mv "$SKILL_DST" "${SKILL_DST}.bak-${STAMP}"
  say "Existing skill backed up to ${SKILL_DST}.bak-${STAMP}"
fi
cp -a "$REPO_DIR/skill/unifi-api" "$SKILL_DST"
find "$SKILL_DST" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
chmod -R u+rwX,go-rwx "$SKILL_DST"

for script in \
  unifi-api-status \
  unifi-api-configure \
  unifi-api-disable \
  unifi-api-enable \
  unifi-config-backup \
  unifi-config-restore; do
  install -m 700 "$REPO_DIR/scripts/$script" "$BIN_DIR/$script"
done

if [[ -f "$ENV_FILE" && "$FORCE_ENV" -eq 1 ]]; then
  cp -p "$ENV_FILE" "${ENV_FILE}.bak-${STAMP}"
  chmod 600 "${ENV_FILE}.bak-${STAMP}"
  install -m 600 "$REPO_DIR/env.example" "$ENV_FILE"
  say "Existing env backed up and replaced: ${ENV_FILE}.bak-${STAMP}"
elif [[ ! -f "$ENV_FILE" ]]; then
  install -m 600 "$REPO_DIR/env.example" "$ENV_FILE"
  say "Created env template: $ENV_FILE"
else
  chmod 600 "$ENV_FILE"
  say "Existing env preserved: $ENV_FILE"
fi

if [[ "$ADD_ALIASES" -eq 1 ]]; then
  touch "$SHELL_RC"
  if ! grep -q 'UniFi AI Network Management aliases' "$SHELL_RC"; then
    cat >> "$SHELL_RC" <<ALIASES

# UniFi AI Network Management aliases
alias unifi-status='$BIN_DIR/unifi-api-status'
alias unifi-setup='$BIN_DIR/unifi-api-configure'
alias unifi-off='$BIN_DIR/unifi-api-disable'
alias unifi-on='$BIN_DIR/unifi-api-enable'
alias unifi-backup='$BIN_DIR/unifi-config-backup'
alias unifi-restore='$BIN_DIR/unifi-config-restore'
ALIASES
    say "Aliases added to $SHELL_RC"
  else
    say "Aliases already present in $SHELL_RC"
  fi
fi

python3 -m py_compile "$SKILL_DST/scripts/unifi_api.py" "$BIN_DIR/unifi-config-backup" "$BIN_DIR/unifi-config-restore"
rm -rf "$SKILL_DST/scripts/__pycache__" "$BIN_DIR/__pycache__" 2>/dev/null || true

say ""
say "Install complete."
say "Next steps:"
say "  1. source $SHELL_RC"
say "  2. unifi-setup"
say "  3. unifi-status"
say ""
say "For OpenClaw, run its skill check command if available, for example:"
say "  openclaw skills check --agent <agent-name>"
