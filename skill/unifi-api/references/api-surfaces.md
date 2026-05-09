# UniFi API Surfaces

UniFi has multiple API surfaces. The agent should choose the narrowest official surface that can satisfy the request, and fall back to private legacy routes only when needed.

## 1. Site Manager API

Base URL:

```text
https://api.ui.com/v1
```

Authentication:

```http
X-API-Key: <site-manager-api-key>
Accept: application/json
```

Best for:

- Listing UniFi OS hosts and cloud-managed sites
- Fleet-level health and inventory
- Looking up which console owns a site
- Cloud-visible status across multiple locations
- Starting a workflow before connecting to a local console

Typical tasks:

```bash
python3 scripts/unifi_api.py site-manager-get /hosts
python3 scripts/unifi_api.py site-manager-get /sites
```

Notes:

- API keys are created from the UniFi Site Manager / API key workflow documented by Ubiquiti.
- This is not the best surface for every low-level LAN action.
- Keep responses compact; cloud inventory can be large.

## 2. Official Local Network Integration API

Base URL pattern:

```text
https://<unifi-os-console-or-network-app>
```

Default prefix used by this skill:

```text
/proxy/network/integration/v1
```

Some controller builds or documentation revisions may use a pluralized prefix. If every official local call returns 404 while auth is correct, try:

```bash
export UNIFI_NETWORK_PREFIX=/proxy/network/integrations/v1
```

Authentication:

```http
X-API-Key: <network-api-key>
Accept: application/json
```

Best for:

- Local sites
- UniFi Network clients
- UniFi Network devices
- Guest authorization where supported
- Stable local inventory without cookie login

Typical tasks:

```bash
python3 scripts/unifi_api.py network-get /sites
python3 scripts/unifi_api.py network-get /sites/<site_id>/devices
python3 scripts/unifi_api.py network-get /sites/<site_id>/clients
```

Notes:

- Generate local API keys inside the UniFi Network application where available.
- The official local API is versioned but still changes with UniFi Network releases.
- Always inspect the returned schema instead of assuming field names.

## 3. Legacy Private Network Application API

Base URL examples:

```text
https://192.168.1.1
https://192.168.1.1:8443
https://unifi.local
```

Authentication:

- Cookie session from `/api/auth/login` on UniFi OS consoles, or
- Cookie session from `/api/login` on older standalone Network Application instances

Best for:

- Actions not exposed in official APIs yet
- Compatibility with older controller workflows
- Community-known operations such as station reconnect/block, WLAN config reads, and device command routes

Typical login sequence handled by the helper:

1. Try `POST /api/auth/login`
2. If that fails, try `POST /api/login`
3. Store cookies in memory for the process
4. Call `/proxy/network/api/...` or `/api/...` paths

Warnings:

- These endpoints are private and may change without notice.
- Response fields can differ across Network Application versions.
- Do not use legacy write routes when an official API can do the same job.
- For destructive actions, verify the exact object first.

## Environment Variables

Recommended private env file: `~/.openclaw/unifi.env`

Recommended `.env` shape:

```bash
# Official Site Manager cloud API
UNIFI_SITE_MANAGER_API_KEY=...

# Official local Network API
UNIFI_NETWORK_BASE_URL=https://192.168.1.1
UNIFI_API_KEY=...
UNIFI_NETWORK_PREFIX=/proxy/network/integration/v1

# Legacy private API fallback
UNIFI_LEGACY_BASE_URL=https://192.168.1.1
UNIFI_USERNAME=...
UNIFI_PASSWORD=...
UNIFI_SITE=default
UNIFI_INSECURE_TLS=1
```

Do not put credentials in skill files. Put them in the gateway environment, a private `.env`, or the host service environment.

## Choosing Between Cloud and Local

Use Site Manager when the question is about global status or finding the right console. Use the local Network API when the question is about devices, clients, or Wi-Fi state inside one site. Use legacy only when the task needs a controller action not supported by official APIs.

## Safety Tiers

Read-only:

- List hosts/sites/devices/clients
- Inspect SSIDs, networks, DHCP, VLANs, WAN health
- Summarize firmware/update status

Low-impact writes:

- Reconnect one client
- Rename one client alias
- Authorize a guest client for a limited time

High-impact writes:

- Reboot a gateway, switch, or AP
- Change SSIDs/security/VLAN/firewall/WAN/DHCP
- PoE cycle a switch port
- Adopt, forget, delete, upgrade, or factory-reset devices

High-impact writes require either an explicit user request naming the action or a final concise confirmation.

## Version Awareness

UniFi API support changes quickly. When a call does not match this runbook:

1. Check the official docs first.
2. Confirm the Network Application version.
3. Run a read-only discovery endpoint.
4. Inspect returned links, IDs, and schemas.
5. Update this skill if the deployed controller has a newer stable route.