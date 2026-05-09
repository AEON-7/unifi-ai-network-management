# Operational Security for AI Network Management

Giving an AI network API access is a trust and blast-radius decision. This package is designed to make that decision explicit and reversible.

## Key Handling

- Store keys in `~/.openclaw/unifi.env` only.
- Use mode `0600` for env files.
- Do not paste keys into chat, tickets, screenshots, or logs.
- Do not commit real keys to git.
- Use `unifi-setup` to enter secrets without terminal echo.
- Rotate keys after testing, after staff changes, and after suspected compromise.

## Least Privilege

Prefer separate credentials:

| Credential | Recommended use |
| --- | --- |
| Site Manager read key | Fleet visibility and discovery. |
| Local Network API read key | Daily monitoring and diagnostics. |
| Local write key | Maintenance windows and explicit change operations. |
| Legacy account | Disabled unless an official API route is missing. |

If UniFi exposes read-only roles in your deployment, use them for normal agent operation.

## Break Glass

Local immediate disable:

```bash
unifi-off
```

Then revoke the real key in UniFi:

- Network API: Network > Settings > Control Plane > Integrations
- Site Manager API: UniFi Site Manager / Ubiquiti developer API key workflow
- Legacy: disable service user or rotate password

## Change Safety

Before major changes:

```bash
unifi-backup
```

Major changes include VLANs, DHCP, DNS, firewall, SSIDs, WAN, port profiles, PoE, firmware upgrades, device adoption, or anything that could sever the management path.

## Agent Rules

A well-behaved agent should:

1. Use read-only calls first.
2. Avoid legacy private routes unless official APIs are insufficient.
3. Verify target site/device/client exactly.
4. Describe the intended action and rollback.
5. Apply the smallest change.
6. Verify after action.
7. Never expose secrets.

## Incident Response

If the agent appears to be acting incorrectly:

1. Run `unifi-off`.
2. Revoke the real key in UniFi.
3. Preserve logs and restore logs.
4. Inspect recent controller changes.
5. Restore from backup if needed with `unifi-restore`.
6. Rotate keys and re-enable only after review.
