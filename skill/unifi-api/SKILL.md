---
name: unifi-api
description: >
  UniFi and Ubiquiti network API operations for diagnostics, inventory, clients, APs,
  switches, gateways, sites, VLANs, Wi-Fi networks, guest access, firmware status,
  topology, alerts, and safe automation. Use this skill whenever the user mentions
  UniFi, Ubiquiti, UniFi OS, Network Application, Cloud Gateway, Dream Machine,
  UDM, UXG, Cloud Key, UniFi Express, access points, switches, cameras in a UniFi
  site, Wi-Fi clients, client reconnects, port PoE, VLANs, SSIDs, WAN health,
  site manager, or asks the agent to inspect, troubleshoot, or change the network.
---

# UniFi API Skill

This skill gives the agent a safe, detailed runbook for UniFi automation. It covers the official Ubiquiti Site Manager API, the official local UniFi Network Integration API, and the older private controller API that many community tools still use for actions not yet exposed in the official API.

Use deterministic API calls. Do not invent endpoint shapes. Prefer the helper script in `scripts/unifi_api.py` and consult the reference files only when the task needs details.

## Operating Principles

1. Prefer read-only discovery before changing anything.
2. Prefer official APIs over private legacy endpoints.
3. Never print, paste, or summarize API keys, session cookies, CSRF tokens, recovery keys, or passwords.
4. For network-impacting changes, capture the current state first and explain the exact target object before acting.
5. Avoid changes that could lock the user out unless they explicitly asked for that exact change and a rollback path exists.
6. Treat site IDs, device IDs, client IDs, MAC addresses, and network IDs as easy to confuse. Verify by name plus MAC/IP/model before writes.
7. If an endpoint returns 404, do not assume the resource is absent until the API surface and prefix have been checked.
8. When a task can be done with a read-only endpoint, do not use a command endpoint.

## API Surface Chooser

| Need | Preferred surface | Why |
| --- | --- | --- |
| List cloud consoles, sites, hosted UniFi deployments | Site Manager API | Official cloud API, API-key auth, fleet-level view |
| List local clients/devices/sites on one console | Local Network Integration API | Official local API for UniFi Network data |
| Routine status dashboards, health checks, inventory | Site Manager or Local Network Integration API | Stable and safer than private controller routes |
| Missing actions such as reconnect/block/legacy port actions | Legacy Network Application API | Private but often still needed; use carefully |
| Automation across multiple controllers | Site Manager for discovery, then local API per controller | Keeps global discovery separate from local action |

See `references/api-surfaces.md` for the differences and authentication models.

## Credential Discovery

Look for configured values in environment files or OpenClaw configuration, but do not reveal secrets in chat.

Put credentials in `~/.openclaw/unifi.env` with permissions `0600`. Common environment names this skill supports:

```bash
UNIFI_SITE_MANAGER_API_KEY=...
UNIFI_API_KEY=...                  # fallback API key for official APIs
UNIFI_NETWORK_BASE_URL=https://192.168.1.1
UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1
UNIFI_LEGACY_BASE_URL=https://192.168.1.1
UNIFI_USERNAME=...
UNIFI_PASSWORD=...
UNIFI_SITE=default
UNIFI_INSECURE_TLS=1               # use for self-signed local controllers only
```

The helper reads these automatically. If both `UNIFI_SITE_MANAGER_API_KEY` and `UNIFI_API_KEY` are present, Site Manager uses `UNIFI_SITE_MANAGER_API_KEY`.

## Helper Script

Run from the OpenClaw server:

```bash
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py --help
```

Quick checks:

```bash
# Show detected configuration without exposing secret values
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py env

# Site Manager fleet view
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py site-manager-get /sites
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py site-manager-get /hosts

# Official local Network Integration API
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites/<site_id>/devices
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites/<site_id>/clients

# Legacy private Network Application API
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py legacy-sites
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py legacy-clients --site default
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py legacy-devices --site default
```

The helper prints JSON. Pipe to `jq` for filtering when available.

The operational backup/restore tools are also part of this skill because they protect major UniFi changes:

```bash
unifi-backup    # create a secure timestamped backup before major changes or on demand
unifi-restore   # choose a restore point and dry-run/apply a restore
```

If aliases are not loaded in the agent shell, use the scripts directly:

```bash
~/.local/bin/unifi-config-backup
~/.local/bin/unifi-config-restore
```

Backup and restore are normal safety operations. Break-glass local access-control tooling remains owner-only and is intentionally not part of this skill workflow.

## Standard Workflow

1. Classify the request: read-only, low-impact write, high-impact write, backup, or restore.
2. Identify API surface: Site Manager, official local Network API, legacy, or backup/restore tooling.
3. Load only the reference page needed for the request.
4. Run `env` to confirm which credentials and base URLs exist. Do not display secret values.
5. Run a read-only call to find exact IDs and current state.
6. Before any major write, run `unifi-backup` and wait for a successful timestamped backup path.
7. For writes, build a short change plan with the target object, intended endpoint, and rollback.
8. Execute the smallest possible change.
9. Verify state after the change.
10. Report what changed, what was verified, the backup path if one was created, and any residual risk.

## Backup And Restore Tasks

### On-demand backup

If the user asks to back up the UniFi configuration, run:

```bash
unifi-backup
```

If aliases are not loaded:

```bash
~/.local/bin/unifi-config-backup
```

Report the created backup path. Do not paste backup contents into chat because backups may contain sensitive network configuration.

### Backup before major changes

Run `unifi-backup` before changes involving:

- VLANs, networks, DHCP, DNS, WAN, routing, firewall, or port forwards
- SSIDs, Wi-Fi security, guest/captive portal, or RADIUS profiles
- switch port profiles, PoE actions, or port configuration
- firmware upgrades, provisioning, adoption/forget/delete, gateway/AP/switch reboot
- any batch change across multiple devices or sites

For small reversible client actions such as reconnecting one verified Wi-Fi client, a backup is optional unless the user asks for it.

### Restore workflow

Restore is potentially disruptive. Only start a restore when the user explicitly asks to restore from backup or rollback UniFi configuration.

If multiple restore points exist, list them newest-first and ask the user which date/time they want to restore to. Use the folder names as the source of truth:

```bash
find ~/.openclaw/unifi-backups -maxdepth 1 -type d -name 'backup-*' -printf '%f\n' | sort -r
```

After the user chooses a restore point, run a dry-run first:

```bash
unifi-restore --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS
```

If aliases are not loaded:

```bash
~/.local/bin/unifi-config-restore --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS
```

Summarize the dry-run plan: selected backup, site, collections, objects that would update/create, extra current objects, and any errors. Then ask for explicit confirmation before applying.

Only after explicit confirmation, apply the restore:

```bash
unifi-restore --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS --apply --confirm 'RESTORE UNIFI CONFIG'
```

Do not use `--delete-extra` unless the user explicitly asks for a full rollback that deletes current objects not present in the backup. If the user asks for full rollback, explain the risk, run the dry-run with the chosen backup first, and ask for explicit confirmation before using `--delete-extra`.

### Restore selection rule

When multiple backup dates exist, do not guess. Present a concise list like:

```text
1. backup-20260509-193200
2. backup-20260508-221015
3. backup-20260507-101044
```

Ask: "Which backup date/time should I restore from?"

## Read-Only Tasks

### Fleet inventory

Use Site Manager first:

```bash
python3 scripts/unifi_api.py site-manager-get /hosts
python3 scripts/unifi_api.py site-manager-get /sites
```

Then use the local Network API for each site if more detail is needed:

```bash
python3 scripts/unifi_api.py network-get /sites/<site_id>/devices
python3 scripts/unifi_api.py network-get /sites/<site_id>/clients
```

### Find a client

Search by MAC, IP, hostname, username, or OUI. Prefer exact MAC when possible.

```bash
python3 scripts/unifi_api.py legacy-clients --site default | jq '.data[] | select(.mac=="aa:bb:cc:dd:ee:ff")'
```

For official local API, use the site-specific clients route and inspect the schema returned by the controller version.

### AP and switch health

Read devices, then summarize:

- Model, name, MAC, IP, site
- State/adoption status
- Firmware version and update availability
- Uplink and parent device
- PoE budget and port state for switches
- Channel, transmit power, client count for APs
- Last seen and uptime

### Wi-Fi and VLAN audit

Use read-only network/WLAN endpoints. If official endpoints do not expose enough detail, use legacy `/rest/wlanconf` and `/rest/networkconf` cautiously.

Summarize:

- SSID name, enabled state, security mode, VLAN/network mapping
- Hidden SSIDs, guest policies, captive portal policies
- Networks/VLAN IDs, DHCP mode/ranges, DNS settings
- Any obvious drift from requested intent

## Write Tasks

Writes can break connectivity. Use exact IDs and verify before acting.

Low-impact examples:

- Reconnect one Wi-Fi client
- Authorize one guest client
- Rename a client alias
- Trigger a non-critical refresh/sync operation

High-impact examples:

- Reboot gateway/AP/switch
- Change VLAN, DHCP, DNS, firewall, or WAN settings
- Modify SSIDs or security settings
- Block/unblock a client if the user is currently depending on it
- PoE cycle a port
- Firmware upgrades
- Delete/adopt/forget devices

For high-impact actions, make sure the user has explicitly asked for the action. If the request is ambiguous, stop and ask one concise clarification.

## Legacy Action Examples

Legacy endpoints vary by UniFi Network version. Use only when official APIs are insufficient. See `references/endpoints.md` for endpoint notes.

Reconnect one station:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"kick-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

Block one station:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"block-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

Unblock one station:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"unblock-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

## Response Style

When reporting to the user:

- Say which API surface was used.
- Include object names and non-secret identifiers needed for human verification, such as MAC suffixes or device names.
- Do not paste full API responses unless asked.
- For failures, include HTTP status, endpoint path, and likely next diagnostic.
- For writes, state the before/after verification.

## When To Read References

- `references/api-surfaces.md`: authentication, cloud vs local, env var setup, choosing the API.
- `references/endpoints.md`: endpoint catalog and examples.
- `references/troubleshooting.md`: common status codes, TLS, 404 prefix mistakes, rate limits, stale sessions.
- `references/task-recipes.md`: repeatable playbooks for health checks, client troubleshooting, firmware audits, SSID/VLAN audits, guest access, and port work.

## Official Documentation Links

- Ubiquiti Help: Getting Started with UniFi API: https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-UniFi-API
- UniFi Site Manager API docs: https://developer.ui.com/site-manager-api/
- Ubiquiti Developer portal: https://developer.ui.com/

The official docs are the source of truth. This skill is a practical runbook and helper around those APIs, with legacy endpoints clearly marked as private/compatibility-only.
