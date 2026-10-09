# SentinelX — Academic Viva & Technical Defense Guide

This document prepares project authors for the final-year academic oral defense (Viva Voce). Every question is answered concisely, with direct references to implemented architecture, algorithms, empirical test results, and actual source code.

---

## 1. Project Foundations & Motivation

### Q1: What is SentinelX?
**Answer:**
SentinelX is a context-aware Endpoint Data Loss Prevention (DLP) and Exfiltration Detection System. It runs an intelligent background daemon on endpoint workstations (Windows, Linux, macOS) that intercepts file modifications, USB transfers, network uploads, and clipboard activities in real time. It uses a **Hybrid Detection Engine** (combining deterministic regex/keyword heuristics with supervised machine learning classifiers) coupled with a dynamic **Multi-Factor Risk Assessment Engine** to classify data confidentiality and enforce tiered policy actions (`ALLOW`, `HOLD`, or `BLOCK`).

### Q2: What specific problem does SentinelX solve?
**Answer:**
Traditional endpoint DLP systems suffer from two major flaws:
1. **High False Positive Rates:** Pure regex-based DLP flags benign files containing number sequences (e.g., zip codes, math worksheets, source code constants) as sensitive credit card or SSN leaks, disrupting daily business operations.
2. **Context Blindness:** Legacy DLPs evaluate content in isolation without considering contextual exfiltration vectors—such as transfer destination (internal NAS vs. external cloud storage), time of day (normal working hours vs. 3:00 AM off-hours), transfer volume burstiness, employee risk tier, or previous violation frequency.

SentinelX solves this by synthesizing deep textual classification with an 8-factor contextual risk formula, preventing exfiltration without blocking routine developer or administrative work.

### Q3: Why is Data Loss Prevention (DLP) critical in modern enterprise cybersecurity?
**Answer:**
Data breaches consistently cost enterprises millions in regulatory fines (GDPR, HIPAA, PCI-DSS) and intellectual property loss. Over 60% of data exfiltration incidents originate from insider threats, compromised employee credentials, or accidental transfers via removable USB drives and unauthorized web uploads. DLP enforces boundary control at the endpoint—the point of origin before data enters encrypted transit tunnels where perimeter firewalls can no longer inspect packet payloads.

### Q4: What were the core technical objectives of the SentinelX project?
**Answer:**
1. **Low-Latency Endpoint Monitoring:** Intercept system file-system events, removable media attachment, and clipboard buffers with minimal CPU/RAM overhead (<2% CPU, <50MB RAM).
2. **Hybrid Classification Intelligence:** Combine deterministic regex patterns (high precision on structured formats) with TF-IDF-based Machine Learning (Logistic Regression & Random Forest for unstructured text).
3. **Multi-Factor Risk Scoring:** Formulate an 8-parameter risk model outputting scores between `0.0` and `1.0`.
4. **Tiered Policy Enforcement:** Execute automated `ALLOW`, synchronous containment `HOLD` (quarantine + administrator approval loop), and immediate `BLOCK`.
5. **Real-Time SOC Dashboard:** Provide centralized administrative visibility via FastAPI backend and React dashboard with WebSocket notifications and complete SHA-256 audit trails.

---

## 2. Architecture & Tech Stack Decisions

### Q5: How is the system architecture organized?
**Answer:**
SentinelX follows a distributed client-server architecture:
- **Endpoint Agent (`agent/`):** Python-based daemon running on protected workstations. Houses event interceptors (`watchdog` file monitor, USB volume poller, clipboard reader), a local hybrid classifier, quarantine isolation staging, and an asynchronous HTTP/WebSocket agent client.
- **Central Management Backend (`backend/`):** FastAPI application serving RESTful APIs, WebSocket hub for real-time alerting, SQLite/PostgreSQL persistence via SQLAlchemy ORM, and policy synchronization.
- **SOC Administrator Dashboard (`dashboard/`):** React 18 SPA (Vite, TailwindCSS, Lucide icons) displaying live incident streams, pending approval queues, policy rules editors, device telemetry, and evaluation metrics.

### Q6: Why was FastAPI selected for the backend rather than Django or Flask?
**Answer:**
1. **Native Asynchronous Concurrency (`async`/`await`):** DLP backends process continuous heartbeat pings, concurrent event streams, and real-time WebSocket broadcasts from multiple agents. FastAPI's `asyncio` core easily scales non-blocking I/O operations.
2. **Automatic Pydantic Validation & Serialization:** Every telemetry payload and security event schema is strictly type-checked at the HTTP boundary, eliminating malformed packet bugs.
3. **High Throughput / Low Overhead:** Powered by Starlette and Uvicorn (uvloop), FastAPI achieves benchmark performance comparable to Go and Node.js while retaining Python's rich data science and ML ecosystem.
4. **Interactive OpenAPI (Swagger) Documentation:** Instant auto-generated docs at `/docs` simplified endpoint integration and test automation.

### Q7: How does the endpoint agent work from event capture to backend reporting?
**Answer:**
1. **Capture:** The `watchdog` library hooks OS filesystem event queues. The agent filters temporary OS files (`.tmp`, `.crdownload`).
2. **Extraction:** Supported text files (`.txt`, `.csv`, `.json`, `.py`, `.md`) are read.
3. **Classification:** Text is evaluated by regex patterns, keyword sets, and ML models. If sensitive tokens (e.g., credit card, API key, SSN) are detected, a classification result (`category`, `confidence`, `evidences`) is generated.
4. **Risk Calculation:** Classification confidence is combined with contextual signals (destination channel, transfer size, time of day, device trust).
5. **Enforcement:**
   - Score `< 0.35`: `ALLOW` — log event and let process proceed.
   - Score `0.35 - 0.70`: `HOLD` — file is instantly moved to secure quarantine (`.quarantine/`), event sent to backend with `PENDING` approval.
   - Score `> 0.70`: `BLOCK` — file operation aborted or isolated, event recorded as `BLOCKED`.
6. **Reporting:** Event payload is dispatched asynchronously via HTTP POST (`/api/v1/events/`) with JWT authentication. If offline, the event is queued locally in SQLite for retry.

---

## 3. Classification & Machine Learning Mechanics

### Q8: How does rule-based detection differ from machine learning classification in SentinelX?
**Answer:**
- **Rule-Based Detection (Deterministic):** Uses regular expressions (Luhn-verified credit cards, SSN patterns, AWS/Stripe API key structures) and explicit keyword dictionaries.
  - *Strength:* 100% precision on rigidly formatted tokens; zero false negatives when exact patterns match.
  - *Weakness:* Brittle against unstructured text, obfuscation, or contextual meaning (e.g., cannot distinguish between a financial forecast document and employee onboarding guidelines).
- **Machine Learning (Statistical):** Uses TF-IDF vectorization paired with Logistic Regression or Random Forest trained on synthetic corpus classes.
  - *Strength:* Learns topical distributions and semantic token co-occurrence (e.g., detects confidential payroll memos or customer lists even without specific credit card numbers).
  - *Weakness:* Probabilistic; can produce false positives on benign technical documentation.

### Q9: How do Logistic Regression and Random Forest work in this project?
**Answer:**
- **Logistic Regression (`backend/ml/classifier.py`):** A linear classifier that applies a sigmoid function to the dot product of feature weights and TF-IDF term vectors. It outputs calibrated class probabilities. It is computationally lightweight, has an empirical inference latency of **0.017 ms**, and serves as a fast primary baseline.
- **Random Forest (`backend/ml/classifier.py`):** An ensemble of 100 decision trees trained with bagging (bootstrap aggregation) and random feature subspace splitting. It captures non-linear relationships and interactions between rare sensitive terms. In Phase 9 benchmarks, it achieved high stability with an average inference latency of **0.166 ms**.

### Q10: What role does TF-IDF play in text vectorization?
**Answer:**
**TF-IDF (Term Frequency-Inverse Document Frequency)** transforms raw variable-length text strings into dense numerical feature vectors:
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log\left(\frac{N}{|\{d \in D : t \in d\}|}\right)$$
- **Term Frequency ($\text{TF}$):** Measures how frequently token $t$ appears in document $d$.
- **Inverse Document Frequency ($\text{IDF}$):** Penalizes ubiquitous stop words (e.g., "the", "file", "system") and amplifies rare, discriminative tokens (e.g., "confidential", "salary", "ssn", "stripe_sk", "pan_card").
Our pipeline uses `TfidfVectorizer(max_features=5000, ngram_range=(1, 2))` to extract both single words and two-word phrases.

### Q11: How does the SentinelX Hybrid classification approach work?
**Answer:**
The **Hybrid Engine** (`agent/hybrid_classifier.py`) unifies rule-based and ML outputs using an evidence-weighted aggregation algorithm:
1. Both the Rule-Based engine and the ML model inspect the document in parallel.
2. If high-confidence deterministic patterns match (e.g., a valid credit card matching the Luhn algorithm or an API key regex), the rule-based result is given primary precedence, overriding potential ML false negatives.
3. If no deterministic patterns match, the ML model's predicted class probability is evaluated. If probability $> 0.60$, the document is classified as sensitive.
4. If both engines agree, the confidence score is boosted:
   $$\text{Confidence}_{\text{hybrid}} = \min(1.0, \max(C_{\text{rule}}, C_{\text{ml}}) + 0.10)$$
This hybrid synergy yields high recall while maintaining enterprise-grade explainability.

---

## 4. Risk Assessment & Policy Enforcement

### Q12: How is the Risk Score calculated?
**Answer:**
The risk engine (`agent/risk_engine.py` / `backend/policy/engine.py`) calculates a normalized risk score between `0.0` and `1.0` using an 8-factor weighted linear combination:
$$\text{Risk} = \sum_{i=1}^{8} w_i \cdot F_i$$
Where weights sum to $1.0$:
1. **$F_1$ Sensitivity Weight ($w_1 = 0.25$):** Categorical severity (Payment Card = 1.0, Credentials = 0.95, PII = 0.85, Internal = 0.50).
2. **$F_2$ Confidence Score ($w_2 = 0.15$):** Classification certainty from the Hybrid Engine ($0.0 - 1.0$).
3. **$F_3$ Channel Severity ($w_3 = 0.15$):** Exfiltration vector risk (USB Removable Drive = 0.90, Cloud Upload = 0.85, Clipboard = 0.60, Local NAS = 0.30).
4. **$F_4$ Destination Risk ($w_4 = 0.10$):** Known external untrusted domain/IP ($0.90$) vs. internal corporate subnet ($0.10$).
5. **$F_5$ Transfer Volume ($w_5 = 0.10$):** Logarithmic scale based on file size or batch record count ($>10\text{MB}$ or $>1000$ records = $0.90$).
6. **$F_6$ Off-Hours Multiplier ($w_6 = 0.05$):** Operations between 8:00 PM and 6:00 AM or on weekends ($0.80$) vs. working hours ($0.20$).
7. **$F_7$ User Risk Tier ($w_7 = 0.05$):** Privileged executive = 0.80 (high blast radius), standard employee = 0.40, contractor = 0.70.
8. **$F_8$ Historical Violation Rate ($w_8 = 0.05$):** Frequency of policy alerts triggered by this user/device in the past 30 days.

### Q13: What distinguishes ALLOW, HOLD, and BLOCK dispositions?
**Answer:**
- **`ALLOW` (Risk $< 0.35$):** Routine business activity. File transfer proceeds unhindered. Event is silently logged in the telemetry store for audit compliance.
- **`HOLD` ($0.35 \le \text{Risk} \le 0.70$):** Ambiguous or medium-risk operation (e.g., employee copying non-critical PII to a company USB drive during business hours).
  - *Mechanism:* The source file is safely moved into encrypted local isolation quarantine (`.quarantine/<uuid>.dat`). An event with status `PENDING` is broadcast to the SOC Dashboard via WebSocket. The transfer cannot complete until an administrator explicitly issues an approval.
- **`BLOCK` (Risk $> 0.70$):** Critical exfiltration attempt (e.g., mass payment records copied to personal USB at 2:00 AM).
  - *Mechanism:* The file transfer is forcibly severed/quarantined immediately. The incident is permanently logged as `BLOCKED`, and high-priority visual alerts are flashed to the administrator.

### Q14: How does the Administrator Approval workflow operate?
**Answer:**
1. When an operation receives a `HOLD` verdict, the agent generates an `ApprovalRequest` record on the backend with status `PENDING`.
2. The React SOC dashboard displays the item in the **Approvals** screen with details: User, File Name, Sensitivity Class, Risk Score, and Destination.
3. A SOC Analyst reviews the context and clicks either **Approve** or **Deny** (with optional review notes).
4. The backend updates the event status to `APPROVED` or `DENIED` and pushes the decision over WebSocket directly to the originating agent.
5. If **Approved**, the agent restores the file from quarantine to the intended destination. If **Denied**, the file is permanently purged or preserved in quarantine, and an immutable audit entry is written.

### Q15: How are security events stored and audited?
**Answer:**
Events are stored in relational tables managed by SQLAlchemy:
- `events`: Contains timestamp, device_id, file_path, file_hash (SHA-256), classification category, risk score, decision, channel, and status.
- `audit_logs`: Tracks administrative actions (user login, approval decisions, policy rule updates, device registrations). Every entry records admin username, IP address, timestamp, action type, and JSON metadata changes.

---

## 5. Distributed Networking & Implementation Validation

### Q16: How do the two laptops communicate in a distributed deployment?
**Answer:**
- **Physical Layout:** Laptop 1 acts as the **Protected Endpoint** (running the Agent daemon). Laptop 2 acts as the **Central Management Server** (running FastAPI on port 8000 and React Dashboard on port 5173).
- **Network Protocol:**
  - Standard REST over HTTP/JSON for registration, telemetry reporting, and heartbeat checks.
  - Full-duplex WebSocket (`ws://<server-ip>:8000/api/v1/ws/alerts`) for real-time policy updates and approval decision push notifications.
- **Authentication:** All agent-to-server HTTP calls include a Bearer API Token or JWT header issued during initial device enrollment.

### Q17: How was the system tested and validated?
**Answer:**
The project was tested using a four-tier automated testing strategy:
1. **Unit Tests (`pytest`):** Individual verifications of regex engines, Luhn validation, TF-IDF vectorizers, risk scoring formulas, and JWT helpers.
2. **API & Route Tests:** FastAPI `TestClient` tests exercising every endpoint (authentication, event ingestion, approvals, audit logs, policy CRUD).
3. **Agent Integration Tests:** Mocked filesystem, USB, and clipboard events verifying quarantine moves and recovery.
4. **End-to-End System Tests:** 4 full integration tests in `backend/tests/test_system_validation.py` executing complete workflows (Allow, Hold, Deny, Block).
- **Result:** **176 tests executed, 176 passed (100% pass rate, 0 failures)**.

### Q18: Which evaluation metrics were used in Phase 9 and why?
**Answer:**
We evaluated the models using 5 standard statistical classification metrics:
1. **Accuracy:** $\frac{\text{TP} + \text{TN}}{\text{Total}}$ — overall correctness across balanced test samples.
2. **Precision:** $\frac{\text{TP}}{\text{TP} + \text{FP}}$ — measures protection against false alarms (crucial so employees aren't blocked needlessly).
3. **Recall (Sensitivity):** $\frac{\text{TP}}{\text{TP} + \text{FN}}$ — measures leak detection coverage (critical so sensitive data isn't missed).
4. **F1-Score:** $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$ — harmonic mean balancing precision and recall.
5. **Inference Latency (ms):** Wall-clock execution time per document classification (ensures endpoint responsiveness).

---

## 6. Empirical Findings & Defense Questions

### Q19: What did the actual Phase 9 experimental evaluation show?
**Answer:**
On our standardized 600-sample synthetic benchmark dataset (420 train, 180 test across 12 diverse categories):
- **Rule-Based:** Accuracy = **78.33%**, Precision = **71.43%**, Recall = **94.44%**, F1 = **0.8134**, Latency = **0.024 ms**.
- **Logistic Regression:** Accuracy = **100.0%**, Precision = **100.0%**, Recall = **100.0%**, F1 = **1.0000**, Latency = **0.017 ms**.
- **Random Forest:** Accuracy = **100.0%**, Precision = **100.0%**, Recall = **100.0%**, F1 = **1.0000**, Latency = **0.166 ms**.
- **SentinelX Hybrid:** Accuracy = **81.67%**, Precision = **77.67%**, Recall = **88.89%**, F1 = **0.8290**, Latency = **33.61 ms** (includes full regex extraction + model scoring).

*Key Finding:* ML models achieve near-perfect discrimination on clean text, but the Hybrid engine offers robust defense-in-depth by guaranteeing that known structured token sequences (API keys, Credit Cards) trigger immediate alerts regardless of document formatting.

### Q20: What are the primary causes of false positives and false negatives in your system?
**Answer:**
- **False Positives (Benign text flagged as sensitive):**
  - High-frequency numerical files: IP access logs, sensor readings, or software version matrices matching the generic length of credit cards or SSNs.
  - Source code comments containing words like "password", "token", or "secret" in documentation contexts.
- **False Negatives (Sensitive text missed):**
  - Obfuscation techniques: Users splitting credit card digits with random punctuation, base64 encoding payloads, or compressing files into password-protected archives before exfiltration.
  - Image-based exfiltration: Screenshots of confidential documents (since current agent does not perform real-time OCR).

### Q21: What are the current architectural limitations of SentinelX?
**Answer:**
1. **User-Space Operation:** The agent uses Python `watchdog` rather than a Windows Kernel Minifilter driver (`fltmgr.sys`). A user with local Administrator privileges can terminate the Python process.
2. **Post-Event Quarantine:** On file system saves, the file is written to disk before being intercepted and moved to quarantine within milliseconds. True kernel-level DLP intercepts `IRP_MJ_CREATE` and denies I/O before the block hits physical storage.
3. **No Embedded OCR:** Text inside PNG, JPEG, or scanned PDFs is not inspected.
4. **Transport Layer Inspection:** The agent monitors filesystem writes to browser download/upload paths, but does not perform TLS Man-in-the-Middle decryption on outgoing HTTPS network streams.

### Q22: What specific improvements would be prioritized in future work?
**Answer:**
1. **Kernel-Level Minifilter Driver (C/C++):** Develop a Windows Kernel File System Minifilter driver and Linux eBPF probes for tamper-proof, zero-latency I/O prevention.
2. **On-Device Optical Character Recognition (OCR):** Integrate a lightweight Tesseract or PaddleOCR pipeline to inspect image attachments and screenshots.
3. **Enterprise Directory Integration:** Bind user tiers directly to Microsoft Active Directory / LDAP groups.
4. **Automated End-to-End Encryption:** Rather than quarantining to local folders, automatically encrypt files with public-key cryptography if transfer policies are violated.
