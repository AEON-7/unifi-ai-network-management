# UniFi Owner Runbook

This folder is owner-facing documentation for Albert. It documents the local UniFi helper aliases on the OpenClaw server and the UDM Pro web-console steps for API key creation/revocation.

These commands are intentionally not part of Celina's UniFi skill instructions. They are for manual shell use by Albert.

## Quick Command List

After logging into the OpenClaw server as `albert`, run:

```bash
source ~/.bashrc   # only needed if the current shell does not know the aliases yet
```

| Alias | Script | Purpose |
| --- | --- | --- |
| `unifi-status` | `~/.local/bin/unifi-api-status` | Show whether UniFi API access is locally enabled and print redacted env status. |
| `unifi-setup` | `~/.local/bin/unifi-api-configure` | Interactive prompt to create/update the UniFi env file. Secrets are typed hidden and confirmed. |
| `unifi-off` | `~/.local/bin/unifi-api-disable` | Break-glass local kill switch. Renames `unifi.env` to `unifi.env.disabled` and restarts OpenClaw. |
| `unifi-on` | `~/.local/bin/unifi-api-enable` | Restores `unifi.env` from `unifi.env.disabled` and restarts OpenClaw. |
| `unifi-backup` | `~/.local/bin/unifi-config-backup` | Create a secure timestamped UniFi config snapshot before major changes. |
| `unifi-restore` | `~/.local/bin/unifi-config-restore` | Interactively inspect/restore an available backup sorted newest-first. Defaults to dry-run. |

## Important Paths

| Path | Purpose |
| --- | --- |
| `~/.openclaw/unifi.env` | Active UniFi API env file loaded by the helper. Mode should be `0600`. |
| `~/.openclaw/unifi.env.disabled` | Disabled copy used by `unifi-off`. |
| `~/.openclaw/unifi-backups/` | Secure backup root. Directory mode should be `0700`. |
| `~/.openclaw/unifi-backups/latest` | Symlink to the newest backup, when symlink creation succeeds. |
| `~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS/` | One timestamped backup snapshot. |
| `~/.openclaw/unifi-backups/restore-logs/` | Restore dry-run/apply logs. |
| `~/.openclaw/workspace/skills/unifi-api/` | Celina's UniFi skill and helper code. |

## API Env File

The env file supports these fields:

```bash
# Official Site Manager cloud API
UNIFI_SITE_MANAGER_API_KEY=...
UNIFI_SITE_MANAGER_BASE_URL=https://api.ui.com/v1

# Official local UniFi Network Integration API on the UDM Pro / UniFi Network app
UNIFI_NETWORK_BASE_URL=https://192.168.1.1
UNIFI_NETWORK_API_KEY=...
UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1
UNIFI_INSECURE_TLS=1

# Legacy private Network Application fallback, only if API-key routes cannot do the job
UNIFI_LEGACY_BASE_URL=https://192.168.1.1
UNIFI_USERNAME=...
UNIFI_PASSWORD=...
UNIFI_SITE=default
```

Prefer `unifi-setup` to edit this file because it hides secret input, creates backups, writes mode `0600`, and can restart the OpenClaw gateway.

Manual permission repair:

```bash
chmod 600 ~/.openclaw/unifi.env
```

## Break-Glass Disable / Restore

Fast local disable:

```bash
unifi-off
```

This renames the active env file so OpenClaw cannot load UniFi API credentials, then restarts `openclaw-gateway.service`.

Restore local access:

```bash
unifi-on
```

Check status:

```bash
unifi-status
```

Important: `unifi-off` is a local kill switch only. It does not revoke the real API key in UniFi. In a real compromise, use `unifi-off` first, then revoke/delete the key in the UDM Pro web console.

## Backup Before Major Changes

Run this before Wi-Fi, VLAN, firewall, gateway, port profile, guest, or routing changes:

```bash
unifi-backup
```

Backups are stored under:

```bash
~/.openclaw/unifi-backups/
```

Each backup includes a timestamped folder such as:

```bash
~/.openclaw/unifi-backups/backup-20260509-192255/
```

Backup contents can include SSIDs, VLANs, firewall rules, port profiles, and possibly Wi-Fi credentials. Treat these folders as sensitive.

## Restore From Backup

Interactive restore chooser:

```bash
unifi-restore
```

The restore tool lists backups newest-first. By default it performs a dry run only and writes a restore log.

To actually apply a restore after reviewing the dry run:

```bash
unifi-restore --apply
```

It will require the typed phrase:

```text
RESTORE UNIFI CONFIG
```

Extra safety: it does not delete current objects that are not present in the backup unless explicitly requested:

```bash
unifi-restore --apply --delete-extra
```

Use `--delete-extra` only when intentionally rolling back to an older full config state.

## Getting a Local UniFi Network API Key on UDM Pro

Use this for the local UDM Pro / UniFi Network application API.

1. Open the UDM Pro web console:

   ```text
   https://<UDM-Pro-IP-or-hostname>
   ```

2. Sign in with a local/admin account that has permission to manage integrations.
3. Open the **Network** application.
4. Go to **Settings**.
5. Go to **Control Plane**.
6. Open **Integrations**.
7. Create/generate an API key or integration key.
8. Copy the key once. Store it in:

   ```bash
   ~/.openclaw/unifi.env
   ```

   The easiest path is:

   ```bash
   unifi-setup
   ```

9. Set the local base URL to the UDM Pro, for example:

   ```bash
   UNIFI_NETWORK_BASE_URL=https://192.168.1.1
   UNIFI_NETWORK_API_KEY=<the-key>
   UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1
   UNIFI_INSECURE_TLS=1
   ```

10. Verify from the shell:

    ```bash
    unifi-status
    python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites
    ```

If `/proxy/network/integration/v1` returns 404 on every endpoint but auth and host are correct, try the plural prefix used by some docs/builds:

```bash
UNIFI_NETWORK_PREFIX=/proxy/network/integrations/v1
```

Then re-test:

```bash
python3 ~/.openclaw/workspace/skills/unifi-api/scripts/unifi_api.py network-get /sites
```

## Revoking a Local UniFi Network API Key on UDM Pro

1. Use the local kill switch first if you need immediate local disable:

   ```bash
   unifi-off
   ```

2. Open the UDM Pro web console:

   ```text
   https://<UDM-Pro-IP-or-hostname>
   ```

3. Open the **Network** application.
4. Go to **Settings > Control Plane > Integrations**.
5. Find the API key/integration used by OpenClaw/Celina.
6. Delete/revoke/remove that key.
7. If a legacy username/password was configured instead of an API key, disable that service user, change its password, or remove its UniFi permissions.
8. Update the OpenClaw env file with a new key when ready:

   ```bash
   unifi-setup
   unifi-on   # only if access was disabled and you are ready to re-enable
   ```

## Site Manager Cloud API Key

The Site Manager API is separate from the local Network API. It is for high-level fleet/site/host visibility through Ubiquiti's cloud API at:

```text
https://api.ui.com/v1
```

Create/revoke Site Manager keys from the UniFi Site Manager / Ubiquiti developer workflow, not from the local UDM Pro Network Integration page.

Use this env field for Site Manager:

```bash
UNIFI_SITE_MANAGER_API_KEY=...
UNIFI_SITE_MANAGER_BASE_URL=https://api.ui.com/v1
```

## Safety Notes

- Use `unifi-backup` before major changes.
- Prefer official API-key routes over legacy username/password sessions.
- Keep `~/.openclaw/unifi.env` and backups private.
- Do not paste API keys, cookies, passwords, or restore logs into chat.
- If a key may be compromised: `unifi-off` first, then revoke the key in UniFi.
- Avoid changing VLAN/Wi-Fi/firewall settings while relying on that same network path for remote access unless you have a rollback plan.

## Official References

- Ubiquiti: Getting Started with the Official UniFi API: https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-UniFi-API
- UniFi Site Manager API docs: https://developer.ui.com/site-manager-api/
- Ubiquiti Developer portal: https://developer.ui.com/
