# SentinelX Phase 5: Enforcement Demonstration

This guide walks you through demonstrating the Phase 5 Enforcement capabilities.

## Setup

1. **Start the backend server:**
   ```bash
   cd d:\SentinelX\backend
   # Make sure DB is initialized (happens automatically now)
   python -m uvicorn app.main:app --reload
   ```

2. **Configure the Agent Environment**
   Open `d:\SentinelX\.env` and ensure:
   ```env
   AGENT_MONITORING_MODE=STRICT
   AGENT_PROTECTED_PATHS=C:/tmp/sentinelx_protected
   AGENT_ENFORCEMENT_ENABLED=true
   ```

3. **Start the Agent:**
   ```bash
   cd d:\SentinelX\agent
   python -m sentinel_agent.main
   ```

4. **Start the Upload Simulator (in a new terminal):**
   ```bash
   python d:\SentinelX\simulator\upload_server.py --drop-dir C:\tmp\sentinelx_upload_test
   ```

## Demo 1: Passive Blocking (The "File Drop" scenario)

We'll simulate an application attempting to write a highly sensitive file to a protected directory.

1. **Create the protected directory if it doesn't exist:**
   ```bash
   mkdir C:\tmp\sentinelx_protected
   ```

2. **Simulate a sensitive data leak:**
   We create a file containing sensitive keywords (e.g. "password", "SSN") and drop it in the protected directory.
   ```bash
   echo "Confidential: User password is 'hunter2' and SSN is 000-11-2222" > C:\tmp\sentinelx_protected\leak.txt
   ```

3. **Observe the Agent Logs:**
   - The agent detects the file creation.
   - The Local Classifier identifies it as HIGHLY_CONFIDENTIAL.
   - The event is sent to the backend Risk Engine.
   - The Risk Engine returns a **BLOCK** decision.
   - The Agent's BlockHandler kicks in and immediately **deletes** the file.
   - *Check the folder — the file should be gone!*

## Demo 2: The Upload Simulator Interception

1. **Perform a malicious upload:**
   Use curl to upload a file containing credit card data to our dummy upload server.
   *(Note: The upload server is writing to `C:\tmp\sentinelx_upload_test`. You should add this path to `AGENT_PROTECTED_PATHS` in `.env` and restart the agent!)*

   ```bash
   # Add to .env: AGENT_PROTECTED_PATHS=C:/tmp/sentinelx_protected,C:/tmp/sentinelx_upload_test
   # Restart agent
   
   # Run curl:
   curl -X POST -H "X-File-Name: cc_data.txt" --data "Here is the customer credit card list: 4532 1234 5678 9010" http://localhost:8080/upload
   ```

2. **Observe the result:**
   - The upload server receives the POST and writes the file to disk.
   - The SentinelX FileSystem collector detects the write.
   - The content is classified as HIGHLY_CONFIDENTIAL.
   - The server mandates a BLOCK.
   - SentinelX deletes the uploaded file.

## Demo 3: HOLD and Staging (Simulated)

If the server policy dictates a "HOLD" decision (e.g., for medium risk files or based on specific policies), the Agent will:
1. Copy the file into the secure staging directory (`d:\SentinelX\agent\staging`).
2. Delete the original destination write (if it was passive detection).
3. Wait for the administrator to approve via the Backend API.
4. If approved, copy from staging back to the destination.
5. If denied/expired, securely delete the staging file.

*(Note: To test this, you'd need to create a specific policy on the backend that returns HOLD for a given risk level, or temporarily change the offline fail-safe policy in `.env` to HOLD and disconnect the backend).*
