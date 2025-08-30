
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="Agent Swarm Dashboard")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "Dashboard API Running", "time": datetime.now().isoformat()}

@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": [], "message": "Backend running in minimal mode"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "connection", "status": "connected"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"echo": data})
    except:
        pass

if __name__ == "__main__":
    print("Starting minimal dashboard backend on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
