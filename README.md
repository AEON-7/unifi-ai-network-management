# UniFi AI Network Management

[![Buy me a coffee on LotusMake](https://lotusmake.com/badges/coffee-light.v2.svg)](https://lotusmake.com/support) [![Subscribe on lotusmake.com](https://lotusmake.com/badges/subscribe-light.v2.svg)](https://lotusmake.com/support?mode=tiers)

A safety-first UniFi API skill and tooling package for AI agents that can inspect, troubleshoot, document, and carefully optimize UniFi networks.

This package gives an AI agent a practical UniFi runbook, a deterministic API helper, owner-only shell tooling, secure `.env` handling, backup/restore commands, and break-glass controls for revoking local access quickly.

Repository name: `unifi-ai-network-management`.

This repo is designed to be installed as a complete package: the skill folder is copied into the agent skills directory, helper scripts are installed into the user's local bin directory, and credentials are stored in a private env file outside the repository.

## What This Does

This repository packages three things:

| Component | Location | Purpose |
| --- | --- | --- |
| Agent skill | `skill/unifi-api/` | `SKILL.md` package for OpenClaw (`~/.openclaw/workspace/skills/unifi-api`) or Hermes (`~/.hermes/skills/unifi-api`) with UniFi API operations, safety tiers, endpoint selection, and troubleshooting. |
| API helper | `skill/unifi-api/scripts/unifi_api.py` | Zero-dependency Python helper for Site Manager, official local Network API, and legacy controller API. |
| Operational scripts | `scripts/` | Setup, status, break-glass disable/enable, secure backup, and dry-run/apply restore tooling. |

The goal is not to let an AI randomly mutate your network. The goal is to give a trusted local agent enough structure to:

- inventory sites, controllers, devices, clients, SSIDs, VLANs, and firmware state
- diagnose Wi-Fi and client issues from real controller data
- summarize health and configuration drift
- identify risky states before they become outages
- prepare and verify changes with backups and rollback paths
- act on explicit, narrow instructions when write access is intentionally granted

## Supported UniFi API Surfaces

UniFi has multiple APIs. This package deliberately separates them instead of pretending there is one universal endpoint.

| Surface | Base | Auth | Best for |
| --- | --- | --- | --- |
| Site Manager API | `https://api.ui.com/v1` | `X-API-Key` | Cloud/fleet/site/host overview across UniFi sites. |
| Local Network Integration API | `https://<controller>/proxy/network/integration/v1` | `X-API-Key` | Official local UniFi Network data and supported actions. |
| Legacy private Network Application API | `https://<controller>/api/...` or `/proxy/network/api/...` | username/password session cookie | Compatibility actions not yet exposed by the official API. Use sparingly. |

Official documentation:

- Ubiquiti: Getting Started with the Official UniFi API: https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-UniFi-API
- UniFi Site Manager API: https://developer.ui.com/site-manager-api/
- Ubiquiti Developer portal: https://developer.ui.com/

Ubiquiti states that localized Network API documentation is available inside UniFi Network at **Settings > Control Plane > Integrations**. Always prefer the docs from your deployed controller version when route details differ.

## Quick Start

Clone the repo on the machine where your agent or gateway runs.

For OpenClaw:

```bash
git clone https://github.com/AEON-7/unifi-ai-network-management.git
cd unifi-ai-network-management
./setup.sh --target openclaw
source ~/.bashrc
unifi-setup-openclaw
unifi-status-openclaw
```

For Hermes Agent:

```bash
git clone https://github.com/AEON-7/unifi-ai-network-management.git
cd unifi-ai-network-management
./setup.sh --target hermes
source ~/.bashrc
unifi-setup-hermes
unifi-status-hermes
hermes doctor
```

If your shell already had an older `unifi-*` alias block, open a new shell or run `source ~/.bashrc` after setup. The installer is safe to re-run; it backs up an existing skill directory before replacing it and preserves the existing target env file unless `--force-env` is used.

`setup.sh` installs:

```text
# OpenClaw target
~/.openclaw/workspace/skills/unifi-api/
~/.openclaw/unifi.env

# Hermes target
~/.hermes/skills/unifi-api/
~/.hermes/unifi.env

# Both targets
~/.local/bin/unifi-api-status
~/.local/bin/unifi-api-configure
~/.local/bin/unifi-api-disable
~/.local/bin/unifi-api-enable
~/.local/bin/unifi-config-backup
~/.local/bin/unifi-config-restore
```

It installs explicit target commands into `~/.local/bin` and ensures that directory is on your shell `PATH`:

```bash
# OpenClaw target
unifi-status-openclaw
unifi-setup-openclaw
unifi-off-openclaw
unifi-on-openclaw
unifi-backup-openclaw
unifi-restore-openclaw

# Hermes target
unifi-status-hermes
unifi-setup-hermes
unifi-off-hermes
unifi-on-hermes
unifi-backup-hermes
unifi-restore-hermes
```

Use `./setup.sh --target hermes` for Hermes Agent, `./setup.sh --target openclaw` for OpenClaw, `./setup.sh --no-aliases` if you want files installed without modifying your shell rc/PATH, and `./setup.sh --force-env` only if you intentionally want to replace the existing env file with `env.example` after creating a timestamped backup.

If you do not use OpenClaw or Hermes, you can still use the helper script and docs. Install the skill folder wherever your agent framework expects tool instructions.

### What `setup.sh` Copies

The installer copies the canonical skill directory from:

```text
./skill/unifi-api/
```

to the selected agent skill path:

```text
~/.openclaw/workspace/skills/unifi-api/  # OpenClaw
~/.hermes/skills/unifi-api/              # Hermes
```

It preserves this layout because the `SKILL.md` references `references/` and `scripts/unifi_api.py` by relative path:

```text
unifi-api/
|-- SKILL.md
|-- scripts/unifi_api.py
|-- references/
`-- agents/openai.yaml
```

For other agent frameworks, copy the entire `skill/unifi-api` directory into that framework's skills/tools directory. Do not copy only `SKILL.md`; the helper script and reference files are part of the package.

See `AGENTS.md` for detailed agent-framework installation and behavior guidance.

### Hermes Agent Install Notes

Hermes Agent uses `SKILL.md` skills under `~/.hermes/skills/`. The Hermes target installs this package as:

```text
~/.hermes/skills/unifi-api/
|-- SKILL.md
|-- scripts/unifi_api.py
|-- references/
`-- agents/openai.yaml
```

The private credential file is stored separately at:

```text
~/.hermes/unifi.env
```

After setup, open a new shell or run `source ~/.bashrc`, then run `unifi-setup-hermes`. Start a new Hermes session so it reloads the skill catalog. If Hermes is installed, `hermes doctor` should still pass.


This repository intentionally does **not** commit a real `.env` file. The common and safer convention is:

1. Commit `env.example` as a template.
2. Copy it to a private runtime env file.
3. Keep real `.env` / `unifi.env` files ignored by git.

`setup.sh` handles this automatically by copying `env.example` to the target-private env path (`~/.openclaw/unifi.env` or `~/.hermes/unifi.env`) when one does not already exist.

## Environment File

The private env file lives at `~/.openclaw/unifi.env` for OpenClaw or `~/.hermes/unifi.env` for Hermes.

It should be readable only by your user:

```bash
chmod 600 ~/.openclaw/unifi.env  # OpenClaw
chmod 600 ~/.hermes/unifi.env    # Hermes
```

Template:

```bash
# Site Manager cloud API
UNIFI_SITE_MANAGER_API_KEY=
UNIFI_SITE_MANAGER_BASE_URL=https://api.ui.com/v1

# Local UniFi Network API
UNIFI_NETWORK_BASE_URL=https://192.168.1.1
UNIFI_NETWORK_API_KEY=
UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1
UNIFI_INSECURE_TLS=1

# Legacy fallback, only when official API cannot do the job
UNIFI_LEGACY_BASE_URL=https://192.168.1.1
UNIFI_USERNAME=
UNIFI_PASSWORD=
UNIFI_SITE=default
```

Use the interactive setup tool instead of editing by hand:

```bash
unifi-setup-openclaw  # OpenClaw
unifi-setup-hermes    # Hermes
```

It hides secret input, confirms keys/passwords, backs up the old env file, writes `0600`, and can restart OpenClaw if installed as a user service. Hermes users should start a fresh Hermes session after setup so the skill catalog reloads.

## Owner Commands

| Command | Purpose |
| --- | --- |
| `unifi-status-openclaw` / `unifi-status-hermes` | Show local access state and redacted env status for a specific target. |
| `unifi-setup-openclaw` / `unifi-setup-hermes` | Interactive setup/update for API keys and controller URLs for a specific target. |
| `unifi-off-openclaw` / `unifi-off-hermes` | Local break-glass disable. Renames the target `unifi.env` to `unifi.env.disabled` and restarts the gateway if present. |
| `unifi-on-openclaw` / `unifi-on-hermes` | Re-enable local UniFi access by restoring the target `unifi.env`. |
| `unifi-backup-openclaw` / `unifi-backup-hermes` | Create a secure timestamped config snapshot before major changes. |
| `unifi-restore-openclaw` / `unifi-restore-hermes` | Choose an available backup newest-first and run a dry-run restore plan. |

Setup/status/break-glass commands are for the owner/operator. Backup and restore are included in the AI skill because they are part of safe change management; restore still requires explicit user selection and confirmation.

## Break-Glass Procedure

If a key may be compromised or you want to immediately stop the agent from using UniFi:

```bash
unifi-off-openclaw
```

This is a local kill switch. It does not revoke the real key in UniFi.

Then revoke the key in the UniFi UI:

1. Open your UDM Pro / Cloud Gateway web console.
2. Open **Network**.
3. Go to **Settings > Control Plane > Integrations**.
4. Find the API key/integration used by the agent.
5. Delete/revoke/remove it.
6. If legacy username/password was used, disable that service user, rotate the password, or remove its UniFi permissions.

After issuing a new key:

```bash
unifi-setup-openclaw
unifi-on-openclaw
unifi-status-openclaw
```

## Getting a Local API Key on UDM Pro

Use the local Network API key for device/client/site operations on your own console.

1. Browse to your UDM Pro or Cloud Gateway:

   ```text
   https://<UDM-Pro-IP-or-hostname>
   ```

2. Sign in with an account allowed to manage integrations.
3. Open the **Network** application.
4. Open **Settings**.
5. Open **Control Plane**.
6. Open **Integrations**.
7. Generate/create an API key.
8. Copy it once and store it with the setup alias for your target:

   ```bash
   unifi-setup-openclaw  # OpenClaw
   unifi-setup-hermes    # Hermes
   ```

9. Verify:

   ```bash
   unifi-status-openclaw
   # OpenClaw
   python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites

   # Hermes
   python3 ~/.hermes/skills/unifi-api/scripts/unifi_api.py network-get /sites
   ```

Default local prefix:

```bash
UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1
```

If every local official endpoint returns 404 while host/auth are correct, try the pluralized prefix some controller/docs revisions use:

```bash
UNIFI_NETWORK_PREFIX=/proxy/network/integrations/v1
```

## Operational Security Model

Handing an AI API access to your network is powerful. Treat it like giving a junior network admin a constrained service account and a very detailed runbook.

Minimum safety baseline:

1. Use a dedicated UniFi service/integration key.
2. Prefer read-only or least-privilege access when UniFi exposes it.
3. Keep write-capable keys out of chat history.
4. Store keys only in the selected private env file, `~/.openclaw/unifi.env` for OpenClaw or `~/.hermes/unifi.env` for Hermes, with mode `0600`.
5. Use `unifi-backup-openclaw` or `unifi-backup-hermes` before major changes, matching the agent target.
6. Use official APIs before legacy private endpoints.
7. Require exact object verification before writes: site, name, MAC/IP/model/id.
8. Avoid changes that could sever the current management path unless you have a rollback path.
9. Use `unifi-off` immediately if anything looks wrong.
10. Revoke real keys in UniFi after any suspected compromise.

Recommended permission split:

| Key/account | Purpose | Access level |
| --- | --- | --- |
| Read-only API key | Daily monitoring, inventory, diagnostics | Read-only if available |
| Write-capable API key | Explicit maintenance windows and targeted changes | Narrowest available write scope |
| Legacy service account | Compatibility fallback only | Disabled unless needed |

Never paste API keys, cookies, CSRF tokens, passwords, restore logs, or full raw config dumps into chat.

## Backup and Restore

Create backup:

```bash
unifi-backup-openclaw  # OpenClaw
unifi-backup-hermes    # Hermes
```

Backups are stored under the selected agent home, for example:

```bash
~/.openclaw/unifi-backups/   # OpenClaw target
~/.hermes/unifi-backups/     # Hermes target
```

Example:

```text
~/.openclaw/unifi-backups/backup-20260509-192255/
```

Backups use `0700` directories and `0600` files. They may contain sensitive network data including SSIDs, firewall rules, VLANs, port profiles, and possibly Wi-Fi credentials.

Dry-run restore:

```bash
unifi-restore-openclaw --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS
unifi-restore-hermes --backup ~/.hermes/unifi-backups/backup-YYYYMMDD-HHMMSS
```

Apply restore after explicit confirmation:

```bash
unifi-restore-openclaw --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS --apply
unifi-restore-hermes --backup ~/.hermes/unifi-backups/backup-YYYYMMDD-HHMMSS --apply
```

For non-interactive agent execution after explicit user confirmation, the same confirmation phrase can be supplied as a flag:

```bash
unifi-restore-openclaw --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS --apply --confirm 'RESTORE UNIFI CONFIG'
unifi-restore-hermes --backup ~/.hermes/unifi-backups/backup-YYYYMMDD-HHMMSS --apply --confirm 'RESTORE UNIFI CONFIG'
```

The restore tool requires this exact confirmation phrase before applying:

```text
RESTORE UNIFI CONFIG
```

It will not delete current objects that are absent from the backup unless explicitly requested:

```bash
unifi-restore-openclaw --apply --delete-extra
unifi-restore-hermes --apply --delete-extra
```

Use `--delete-extra` only for intentional rollback to an older full state.

## Endpoint Breakdown

The helper exposes generic commands so the agent can call exact endpoints without guessing curl syntax.

### Site Manager API

Base:

```text
https://api.ui.com/v1
```

| Command | Endpoint | What it does | AI use cases |
| --- | --- | --- | --- |
| `site-manager-get /hosts` | `GET /hosts` | Lists UniFi OS hosts/consoles visible to the API key. | Fleet health, find the right console, identify offline hosts. |
| `site-manager-get /sites` | `GET /sites` | Lists sites visible to the key. | Site inventory, mapping site names to controllers. |
| `site-manager-get /devices` | `GET /devices` | Lists cloud-visible devices where available. | Global firmware/update/online summary. |
| `site-manager-post <path>` | `POST <path>` | Generic cloud write/action route, if supported by the official docs. | Rare; use only with docs-confirmed path and explicit intent. |

### Official Local Network API

Base pattern:

```text
https://<controller>/proxy/network/integration/v1
```

| Command | Endpoint pattern | What it does | AI use cases |
| --- | --- | --- | --- |
| `network-get /sites` | `GET /sites` | Lists local Network sites. | Select exact site id before drilling into clients/devices. |
| `network-get /sites/<site_id>/devices` | `GET /sites/{site_id}/devices` | Lists UniFi Network devices. | AP/switch/gateway health, firmware, adoption state, uplink checks. |
| `network-get /sites/<site_id>/clients` | `GET /sites/{site_id}/clients` | Lists clients. | Client diagnostics, unknown device review, Wi-Fi quality checks. |
| `network-post <path>` | `POST <path>` | Generic official local action route. | Guest authorization or supported actions from local docs. Requires explicit write acknowledgement. |

### Legacy Private Network Application API

Use only when the official APIs do not expose the needed function.

| Command | Endpoint pattern | What it does | AI use cases |
| --- | --- | --- | --- |
| `legacy-sites` | `GET /api/self/sites` or `/proxy/network/api/self/sites` | Lists legacy sites. | Find legacy site names such as `default`. |
| `legacy-clients --site default` | `GET /api/s/<site>/stat/sta` | Lists clients. | Deep client stats, RSSI, rates, AP association, legacy fields. |
| `legacy-devices --site default` | `GET /api/s/<site>/stat/device` | Lists devices. | Detailed AP/switch/gateway stats and port/radio tables. |
| `legacy-get /api/s/<site>/rest/wlanconf` | WLAN config read | Reads SSID/Wi-Fi config. | SSID/security/VLAN mapping audit. |
| `legacy-get /api/s/<site>/rest/networkconf` | Network config read | Reads networks/VLANs/DHCP config. | VLAN/DHCP/DNS audit. |
| `legacy-get /api/s/<site>/rest/firewallrule` | Firewall rules read | Reads firewall policy. | Security posture review and drift detection. |
| `legacy-get /api/s/<site>/rest/firewallgroup` | Firewall groups read | Reads address/port groups. | Explain firewall rule targets and identify stale groups. |
| `legacy-get /api/s/<site>/rest/portconf` | Port profiles read | Reads switch port profiles. | Validate VLAN/trunk/access profiles. |
| `legacy-post /api/s/<site>/cmd/stamgr` | Station manager commands | Reconnect/block/unblock a client. | Targeted response to a confirmed rogue or misbehaving client. |
| `legacy-post /api/s/<site>/cmd/devmgr` | Device manager commands | Device actions such as provision/restart where supported. | Maintenance only; high-impact confirmation required. |

See `docs/API-ENDPOINTS.md` and `skill/unifi-api/references/endpoints.md` for more detail.

## AI Use Cases

### Reliability and efficiency

- Find clients with weak signal, low data rates, excessive roaming, or bad AP association.
- Identify overloaded APs or imbalanced client distribution.
- Audit channel width, band use, SSID-to-VLAN mapping, and firmware update state.
- Detect offline or repeatedly reconnecting devices.
- Explain which switch port or AP a client is connected through.
- Build a maintenance plan that upgrades devices in safe batches instead of all at once.

### Security and threat response

- Identify unknown clients by MAC/IP/hostname/vendor and recent activity.
- Compare connected clients against an expected inventory.
- Detect risky firewall or guest network drift.
- Summarize security events and correlate them with clients, ports, APs, and VLANs.
- Recommend containment steps before action.
- With explicit permission and exact target verification, block or reconnect a suspicious client.
- Produce an incident record: what was observed, what changed, how it was verified, and rollback.

### Documentation and operations

- Generate a human-readable network map from controller data.
- Export a site inventory report.
- Maintain a change log with before/after state.
- Verify that a requested change actually took effect.
- Prepare rollback plans from backups.

## Safe Write Workflow For Agents

The skill instructs the agent to follow this pattern:

1. Read current state.
2. Identify exact site and object.
3. Capture backup for major changes.
4. Explain intended endpoint/action.
5. Execute the smallest possible write.
6. Verify state after the write.
7. Report before/after and rollback.

High-impact actions require explicit user intent:

- gateway/AP/switch reboot
- firmware upgrades
- VLAN/DHCP/DNS/firewall changes
- SSID/security changes
- PoE cycling
- delete/adopt/forget/factory reset
- block/unblock clients when target identity is uncertain

## Repository Layout

```text
.
|-- README.md
|-- setup.sh
|-- env.example
|-- AGENTS.md                 # installation/behavior notes for agent frameworks
|-- scripts/
|   |-- unifi-api-status
|   |-- unifi-api-configure
|   |-- unifi-api-disable
|   |-- unifi-api-enable
|   |-- unifi-config-backup
|   `-- unifi-config-restore
|-- skill/unifi-api/
|   |-- SKILL.md
|   |-- scripts/unifi_api.py
|   |-- references/
|   `-- agents/openai.yaml
`-- docs/
    |-- API-ENDPOINTS.md
    |-- OPSEC.md
    |-- USE-CASES.md
    `-- LOCAL_OWNER_RUNBOOK.md
```

## Requirements

- Linux or WSL-style shell environment
- Python 3.10+
- Bash
- OpenClaw or Hermes if you want automatic skill installation into their default skill directories
- UniFi Network version with API integrations for official local API access

The API helper intentionally uses Python standard library only.

## Support the work

AEON-7 models, drafters and tools are built and trained independently, on my own hardware. If they're useful to you, please consider supporting development.

Patreon wrongfully shut down our account without notice and never responded to our appeals, so we built something even better. You can now support the work on **LotusMake**: buy us a Lotus Tea, fund GPU hours, back a project you want to see done, or subscribe for early and full access to publications while supporting what we build. You can become a creator there too: join, apply to become a creator, and get paid for the work you do in public.

[![Buy me a coffee on LotusMake](https://lotusmake.com/badges/coffee-light.v2.svg)](https://lotusmake.com/support) [![Subscribe on lotusmake.com](https://lotusmake.com/badges/subscribe-light.v2.svg)](https://lotusmake.com/support?mode=tiers)

**[AEON FORGE on LotusMake → lotusmake.com/c/aeon-forge](https://lotusmake.com/c/aeon-forge)** · **[Subscribe for early and full access](https://lotusmake.com/support?mode=tiers&from=%2Fc%2Faeon-forge)**

Milestones unlock bigger work: reaching **500 paid supporters** will fund fine-tuning larger models and bigger project releases. Subscribers also get early access to new releases, such as the [AEON DFlash2 drafter](https://huggingface.co/AEON-7/AEON-DFlash2-Qwen3.8-27B).

## License

MIT. Use at your own risk. Network automation can cause outages; read the plan before applying changes.
