# SmartAutomation Desktop-style UI preview

The project uses React + TypeScript, Vite, and the assistant-ui dependency. The initial UI is a desktop-style **prototype**, not an assistant-ui chat runtime and not a live UFO controller. Assistant-ui primitives will be wired after job lifecycle, independent result verification, and safe cancellation are implemented.

## Run locally (Windows)

From the **SmartAutomation root folder**:

```powershell
# Terminal 1 - FastAPI status-only backend
.\.venv\Scripts\python.exe -m uvicorn smartautomation.api:app --host 127.0.0.1 --port 8765

# Terminal 2 - frontend
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 in a browser. Node.js 22 or newer is recommended.

The UI is **not yet connected to actual UFO execution**: submitting a chat message only shows a non-executing acknowledgment. Buttons for starting/stopping desktop tasks are not active; this is intentional and cannot be bypassed with a UI-only change.

This UI does not upload API keys or screenshots. The API is localhost-only and read-only. Keep agents.yaml, API keys, task logs and local files out of GitHub.
