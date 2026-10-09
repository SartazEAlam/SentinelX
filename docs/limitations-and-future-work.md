# SentinelX: Limitations and Future Work

**Document Version:** 1.0.0 (Final Delivery)  
**Classification:** Academic / Architectural Evaluation  

---

## 1. Overview

An honest, transparent appraisal of system boundaries is a core tenet of research-grade software engineering. While SentinelX successfully achieves real-time data loss detection, multi-factor risk scoring, hybrid classification, and policy enforcement across Windows endpoints, specific architectural and environmental limitations exist in the current implementation.

---

## 2. Technical Limitations

### 2.1 User-Space Monitoring vs. Kernel Minifilter Driver
- **Current Architecture:** The SentinelX endpoint agent operates in Windows user space as a background service leveraging the Windows filesystem notification subsystem (`watchdog` / `ReadDirectoryChangesW`).
- **Limitation:** User-space file monitoring operates on post-creation or modification notifications. While the `EnforcementManager` intercepts and deletes or isolates unauthorized files within milliseconds, it does not hold a kernel-level I/O request packet (IRP) in suspended state before initial sector write.
- **Comparison:** Commercial enterprise DLP solutions (e.g., Symantec DLP, Trellix) employ proprietary Windows Kernel Minifilter Drivers (`fltMgr.sys`) executing in Ring 0.

### 2.2 Synthetic Dataset Scope
- **Current Architecture:** Evaluated on a 600-sample balanced synthetic corpus covering 12 representative categories with edge cases.
- **Limitation:** Synthetic data, while strictly compliant with privacy regulations and reproducible, exhibits less noise, compression variation, and encoding artifacts than live corporate network traffic.

### 2.3 File Type & Multimodal Inspection Boundaries
- **Current Architecture:** High-speed extraction for plain text, source code, JSON, YAML, environment variables, logs, and structured CSV tables.
- **Limitation:** Embedded images within complex PDF files, scanned document photos, and steganographic data are not inspected. Optical Character Recognition (OCR) was intentionally excluded to maintain a lightweight endpoint memory footprint (<230 MB peak).

### 2.4 Scalability Architecture (Cluster Testing)
- **Current Architecture:** Single FastAPI server instance paired with SQLite / single PostgreSQL node, verified across local and two-laptop environments.
- **Limitation:** Fleet management was validated with up to dozens of concurrent simulated events rather than tens of thousands of simultaneous enterprise endpoints. Enterprise scale-out would require distributed messaging layers.

---

## 3. Future Work Roadmap

### Phase 10+: Planned Architectural Enhancements

1. **Windows Kernel Minifilter Driver (Ring 0):**
   - Develop a signed kernel driver to intercept `IRP_MJ_CREATE` and `IRP_MJ_WRITE` system calls, enabling true pre-write blocking before data touches the physical disk surface.
2. **Local Lightweight Neural Embeddings:**
   - Integrate an ONNX-runtime quantified transformer model (e.g., MiniLM or DeBERTa) to perform semantic vector embeddings locally on endpoints without cloud roundtrips.
3. **Cross-Platform Agent Support:**
   - Extend agent collectors to macOS using the native `EndpointSecurity` API.
   - Extend agent collectors to Linux using `eBPF` (Extended Berkeley Packet Filter) probes.
4. **OCR & Multimodal Inspection Pipeline:**
   - Implement optional asynchronous OCR extraction for scanned PDF forms and screenshots using an offloaded background worker.
5. **Distributed Ingestion Infrastructure:**
   - Incorporate Apache Kafka or RabbitMQ between the ingestion tier and risk processing services for massive concurrent throughput.
