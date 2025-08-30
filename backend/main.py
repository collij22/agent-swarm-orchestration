from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Task Manager API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: int = 0

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    # Task creation logic here
    return task

@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    # Task retrieval logic here
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
