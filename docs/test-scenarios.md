# SentinelX Integration Test Scenarios

This document outlines the standard end-to-end integration tests required to validate the entire SentinelX pipeline (Agent → Classification → Risk → Policy → Enforcement → Backend → Dashboard).

## Controlled Synthetic Data

We use explicitly synthetic test files to validate classification without exposing real PI/PHI.
- `synthetic_financial.txt`: Contains obvious fake credit card patterns (e.g. `4532-XXXX-XXXX-1234`).
- `synthetic_customer.csv`: Contains fake SSN strings (e.g. `XXX-XX-1234`) or dummy names.
- `synthetic_safe.txt`: Contains harmless boilerplate text.

## Test Matrix

| ID  | Scenario Category | Operation Details | Expected Result |
| --- | ----------------- | ----------------- | --------------- |
| T01 | Legitimate Ops    | Copy `synthetic_safe.txt` locally | ALLOW |
| T02 | Warning Transfer  | Copy `synthetic_customer.csv` | HOLD |
| T03 | High-Risk Ops     | Copy `synthetic_financial.txt` | BLOCK |
| T04 | SecOps Approval   | Admin APPROVEs the HOLD for T02 | ALLOW (Proceeds) |
| T05 | SecOps Denial     | Admin DENYs the HOLD for T02 | BLOCK (Prevented) |
| T06 | Duplicate Ops     | Send same event twice within 5s | Deduplicated at Agent |
| T07 | Offline Mode      | Disconnect Agent, trigger event, Reconnect | Synced to Server |
| T08 | Auth & Security   | Submit event with invalid JWT | 401 Unauthorized |
| T09 | Server Failure    | Stop server, trigger event, Start server | Recovery & Sync |

---

## Detailed Scenarios

### Scenario A: Legitimate Operation
1. The user copies `synthetic_safe.txt` to another directory.
2. The agent normalizes the filesystem event.
3. The classifier finds no sensitive data (Risk = Low).
4. The policy engine outputs `ALLOW`.
5. The enforcement engine lets the OS complete the file copy.
6. The event is batched and posted to the backend.
7. The Dashboard displays an `ALLOW` event in real-time.

### Scenario B: Warning-Level (HOLD) & APPROVE
1. The user attempts to move `synthetic_customer.csv`.
2. The classifier detects PII. Risk score hits warning threshold.
3. The policy engine outputs `HOLD`.
4. The enforcement engine stages the file securely and suspends the transfer.
5. The backend receives the event and generates an `Approval` record.
6. An Administrator navigates to `/approvals` and clicks **Approve**.
7. The backend processes the approval. The agent polls the decision.
8. The enforcement engine restores the file to the destination. Operation allowed.

### Scenario C: High-Risk (BLOCK)
1. The user attempts to copy `synthetic_financial.txt`.
2. The classifier detects PCI data. Risk hits critical threshold.
3. The policy engine outputs `BLOCK`.
4. The enforcement engine denies the OS operation or deletes the destination file.
5. The backend receives the blocked event.
6. The Dashboard triggers a high-severity alert to the Administrator.
