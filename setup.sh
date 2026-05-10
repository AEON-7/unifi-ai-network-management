#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
STAMP="$(date +%Y%m%d-%H%M%S)"
SHELL_RC="${SHELL_RC:-$HOME/.bashrc}"
TARGET="openclaw"

say() { printf '%s\n' "$*"; }

usage() {
  cat <<USAGE
Usage: ./setup.sh [--target openclaw|hermes] [--no-aliases] [--force-env]

Targets:
  openclaw  Skill -> ~/.openclaw/workspace/skills/unifi-api, env -> ~/.openclaw/unifi.env
  hermes    Skill -> ~/.hermes/skills/unifi-api, env -> ~/.hermes/unifi.env

Options:
  --target <name>  Install for openclaw or hermes. Default: openclaw.
  --no-aliases    Install files but do not modify shell rc.
  --force-env     Replace existing env file after backing it up.
USAGE
}

ADD_ALIASES=1
FORCE_ENV=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --target=*)
      TARGET="${1#--target=}"
      shift
      ;;
    --no-aliases) ADD_ALIASES=0; shift ;;
    --force-env) FORCE_ENV=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

case "$TARGET" in
  openclaw)
    AGENT_HOME="${OPENCLAW_DIR:-$HOME/.openclaw}"
    SKILL_DST="$AGENT_HOME/workspace/skills/unifi-api"
    ;;
  hermes)
    AGENT_HOME="${HERMES_HOME:-$HOME/.hermes}"
    SKILL_DST="$AGENT_HOME/skills/unifi-api"
    ;;
  *) echo "Unsupported target: $TARGET" >&2; usage; exit 2 ;;
esac
ENV_FILE="$AGENT_HOME/unifi.env"

if [[ ! -d "$REPO_DIR/skill/unifi-api" ]]; then
  echo "Missing skill/unifi-api. Run setup from the repo root." >&2
  exit 1
fi

mkdir -p "$(dirname "$SKILL_DST")" "$BIN_DIR" "$AGENT_HOME"
chmod 700 "$AGENT_HOME" 2>/dev/null || true

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
  python3 - "$SHELL_RC" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8') if p.exists() else ''
start = '# UniFi AI Network Management aliases'
end = '# End UniFi AI Network Management aliases'
while start in text and end in text:
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    text = before.rstrip() + '\n' + after.lstrip('\n')
p.write_text(text.rstrip() + '\n', encoding='utf-8')
PY
  cat >> "$SHELL_RC" <<ALIASES

# UniFi AI Network Management aliases
alias unifi-status='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-api-status"'
alias unifi-setup='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-api-configure"'
alias unifi-off='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-api-disable"'
alias unifi-on='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-api-enable"'
alias unifi-backup='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-config-backup"'
alias unifi-restore='UNIFI_AGENT_HOME="$AGENT_HOME" UNIFI_SKILL_DIR="$SKILL_DST" UNIFI_ENV_FILE="$ENV_FILE" "$BIN_DIR/unifi-config-restore"'
# End UniFi AI Network Management aliases
ALIASES
  say "Aliases written to $SHELL_RC for target: $TARGET"
fi

python3 -m py_compile "$SKILL_DST/scripts/unifi_api.py" "$BIN_DIR/unifi-config-backup" "$BIN_DIR/unifi-config-restore"
rm -rf "$SKILL_DST/scripts/__pycache__" "$BIN_DIR/__pycache__" 2>/dev/null || true

say ""
say "Install complete for target: $TARGET"
say "Skill: $SKILL_DST"
say "Env:   $ENV_FILE"
say "Next steps:"
say "  1. source $SHELL_RC"
say "  2. unifi-setup"
say "  3. unifi-status"
say ""
if [[ "$TARGET" == "openclaw" ]]; then
  say "For OpenClaw, run its skill check command if available, for example:"
  say "  openclaw skills check --agent <agent-name>"
else
  say "For Hermes, start a new Hermes session or run its diagnostics, for example:"
  say "  hermes doctor"
fi
