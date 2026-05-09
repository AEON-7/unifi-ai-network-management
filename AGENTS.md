# Agent Integration Guide

This repository packages a UniFi API skill plus owner-operated setup and safety tooling. It is written for OpenClaw-style skills, but the same directory can be used by any agent framework that supports filesystem skills or tool instructions.

## Canonical Skill Directory

The skill is contained in:

```text
skill/unifi-api/
```

Install it as a directory, not as a single markdown file. The directory must keep this shape:

```text
unifi-api/
??? SKILL.md
??? scripts/unifi_api.py
??? references/api-surfaces.md
??? references/endpoints.md
??? references/task-recipes.md
??? references/troubleshooting.md
??? agents/openai.yaml
```

The helper script is part of the skill contract. The agent should prefer deterministic helper calls over hand-written curl commands.

## OpenClaw Install Path

Default OpenClaw path:

```text
~/.openclaw/workspace/skills/unifi-api/
```

The provided installer does this automatically:

```bash
./setup.sh
```

Manual install:

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -a skill/unifi-api ~/.openclaw/workspace/skills/unifi-api
chmod -R u+rwX,go-rwx ~/.openclaw/workspace/skills/unifi-api
python3 -m py_compile ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py
```

Then run your agent framework's skill refresh/check command, for example:

```bash
openclaw skills check --agent <agent-name>
```

## Other Agent Frameworks

For non-OpenClaw frameworks:

1. Copy `skill/unifi-api/` into the framework's skill/tool directory.
2. Make sure the framework can read `SKILL.md`.
3. Preserve `references/` and `scripts/` next to `SKILL.md`.
4. Expose Python 3 to the agent runtime.
5. Set credentials in a private env file or process environment.
6. Instruct the agent to load `SKILL.md` when the user mentions UniFi, Ubiquiti, UDM, Network Application, clients, APs, switches, VLANs, SSIDs, firewall rules, or network diagnostics.

## Credential File

Default env location:

```text
~/.openclaw/unifi.env
```

The helper also checks:

```text
~/.openclaw/.env
~/.openclaw/openclaw.env
~/.openclaw/workspace/.env
<skill-dir>/.env
```

Use `env.example` as the template. Never commit a real env file.

## Operational Commands And Agent Boundaries

The repository installs aliases such as:

```bash
unifi-setup
unifi-status
unifi-off
unifi-on
unifi-backup
unifi-restore
```

`unifi-setup`, `unifi-status`, and break-glass local access-control commands are owner/operator commands.

`unifi-backup` and `unifi-restore` are part of safe network change management and are included in `SKILL.md`. Agents may run backups on demand or before major changes. Agents may run restore dry-runs after the user asks for rollback. Agents must ask which backup date/time to use when multiple restore points exist, summarize the dry-run, and apply only after explicit user confirmation.

## Agent Behavior Contract

A safe UniFi agent should:

1. Prefer read-only API calls first.
2. Prefer official APIs over legacy private endpoints.
3. Use exact object identity before writes: site, name, MAC/IP/model/id.
4. Avoid broad changes based on vague requests.
5. Run `unifi-backup` before major changes and report the backup path.
6. For restore requests, list backup date/time folders and ask which restore point to use when multiple exist.
7. Run restore dry-run first, then apply only after explicit confirmation.
8. Explain intended endpoint/action before high-impact writes.
9. Verify after every write.
10. Never reveal API keys, passwords, cookies, CSRF tokens, or raw sensitive config.
11. Report failures with endpoint path and HTTP status, not secrets.

## Helper Script Examples

From an installed OpenClaw skill:

```bash
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py env
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py site-manager-get /sites
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py legacy-clients --site default
```

Write helpers require an explicit acknowledgement flag:

```bash
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"kick-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

## Validation Checklist

After installation:

```bash
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py env
python3 -m py_compile ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py
```

If OpenClaw is installed:

```bash
openclaw skills check --agent <agent-name>
```

Expected result: the skill named `unifi-api` is eligible and visible to the intended agent.
