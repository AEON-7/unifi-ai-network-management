# UniFi API Troubleshooting

Use this when an API call fails or returns surprising data.

## First Triage

1. Confirm which surface you are using: Site Manager, official local Network API, or legacy.
2. Confirm base URL and prefix.
3. Confirm auth type: API key vs cookie login.
4. Run one read-only discovery endpoint.
5. Capture HTTP status and response body, but redact secrets.

## Helper Environment Check

```bash
python3 scripts/unifi_api.py env
```

The output shows whether variables are present without printing values.

## HTTP Status Guide

### 000 / connection errors

Likely causes:

- Wrong IP/hostname/port
- Controller offline
- Firewall or VLAN path issue
- TLS handshake failure
- DNS resolves to the wrong host

Next checks:

```bash
ping <host>
curl -k -I https://<host>/
```

### 400 Bad Request

Likely causes:

- Body schema wrong
- Missing required field
- Wrong content type
- Using a legacy command shape against an official endpoint

Fix:

- Re-read the live response schema.
- Use exact IDs from a fresh GET.
- Try a read-only endpoint on the same prefix to prove auth and routing.

### 401 Unauthorized

Likely causes:

- Missing API key
- Wrong API key type
- Expired/invalid key
- Legacy login failed
- Cookie not sent because the login route changed

Fix:

- Site Manager: verify `UNIFI_SITE_MANAGER_API_KEY`.
- Local official API: verify `UNIFI_API_KEY` and that the key belongs to the target UniFi Network application.
- Legacy: verify `UNIFI_USERNAME`, `UNIFI_PASSWORD`, MFA/session rules, and login route.

### 403 Forbidden

Likely causes:

- Key lacks permission
- User role lacks site access
- Action forbidden by controller role
- Site belongs to a different host/account

Fix:

- Check UniFi role permissions.
- Test a read-only endpoint first.
- Use Site Manager to verify the site-host mapping.

### 404 Not Found

Likely causes:

- Wrong API surface
- Wrong prefix, especially singular `integration` vs plural `integrations`
- UniFi OS console path needs `/proxy/network`
- Standalone controller path does not use `/proxy/network`
- Site ID/name mismatch

Fix examples:

```bash
# Official local prefix variant
export UNIFI_NETWORK_PREFIX=/proxy/network/integrations/v1
python3 scripts/unifi_api.py network-get /sites

# Legacy UniFi OS console vs standalone
python3 scripts/unifi_api.py legacy-get /api/self/sites
python3 scripts/unifi_api.py legacy-get /proxy/network/api/self/sites
```

### 409 Conflict

Likely causes:

- Resource already in requested state
- Controller operation already running
- Firmware/adoption/upgrade state conflict

Fix:

- Refresh state.
- Avoid retry loops for writes.
- Report the current state.

### 429 Rate Limited

Likely causes:

- Cloud API polling too aggressively
- Agent loop querying many objects one by one

Fix:

- Back off exponentially.
- Batch by fetching large lists once and filtering locally.
- Cache inventory for the current task.

### 5xx Server Error

Likely causes:

- Controller busy/restarting
- UniFi OS update in progress
- API bug
- Cloud service transient

Fix:

- Retry read-only calls with a short delay.
- Do not retry writes blindly.
- Check controller health and logs.

## TLS and Self-Signed Certificates

Local UniFi consoles often use self-signed certificates. For local trusted networks, this skill supports:

```bash
export UNIFI_INSECURE_TLS=1
```

Use only for local controller calls. Do not disable TLS verification for cloud `api.ui.com`.

## Legacy Login Problems

The helper tries both common login routes:

```text
/api/auth/login
/api/login
```

If both fail:

- Confirm the host is the controller, not only an app landing page.
- Confirm local credentials are allowed to use the Network application.
- Confirm MFA/session requirements.
- Prefer official API keys if available.

## Data Shape Drift

UniFi versions return different fields. When the agent is unsure:

1. Save a redacted sample of one object.
2. Identify stable fields: `id`, `_id`, `mac`, `name`, `site_id`, `model`.
3. Match objects by multiple fields.
4. Avoid writing back partial config objects unless the endpoint explicitly supports patch semantics.

## Avoid These Mistakes

- Do not use a site display name where the endpoint expects a site id or legacy site name.
- Do not assume `default` is the only site.
- Do not paste full cookies or API keys into Matrix/chat.
- Do not reboot the gateway currently carrying the SSH/API path unless the user explicitly asked for it.
- Do not change Wi-Fi security or VLANs during a voice/text session unless there is another management path.
- Do not use a command endpoint to answer a read-only question.

## Safe Debug Bundle

When asking for help or documenting a failure, collect:

```text
surface: site-manager | network | legacy
base_url: redacted host only
path: /the/path
status: HTTP status
controller_version: if known
site: display name/id, if non-secret
operation: read-only or write
response_error: redacted error message
```

Never include keys, passwords, cookies, or tokens.