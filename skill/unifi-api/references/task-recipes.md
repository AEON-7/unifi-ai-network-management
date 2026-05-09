# Task Recipes

Use these recipes to keep UniFi work calm, precise, and reversible.

## Recipe: Network Health Summary

Goal: answer "How is my UniFi network doing?"

Steps:

1. Use Site Manager if configured:

   ```bash
   python3 scripts/unifi_api.py site-manager-get /hosts
   python3 scripts/unifi_api.py site-manager-get /sites
   ```

2. Use local Network API or legacy device stats for detailed site state:

   ```bash
   python3 scripts/unifi_api.py network-get /sites/<site_id>/devices
   # or
   python3 scripts/unifi_api.py legacy-devices --site default
   ```

3. Summarize by category:

   - Gateways: online, WAN state, firmware, uptime
   - Switches: online, uplink, PoE budget, firmware
   - APs: online, channel, client count, firmware
   - Clients: total, wired/wireless, top talkers if exposed
   - Alerts/anomalies: offline, updateable, adopting, isolated, high retries

4. Do not propose config changes unless the user asks.

## Recipe: Find Why a Client Is Having Bad Wi-Fi

Inputs: client name, MAC, IP, or description.

Steps:

1. List clients.
2. Match the client by exact MAC if possible.
3. Record:

   - AP MAC/name
   - SSID
   - Band/channel if present
   - RSSI/signal/noise
   - Tx/Rx rates
   - Roaming history if available
   - Uptime and last seen
   - IP and VLAN/network

4. List AP device details for the AP serving that client.
5. Look for obvious causes:

   - Weak RSSI or low SNR
   - Connected to distant AP
   - 2.4 GHz when 5/6 GHz expected
   - Low Tx/Rx PHY rates
   - AP overload
   - Recent roam loops
   - Wrong VLAN/SSID

6. Only reconnect/kick the client if the user asks or if they explicitly said to fix connectivity now.

## Recipe: Reconnect One Client

This is a low-impact write if the exact client is verified.

1. Find the client by exact MAC.
2. Confirm it is the intended device by hostname/IP/SSID.
3. Run:

   ```bash
   python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
     --body '{"cmd":"kick-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
     --yes-I-understand
   ```

4. Verify the client reconnects or is last-seen updated.
5. Report result.

## Recipe: Audit Firmware Updates

1. List devices.
2. For each device, capture name, model, version, upgradeable/update availability.
3. Group by device type.
4. Do not start upgrades automatically unless the user asks.
5. If asked to upgrade:

   - Upgrade APs/switches in batches, not all at once.
   - Avoid upgrading the gateway carrying the current management connection unless planned.
   - Warn about brief outages.
   - Verify devices return online.

## Recipe: SSID and VLAN Mapping Audit

1. Read WLAN config.
2. Read network/VLAN config.
3. Build a table:

   - SSID
   - Enabled
   - Security mode
   - Guest/captive portal state
   - VLAN/network mapping
   - Band restrictions if visible
   - Hidden/broadcast state

4. Flag unclear or risky mappings.
5. Do not write SSID config from a partial object.

## Recipe: Guest Access

1. Identify the site.
2. Identify the client MAC.
3. Prefer official local guest endpoints if available in the deployed Network version.
4. If legacy is needed, read current guest/client state first.
5. Authorize with a bounded duration where possible.
6. Verify status afterward.

## Recipe: Switch Port / PoE Issue

High-impact if cycling PoE or disabling a port.

1. Find switch by name/MAC/IP.
2. Read `port_table` or official device port state.
3. Identify port by port index and connected client/device.
4. If PoE cycle is requested:

   - Confirm target port.
   - Warn that the attached device will briefly lose power.
   - Make sure it is not an uplink or management-critical port.
   - Execute one port action.
   - Verify the port returns to expected state.

## Recipe: Create a Change Record

For non-trivial writes, produce a tiny change record in the response:

```text
Change: <what changed>
Target: <site/device/client/network>
Before: <important old value>
After: <important new value>
Verification: <readback endpoint/result>
Rollback: <how to reverse it>
```

Do not include secrets.


## Recipe: Backup Before Major Change

Use this before VLAN, firewall, Wi-Fi, routing, DHCP, DNS, port profile, firmware, or multi-device changes.

1. Run:

   ```bash
   unifi-backup
   ```

2. Confirm the command prints a timestamped path under `~/.openclaw/unifi-backups/`.
3. Include that backup path in the change plan and final report.
4. If backup fails, do not proceed with a major write unless the user explicitly accepts the risk.

## Recipe: Restore From Backup

Use only when the user explicitly asks to restore or roll back UniFi configuration.

1. List backups newest-first:

   ```bash
   find ~/.openclaw/unifi-backups -maxdepth 1 -type d -name 'backup-*' -printf '%f\n' | sort -r
   ```

2. If more than one backup exists, ask the user which date/time to restore.
3. Run dry-run first:

   ```bash
   unifi-restore --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS
   ```

4. Summarize update/create/extra-current/error counts.
5. Ask for explicit confirmation before applying.
6. Apply only after confirmation:

   ```bash
   unifi-restore --backup ~/.openclaw/unifi-backups/backup-YYYYMMDD-HHMMSS --apply --confirm 'RESTORE UNIFI CONFIG'
   ```

7. Use `--delete-extra` only when the user explicitly requests a full rollback and accepts deletion of objects not present in the backup.

