# SentinelX — Demo Guide

> A full demonstration script will be created in Phase 10.

## Phase 0 Demo Steps

1. **Start the backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Verify API documentation**
   - Open `http://localhost:8000/docs` in a browser

3. **Test health endpoint**
   - Open `http://localhost:8000/api/v1/health`

4. **Start the frontend**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Navigate the dashboard**
   - Open `http://localhost:5173`
   - Visit the System Health page to see live backend status

6. **Start the agent**
   ```bash
   cd agent
   python -m sentinel_agent
   ```
   - Observe startup banner and configuration display
   - Press Ctrl+C for clean shutdown
