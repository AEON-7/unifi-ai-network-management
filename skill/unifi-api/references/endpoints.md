# Endpoint Catalog

This catalog is intentionally practical. It lists common routes and usage patterns, but the official Ubiquiti docs and the live controller schema are authoritative.

## Helper Path Rules

The helper accepts either absolute URLs or paths.

- `site-manager-get /sites` means `https://api.ui.com/v1/sites`.
- `network-get /sites` means `$UNIFI_NETWORK_BASE_URL$UNIFI_NETWORK_PREFIX/sites`.
- `legacy-get /api/s/default/stat/sta` means `$UNIFI_LEGACY_BASE_URL/api/s/default/stat/sta` unless the helper detects that `/proxy/network` is needed.

## Site Manager API

Base:

```text
https://api.ui.com/v1
```

Common read-only calls:

```bash
python3 scripts/unifi_api.py site-manager-get /hosts
python3 scripts/unifi_api.py site-manager-get /sites
python3 scripts/unifi_api.py site-manager-get /devices
```

Expected use:

- Find hosted consoles and sites.
- Map a site to a host/console.
- Check high-level health before local drill-down.

If a route returns 404, check the current official Site Manager API reference; the cloud API is versioned and routes can move between releases.

## Official Local Network Integration API

Base prefix default:

```text
/proxy/network/integration/v1
```

Common discovery calls:

```bash
python3 scripts/unifi_api.py network-get /sites
python3 scripts/unifi_api.py network-get /sites/<site_id>/devices
python3 scripts/unifi_api.py network-get /sites/<site_id>/clients
```

Common object workflow:

1. `network-get /sites`
2. Select a site by name/id.
3. `network-get /sites/<site_id>/devices` or `/clients`
4. Match by exact MAC, hostname, IP, or device name.
5. Use returned IDs for any follow-up.

Generic GET:

```bash
python3 scripts/unifi_api.py network-get /sites/<site_id>/clients | jq .
```

Generic POST requires explicit write acknowledgement:

```bash
python3 scripts/unifi_api.py network-post /some/path \
  --body '{"example":true}' \
  --yes-I-understand
```

If you see 404 on every local official endpoint:

```bash
export UNIFI_NETWORK_PREFIX=/proxy/network/integrations/v1
python3 scripts/unifi_api.py network-get /sites
```

Also confirm whether `UNIFI_NETWORK_BASE_URL` should point to the UniFi OS console root, not directly to `/network` or `/manage` UI pages.

## Legacy Private Network Application API

Legacy routes may be rooted differently depending on deployment:

- UniFi OS console: `/proxy/network/api/...`
- Standalone Network Application: `/api/...`

The helper sends exactly the path you pass. If the controller is a UniFi OS console and a `/api/...` path returns 404, try `/proxy/network/api/...`.

### Sites

```bash
python3 scripts/unifi_api.py legacy-sites
```

Equivalent common routes:

```text
GET /api/self/sites
GET /proxy/network/api/self/sites
```

### Clients

```bash
python3 scripts/unifi_api.py legacy-clients --site default
```

Equivalent common routes:

```text
GET /api/s/<site>/stat/sta
GET /proxy/network/api/s/<site>/stat/sta
```

Useful client fields often include:

- `mac`
- `hostname`
- `name`
- `ip`
- `is_wired`
- `essid`
- `ap_mac`
- `sw_mac`
- `uptime`
- `rx_bytes`, `tx_bytes`
- `rssi`, `signal`, `noise`, `tx_rate`, `rx_rate`

Do not assume all fields exist.

### Devices

```bash
python3 scripts/unifi_api.py legacy-devices --site default
```

Equivalent common routes:

```text
GET /api/s/<site>/stat/device
GET /proxy/network/api/s/<site>/stat/device
```

Useful fields often include:

- `name`
- `model`
- `type`
- `mac`
- `ip`
- `state`
- `version`
- `upgradeable`
- `adopted`
- `uplink`
- `port_table`
- `radio_table`

### WLAN/SSID config

Read first:

```bash
python3 scripts/unifi_api.py legacy-get /api/s/default/rest/wlanconf
```

Possible UniFi OS console path:

```bash
python3 scripts/unifi_api.py legacy-get /proxy/network/api/s/default/rest/wlanconf
```

Do not update WLAN config until you have captured the full current object. Legacy `set` operations often require sending complete objects, not tiny patches.

### Networks/VLAN config

```bash
python3 scripts/unifi_api.py legacy-get /api/s/default/rest/networkconf
```

Capture the object before any write. Network changes can break gateway, DNS, DHCP, and VLAN access.

### Reconnect, block, unblock clients

Reconnect/kick one station:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"kick-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

Block:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"block-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

Unblock:

```bash
python3 scripts/unifi_api.py legacy-post /api/s/default/cmd/stamgr \
  --body '{"cmd":"unblock-sta","mac":"aa:bb:cc:dd:ee:ff"}' \
  --yes-I-understand
```

Verify after action by reading the client list again.

### Device commands

Many controller versions expose command routes under:

```text
/api/s/<site>/cmd/devmgr
/proxy/network/api/s/<site>/cmd/devmgr
```

Examples in community clients include restart, force provision, locate, and upgrade actions. These are high impact. Do not run them without explicit user intent and exact device verification.

## Pagination and Filtering

Cloud APIs may paginate. If a response includes cursors such as `next`, `nextToken`, `offset`, or `limit`, follow them until complete unless the user only asked for a sample.

For large local client lists:

- Retrieve once.
- Filter locally with `jq`.
- Avoid repeated API calls inside loops.

## Common jq Patterns

Find by MAC:

```bash
jq '.data[] | select((.mac // "") | ascii_downcase == "aa:bb:cc:dd:ee:ff")'
```

List devices compactly:

```bash
jq -r '.data[] | [.name, .model, .type, .mac, .ip, .state, .version] | @tsv'
```

Wireless client signal summary:

```bash
jq -r '.data[] | select(.is_wired == false) | [.hostname, .mac, .essid, .ap_mac, .rssi, .tx_rate, .rx_rate] | @tsv'
```

## Endpoint Selection Checklist

Before a write:

- Did you identify the correct site?
- Did you identify the exact client/device/network by more than one field?
- Is there an official endpoint for this action?
- Did you capture current state?
- Is the command idempotent or reversible?
- Did you verify after the write?