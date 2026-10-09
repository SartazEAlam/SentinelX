# SentinelX: System Architecture & Design Specification

**Document Version:** 1.0.0 (Final Delivery)  
**Classification:** Technical Documentation / Architectural Specification  

---

## 1. System Overview

SentinelX is an intelligent, enterprise-grade Data Loss Prevention (DLP) and Exfiltration Detection system designed to safeguard organizational data across Windows endpoints. It utilizes a distributed client-server architecture combining real-time filesystem and removable media monitoring, hybrid sensitive data classification (deterministic rules + TF-IDF machine learning), multi-factor risk assessment, proactive policy-driven enforcement, and an administrative SOC dashboard.

---

## 2. Overall SentinelX Architecture

```mermaid
graph TB
    subgraph "Protected Endpoint (Windows 11)"
        subgraph "Monitoring & Capture"
            FS[FileSystemCollector<br/>watchdog observer]
            USB[USBCollector<br/>WMI / PyWin32]
        end

        subgraph "Agent Pipeline"
            Norm[EventNormalizer<br/>Hashing & Metadata]
            Dedup[EventDeduplicator<br/>Sliding Window]
            Queue[EventQueue<br/>Async Priority Queue]
            Disp[EventDispatcher<br/>Batching & Transport]
        end

        subgraph "Local Intelligence & Enforcement"
            Engine[ClassificationEngine<br/>Rules + ML Classifier]
            Enforce[EnforcementManager<br/>BlockHandler & Quarantine]
            Store[(Local SQLite Store<br/>Offline Event Cache)]
        end
    end

    subgraph "Network Transport"
        HTTP[HTTP REST API<br/>JWT Bearer Auth]
        WS[WebSocket / SSE<br/>Real-Time Telemetry]
    end

    subgraph "SentinelX Central Server (FastAPI)"
        subgraph "API Ingestion & Controllers"
            Router[FastAPI Route Handlers<br/>/api/v1/events, /api/v1/devices]
            Auth[Auth & Token Service<br/>RBAC & Security]
        end

        subgraph "Decision Engine"
            Risk[RiskEngine<br/>8-Factor Clamped Scoring]
            Policy[PolicyEngine<br/>Priority-Ordered Rules]
        end

        subgraph "Data & Audit Layer"
            DB[(Central Database<br/>SQLite / PostgreSQL)]
            Audit[AuditLogger<br/>Immutable Activity Log]
        end
    end

    subgraph "SOC Administrator Interface (React + Vite)"
        UI[Administrator Dashboard<br/>Recharts Analytics]
        ApprUI[Approval Interface<br/>Quarantine Decisions]
        AlertUI[Real-Time Alert Feed<br/>Security Operations]
    end

    FS --> Norm
    USB --> Norm
    Norm --> Engine
    Engine --> Norm
    Norm --> Dedup
    Dedup --> Queue
    Queue --> Disp
    Disp --> Store
    Disp --> HTTP
    Enforce -.-> FS
    Enforce -.-> USB

    HTTP --> Router
    Router --> Auth
    Router --> Risk
    Risk --> Policy
    Policy --> Router
    Router --> DB
    Router --> Audit
    Router --> WS

    WS --> UI
    WS --> AlertUI
    UI --> Router
    ApprUI --> Router
```

---

## 3. Endpoint Monitoring Workflow

The endpoint monitoring subsystem operates concurrently using `watchdog` for filesystem events and polling/WMI for USB removable media.

```mermaid
sequenceDiagram
    autonumber
    actor User as Endpoint User / Process
    participant FS as FileSystemCollector
    participant Norm as EventNormalizer
    participant Engine as ClassificationEngine
    participant Enforce as EnforcementManager
    participant Queue as EventQueue

    User->>FS: File Created / Modified / Moved (e.g., in C:/tmp/protected)
    FS->>Norm: Raw Event (Path, Action, Timestamp)
    Norm->>Norm: Calculate SHA-256 Hash & File Size
    Norm->>Engine: Inspect Content (Text/CSV Extraction)
    Engine-->>Norm: ClassificationResult (Level, Categories, Confidence)
    Norm->>Norm: Normalize to Canonical Event Schema
    alt Event matches BLOCK or HOLD policy
        Norm->>Enforce: Check Staging / Action Required
        Enforce->>Enforce: Stage to C:/tmp/sentinelx_staging
    end
    Norm->>Queue: Enqueue Normalized Event
    Queue-->>FS: Acknowledge Buffer Acceptance
```

---

## 4. Sensitive-Data Classification Workflow

SentinelX utilizes a **Hybrid Classification Pipeline** where deterministic rules evaluate high-entropy patterns (regex, keywords, headers) and a machine-learning model (TF-IDF vectorizer + Logistic Regression / Random Forest) provides semantic context scoring.

```mermaid
flowchart TD
    Start([Inspect File / Content]) --> Extractor[Text & CSV Content Extractors]
    Extractor --> TextCtx[Construct Classification Context<br/>Filename, Ext, Plaintext, Headers]
    
    TextCtx --> RuleEval[Rule Evaluation Engine]
    TextCtx --> MLEval[ML Model Predictor]
    
    subgraph "Deterministic Rules"
        RuleEval --> R1[Regex Matchers<br/>Cards, Emails, Secrets]
        RuleEval --> R2[Keyword Matchers<br/>Confidential, Salary, Password]
        RuleEval --> R3[Extension & Column Matchers<br/>.env, .pem, SSN, Payroll]
    end

    subgraph "Machine Learning Intelligence"
        MLEval --> Vec[TF-IDF Vectorizer<br/>1-2 N-Grams, 2000 Features]
        Vec --> Model[Classifier Model<br/>Logistic Regression / Random Forest]
        Model --> MLProb[Class Probability Score]
    end

    R1 & R2 & R3 --> Aggregation[Aggregation Engine _aggregate]
    MLProb --> Aggregation

    Aggregation --> CheckConf{Rules Triggered?}
    CheckConf -- Yes --> Boost[Corroborate Sources & Calculate Confidence]
    CheckConf -- No --> TrustML{ML Confident?}
    TrustML -- Yes --> AssignML[Assign Level based on ML Probability]
    TrustML -- No --> Unknown[Classify as UNKNOWN / PUBLIC]
    
    Boost --> Output([ClassificationResult<br/>Level, Categories, Evidence, Confidence])
    AssignML --> Output
    Unknown --> Output
```

---

## 5. Risk Assessment & Policy Decision Workflow

Risk assessment is decoupled from policy enforcement: the Risk Engine calculates objective threat scores ($0 \le \text{Score} \le 100$), and the Policy Engine determines the enforcement action (`ALLOW`, `HOLD`, `BLOCK`).

```mermaid
flowchart LR
    subgraph "Input Context"
        C1[Sensitivity Level & Categories]
        C2[Action Type: READ, COPY, UPLOAD, USB]
        C3[Destination: LOCAL, CLOUD, USB]
        C4[User Context: Role, Trust]
        C5[Device Context: Compliance, Trust]
        C6[Behavior: Frequency, Velocity]
        C7[Time Context: Business vs Off-Hours]
        C8[Volume: File Size, Cumulative Bytes]
    end

    subgraph "Risk Engine (Formula)"
        C1 & C2 & C3 & C4 & C5 & C6 & C7 & C8 --> WeightedSum["Score = Σ (Factor_i × Weight_i)<br/>Weights sum to 1.0<br/>Clamped [0, 100]"]
        WeightedSum --> Banding{Risk Level Banding}
        Banding -->|0 - 29| Low[LOW]
        Banding -->|30 - 69| Med[MEDIUM]
        Banding -->|70 - 100| High[HIGH]
    end

    subgraph "Policy Engine"
        Low & Med & High --> PolCheck[Evaluate Enabled Rules by Priority]
        PolCheck --> ActionChoice{Rule or Default Match}
        ActionChoice -->|Score < 30| ALLOW[ALLOW: Proceed and Log]
        ActionChoice -->|30 <= Score < 70| HOLD[HOLD: Quarantine & Request Approval]
        ActionChoice -->|Score >= 70| BLOCK[BLOCK: Terminate & Trigger Alert]
    end
```

---

## 6. ALLOW, HOLD, and BLOCK Enforcement Flow

```mermaid
stateDiagram-v2
    [*] --> EventDetected
    EventDetected --> Classification: Extract Content
    Classification --> RiskEvaluation: Calculate Threat Score
    RiskEvaluation --> PolicyDecision: Evaluate Rules

    state PolicyDecision {
        [*] --> CheckDecision
        CheckDecision --> ALLOW_State: Score < 30
        CheckDecision --> HOLD_State: 30 <= Score < 70
        CheckDecision --> BLOCK_State: Score >= 70
    }

    ALLOW_State --> NormalExecution: Operation Permitted
    NormalExecution --> LogAudit: Write to Central Event Log

    HOLD_State --> StageQuarantine: Isolate to Staging Directory
    StageQuarantine --> AwaitReview: Create Approval Record
    AwaitReview --> AdminApproved: SOC Analyst Grants
    AwaitReview --> AdminDenied: SOC Analyst Denies
    AwaitReview --> TimeoutDenied: Timeout (Default 5 min)
    AdminApproved --> ReleaseStaging: Move to Destination
    AdminDenied --> PurgeStaging: Permanently Delete
    TimeoutDenied --> PurgeStaging: Permanently Delete

    BLOCK_State --> KillOperation: Delete File / Intercept Stream
    KillOperation --> TriggerIncident: Generate Critical Alert
    TriggerIncident --> LogAudit: Immutable Audit Record

    LogAudit --> [*]
    ReleaseStaging --> [*]
    PurgeStaging --> [*]
```

---

## 7. Two-Laptop Communication Architecture

SentinelX is tested across a dual-laptop topology representing a real enterprise network:

```mermaid
graph LR
    subgraph "Laptop 1: Protected Endpoint"
        AgentDaemon[SentinelX Endpoint Agent Daemon]
        Watchdog[Watchdog Observer]
        LocalStaging[C:/tmp/sentinelx_staging]
        AgentStore[(event_store.db)]
    end

    subgraph "Enterprise Network (LAN / Wi-Fi)"
        REST[HTTP REST Ingestion /api/v1/events<br/>JWT Bearer Auth ~2-5 ms]
        SSE[SSE / WebSocket Event Bus<br/>Live Notification ~85 ms]
    end

    subgraph "Laptop 2: Central Server & SOC Dashboard"
        Backend[FastAPI Server :8000]
        Postgres[(SQLite / PostgreSQL DB)]
        Frontend[React Vite Dashboard :5173]
    end

    Watchdog --> AgentDaemon
    AgentDaemon --> LocalStaging
    AgentDaemon --> AgentStore
    AgentDaemon -->|Batch POST Events| REST
    REST --> Backend
    Backend --> Postgres
    Backend --> SSE
    SSE --> Frontend
    Frontend -->|Admin Approve/Reject| Backend
    Backend -->|Approval Disposition| AgentDaemon
```

---

## 8. Database and Dashboard Data Flow

```mermaid
flowchart TD
    subgraph "Database Entities (SQLAlchemy ORM)"
        Users[(users)]
        Devices[(devices)]
        Events[(events)]
        Assessments[(risk_assessments)]
        Approvals[(approvals)]
        Alerts[(alerts)]
        AuditLogs[(audit_logs)]
    end

    subgraph "Backend Services"
        AuthSvc[AuthService]
        EventSvc[EventIngestionService]
        RiskSvc[RiskAssessmentService]
        PolicySvc[PolicyService]
        ApprSvc[ApprovalService]
        AlertSvc[AlertService]
    end

    subgraph "Dashboard Views"
        V_Dash[SOC Dashboard Home]
        V_Events[Event Explorer]
        V_Appr[Approval Queue]
        V_Alerts[Alert Manager]
        V_Devices[Device Fleet]
        V_Audit[Audit Log Inspector]
    end

    EventSvc --> Events & Assessments
    RiskSvc --> Assessments
    ApprSvc --> Approvals
    AlertSvc --> Alerts
    AuthSvc --> Users
    PolicySvc --> AuditLogs

    Events & Assessments --> V_Events
    Approvals --> V_Appr
    Alerts --> V_Alerts
    Devices --> V_Devices
    AuditLogs --> V_Audit
    Events & Alerts & Devices --> V_Dash
```

---

## 9. Administrator Approval Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as SOC Security Analyst
    participant UI as Admin Dashboard (React)
    participant API as FastAPI Backend (/api/v1/approvals)
    participant DB as Central Database
    participant Agent as Endpoint Agent (EnforcementManager)
    participant Staging as Local Quarantine Folder

    Agent->>API: Ingest Event (Decision: HOLD)
    API->>DB: Persist Event & Create Approval (Status: PENDING)
    API-->>UI: Real-Time WebSocket / SSE Broadcast
    UI->>Analyst: Display Approval Modal (Reason, User, File, Risk Score)

    alt Analyst Approves
        Analyst->>UI: Click "Approve" (with justification comment)
        UI->>API: POST /api/v1/approvals/{id}/approve
        API->>DB: Update Status = APPROVED, Record Reviewer & Timestamp
        API-->>Agent: Dispatch Disposition: APPROVED
        Agent->>Staging: Release File from Quarantine to Destination
        Agent->>API: Confirm Operation Released
    else Analyst Rejects
        Analyst->>UI: Click "Reject" (with reason comment)
        UI->>API: POST /api/v1/approvals/{id}/reject
        API->>DB: Update Status = REJECTED
        API-->>Agent: Dispatch Disposition: REJECTED
        Agent->>Staging: Securely Delete Quarantined Payload
    end
```

---

## 10. Phase 9 Evaluation Methodology

The scientific evaluation architecture follows a strict reproducible pipeline:

```mermaid
flowchart TD
    Gen[dataset/generator.py<br/>Deterministic Seed 42] --> Data[(dataset/synthetic_data.json<br/>600 Samples: 300 Sensitive / 300 Benign)]
    Data --> Loader[scripts/data_loader.py<br/>Stratified 70/30 Train-Test Split]
    
    Loader --> TrainSet[420 Training Samples<br/>210 Sensitive / 210 Benign]
    Loader --> TestSet[180 Unseen Test Samples<br/>90 Sensitive / 90 Benign]

    TrainSet --> TrainLR[Fit TF-IDF + Logistic Regression]
    TrainSet --> TrainRF[Fit TF-IDF + Random Forest]

    TestSet --> EvalRules[evaluate_rule_based.py]
    TestSet --> EvalLR[evaluate_logistic_regression.py]
    TestSet --> EvalRF[evaluate_random_forest.py]
    TestSet --> EvalTFIDF[evaluate_tfidf.py]
    TestSet --> EvalHybrid[evaluate_hybrid.py]

    EvalRules & EvalLR & EvalRF & EvalHybrid --> Orchestrator[run_all.py Orchestrator]
    
    subgraph "System Performance & Validation"
        Orchestrator --> EvalRisk[evaluate_risk_policy.py<br/>6 Operational Scenarios]
        Orchestrator --> EvalE2E[evaluate_end_to_end.py<br/>100 Timed Pipeline Runs]
        Orchestrator --> EvalRes[evaluate_resources.py<br/>psutil CPU/RAM/Disk Profiling]
    end

    Orchestrator --> Metrics[(results/metrics.json)]
    Orchestrator --> Errors[(results/error_analysis.json)]
    Orchestrator --> Plots[generate_plots.py]
    Plots --> Figs[docs/evaluation/*.png<br/>10 Publication Charts & Matrices]
```
