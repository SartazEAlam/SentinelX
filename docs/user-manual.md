# SentinelX: Endpoint User Manual

**Document Version:** 1.0.0 (Final Delivery)  
**Target Audience:** Enterprise Employees, Workstation Operators, Monitored Users  

---

## 1. Introduction to SentinelX Endpoint Protection

SentinelX is an intelligent Data Loss Prevention (DLP) agent operating on your corporate Windows workstation. Its purpose is to protect confidential organizational assets, customer records, and credentials from accidental exposure or malicious exfiltration while maintaining a frictionless user experience for legitimate day-to-day work.

---

## 2. What SentinelX Monitors

SentinelX monitors specific designated directories and removable hardware interfaces:
- **Protected Corporate Directories:** Paths designated by IT policy (e.g., project workspaces, customer data folders).
- **Removable Media:** USB flash drives and external storage devices attached to the endpoint.
- **External Network Transfers:** Uploads to unapproved cloud hosts or public drop zones.

> **Privacy Guarantee:** SentinelX does **not** log personal keystrokes, personal webcam activity, or private credentials outside of enterprise designated folders. Content inspection is limited to corporate boundary enforcement.

---

## 3. Understanding Operation Outcomes

When you perform an operation on a file (such as copying, saving, or moving data to an external drive), SentinelX classifies the content and assesses the risk. You will experience one of three outcomes:

### 3.1 Outcome 1: ALLOW (Transparent Operation)
- **Condition:** Non-sensitive documents, public reports, internal documentation handled within trusted directories.
- **User Experience:** Instant and transparent. No popups or delays occur.
- **Example:** Editing a weekly engineering memo or saving a local project draft.

### 3.2 Outcome 2: HOLD (Quarantine & Approval Request)
- **Condition:** Sensitive documents (e.g., employee payroll lists, customer records) transferred to external media or shared off-hours.
- **User Experience:**
  1. The file is safely moved into a local secure quarantine staging folder.
  2. A notification alert informs you that administrative review is required.
  3. A request is generated on the SOC Administrator Dashboard.
- **Next Steps:**
  - Contact your IT Security Administrator or SOC team.
  - Once the SOC analyst reviews and grants the approval, the file is automatically released and transferred to your intended destination.
  - If rejected or if no review occurs within the 5-minute timeout, the file is safely removed from staging to prevent exposure.

### 3.3 Outcome 3: BLOCK (Immediate Prevention)
- **Condition:** Highly confidential secrets (e.g., unencrypted database passwords, private encryption keys, bulk payment card numbers) being copied to untrusted external storage or uploaded to unauthorized public cloud hosts.
- **User Experience:**
  1. The file operation is immediately terminated.
  2. The sensitive file is blocked and deleted from the unauthorized drop location.
  3. A critical security incident is logged to the corporate Security Operations Center (SOC).
- **Next Steps:**
  - Contact the Security Operations Center immediately if you believe this was triggered in error during legitimate software testing.

---

## 4. Best Practices for Employees

1. **Keep Secrets in Vaults:** Never store raw passwords or production API keys in plain text files or spreadsheets on local drives.
2. **Use Approved Cloud Storage:** Only synchronize corporate documents with designated corporate cloud repositories (e.g., internal SharePoint or corporate drives) rather than personal storage accounts.
3. **Notify Security for Bulk Transfers:** If your role requires exporting customer lists or payroll data for external audit, notify your supervisor and SOC team beforehand to expedite approval workflows.
