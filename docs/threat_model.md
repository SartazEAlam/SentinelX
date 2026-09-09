# SentinelX — Threat Model

> This document will be expanded as security features are implemented in later phases.

## Assets to Protect

- Sensitive organizational data (classified by sensitivity level)
- User credentials and authentication tokens
- System configuration and secrets
- Audit logs and security events

## Threat Categories

1. **Data Exfiltration** — Unauthorized transfer of sensitive data via USB, network, or cloud services
2. **Insider Threats** — Malicious or negligent actions by authorized users
3. **Privilege Escalation** — Unauthorized access to administrative functions
4. **Tampering** — Modification of security policies, events, or audit logs
5. **Denial of Service** — Disruption of monitoring or enforcement capabilities

## Mitigations (Planned)

| Threat | Mitigation | Phase |
|--------|-----------|-------|
| Data exfiltration via USB | USB device monitoring and blocking | 5 |
| Sensitive file transfers | File operation interception | 5 |
| Credential theft | JWT with short expiry, secure storage | 1 |
| Log tampering | Immutable audit log, server-side validation | 1 |
| Policy bypass | Server-authoritative policy enforcement | 4 |
