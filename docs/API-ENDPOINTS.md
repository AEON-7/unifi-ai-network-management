# UniFi API Endpoint Reference

This file summarizes the endpoint families used by the skill. It is not a replacement for Ubiquiti's official docs or the API docs embedded in your UniFi Network version.

Official docs:

- https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-UniFi-API
- https://developer.ui.com/site-manager-api/
- https://developer.ui.com/

## Site Manager API

Base: `https://api.ui.com/v1`

Auth: `X-API-Key: <key>`

| Endpoint | Method | Purpose | Typical AI use |
| --- | --- | --- | --- |
| `/hosts` | GET | UniFi OS host/console inventory. | Determine which consoles exist, online state, fleet overview. |
| `/sites` | GET | Sites visible to the API key. | Map site names and ids before local drill-down. |
| `/devices` | GET | Cloud-visible device inventory where available. | Cross-site device and firmware summary. |
| Versioned official paths from docs | GET/POST/etc. | Other Site Manager functions exposed by Ubiquiti. | Use only after checking official docs for the current API version. |

## Official Local Network Integration API

Default base: `https://<controller>/proxy/network/integration/v1`

Alternative prefix sometimes encountered: `/proxy/network/integrations/v1`

Auth: `X-API-Key: <key>`

| Endpoint | Method | Purpose | Typical AI use |
| --- | --- | --- | --- |
| `/sites` | GET | List local Network sites. | Select exact site id. |
| `/sites/{site_id}/devices` | GET | List devices in a site. | Gateway/AP/switch health, firmware, adoption, uplinks. |
| `/sites/{site_id}/clients` | GET | List clients in a site. | Troubleshoot clients, detect unknown devices, identify AP/SSID/VLAN. |
| Official local action paths | POST/PATCH/etc. | Actions documented by the local controller. | Guest access or other supported operations, with explicit confirmation. |

## Legacy Private Network Application API

Use these only when official APIs cannot perform the job. Routes vary by deployment:

- Standalone Network app: `/api/...`
- UniFi OS console: `/proxy/network/api/...`

Auth: cookie session from `/api/auth/login` or `/api/login`.

| Endpoint | Method | Purpose | Typical AI use |
| --- | --- | --- | --- |
| `/api/self/sites` | GET | List sites. | Find legacy site names. |
| `/api/s/{site}/stat/sta` | GET | Client stats. | RSSI, rates, AP association, client troubleshooting. |
| `/api/s/{site}/stat/device` | GET | Device stats. | AP/switch/gateway deep health and port/radio tables. |
| `/api/s/{site}/stat/health` | GET | Health summary. | WAN/LAN/WLAN health dashboard. |
| `/api/s/{site}/stat/sysinfo` | GET | Controller/system info. | Version and environment diagnostics. |
| `/api/s/{site}/rest/wlanconf` | GET | WLAN/SSID config. | SSID security and VLAN audit. |
| `/api/s/{site}/rest/networkconf` | GET | Networks/VLAN/DHCP config. | VLAN, DHCP, DNS, gateway config audit. |
| `/api/s/{site}/rest/firewallrule` | GET | Firewall rules. | Security posture and drift review. |
| `/api/s/{site}/rest/firewallgroup` | GET | Firewall groups. | Explain firewall objects and stale references. |
| `/api/s/{site}/rest/portconf` | GET | Switch port profiles. | VLAN/trunk/access profile review. |
| `/api/s/{site}/rest/portforward` | GET | Port forwards. | Exposure review and stale forwarding audit. |
| `/api/s/{site}/rest/routing` or `/route` | GET | Static routes/routing config where present. | Route audit. |
| `/api/s/{site}/rest/usergroup` | GET | User/client groups. | Bandwidth/user policy audit. |
| `/api/s/{site}/rest/setting` | GET | Site settings. | Site-level config review. |
| `/api/s/{site}/rest/radiusprofile` | GET | RADIUS profiles. | Auth and enterprise Wi-Fi audit. |
| `/api/s/{site}/rest/dynamicdns` | GET | Dynamic DNS config. | WAN/DDNS audit. |
| `/api/s/{site}/rest/trafficroute` | GET | Traffic routes where present. | Policy routing review. |
| `/api/s/{site}/rest/trafficrule` | GET | Traffic rules where present. | Client/app policy review. |
| `/api/s/{site}/rest/dnsfilter` | GET | DNS filtering config where present. | DNS security policy review. |
| `/api/s/{site}/cmd/stamgr` | POST | Station manager commands such as reconnect/block/unblock. | Confirmed client containment or reconnect. |
| `/api/s/{site}/cmd/devmgr` | POST | Device commands where supported. | Maintenance actions only. |

## Write Safety

POST/PATCH/PUT/DELETE operations must be treated as writes even when the endpoint name sounds harmless. For writes:

1. Fetch current state.
2. Identify exact object by at least two fields.
3. Backup first for major changes.
4. Prefer official API.
5. Execute one narrow action.
6. Read back and verify.
