# AI Use Cases for UniFi Networks

## Reliability

- Find clients with weak RSSI or poor link rates.
- Detect AP overload or uneven client distribution.
- Identify offline devices and recent reconnect patterns.
- Summarize firmware drift and upgrade candidates.
- Explain topology: client -> AP/switch -> gateway.

## Efficiency

- Recommend safer channel/band/power reviews based on observed client distribution.
- Find stale SSIDs, unused networks, stale firewall groups, and old port forwards.
- Generate before/after change records.
- Maintain an inventory report with names, MACs, models, firmware, and roles.

## Security

- Compare connected clients against an expected inventory.
- Flag unknown devices, suspicious hostnames, or unexpected VLAN/SSID placement.
- Summarize firewall and port-forward exposure.
- Correlate events with clients, ports, APs, and VLANs.
- Recommend containment steps.

## Active Defense, With Constraints

Potential active actions include:

- Reconnect a misbehaving Wi-Fi client.
- Block a confirmed rogue client.
- Unblock a client after verification.
- Disable or change a risky rule only after explicit user approval.
- Prepare a maintenance plan for firmware upgrades.

Active defense should be narrow, reversible, and verified. The agent should never make broad firewall, VLAN, or Wi-Fi security changes based on a vague threat summary.
