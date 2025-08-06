from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime, timezone
import uuid
from contextlib import asynccontextmanager

# Import the emergentintegrations library
from emergentintegrations.llm.openai import OpenAIChatRealtime

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.ai_assistant

# Initialize OpenAI Chat Realtime
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found, voice features will be disabled")
    chat = None
else:
    chat = OpenAIChatRealtime(api_key=OPENAI_API_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting AI Voice Assistant...")
    yield
    # Shutdown
    print("Shutting down AI Voice Assistant...")

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Assistant for Unity Development",
    description="Personal AI assistant with strong memory for game development",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ConversationMessage(BaseModel):
    id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None

class UnityProject(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    created_at: datetime
    last_modified: datetime
    scripts: List[Dict[str, Any]] = []
    status: str = "active"

class Task(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime
    due_date: Optional[datetime] = None
    project_id: Optional[str] = None

class UserMemory(BaseModel):
    id: str
    user_id: str
    key: str
    value: Any
    category: str
    created_at: datetime
    updated_at: datetime

# Register OpenAI Realtime router
router = APIRouter()
if chat:
    OpenAIChatRealtime.register_openai_realtime_router(router, chat)
    app.include_router(router, prefix="/api/v1")
else:
    print("OpenAI realtime router not registered - API key missing")

# Memory and conversation endpoints
@app.post("/api/conversations")
async def save_conversation(conversation: ConversationMessage):
    """Save a conversation to memory"""
    try:
        conversation_dict = conversation.dict()
        await db.conversations.insert_one(conversation_dict)
        return {"status": "success", "message": "Conversation saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str, limit: int = 50):
    """Get recent conversations for context"""
    try:
        conversations = await db.conversations.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unity project management
@app.post("/api/projects")
async def create_project(project: UnityProject):
    """Create a new Unity project entry"""
    try:
        project_dict = project.dict()
        await db.projects.insert_one(project_dict)
        return {"status": "success", "project": project_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{user_id}")
async def get_projects(user_id: str):
    """Get all projects for a user"""
    try:
        projects = await db.projects.find({"user_id": user_id}).to_list(100)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, update_data: Dict[str, Any]):
    """Update project details"""
    try:
        update_data["last_modified"] = datetime.now(timezone.utc)
        result = await db.projects.update_one(
            {"id": project_id},
            {"$set": update_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"status": "success", "message": "Project updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task management
@app.post("/api/tasks")
async def create_task(task: Task):
    """Create a new task"""
    try:
        task_dict = task.dict()
        await db.tasks.insert_one(task_dict)
        return {"status": "success", "task": task_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{user_id}")
async def get_tasks(user_id: str, status: Optional[str] = None):
    """Get tasks for a user, optionally filtered by status"""
    try:
        filter_dict = {"user_id": user_id}
        if status:
            filter_dict["status"] = status
        tasks = await db.tasks.find(filter_dict).sort("created_at", -1).to_list(100)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: str, update_data: Dict[str, Any]):
    """Update task status or details"""
    try:
        result = await db.tasks.update_one(
            {"id": task_id},
            {"$set": update_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Task updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User memory system
@app.post("/api/memory")
async def save_memory(memory: UserMemory):
    """Save user memory/preferences"""
    try:
        memory_dict = memory.dict()
        # Upsert based on user_id, key, and category
        await db.user_memory.update_one(
            {
                "user_id": memory.user_id,
                "key": memory.key,
                "category": memory.category
            },
            {"$set": memory_dict},
            upsert=True
        )
        return {"status": "success", "message": "Memory saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str, category: Optional[str] = None):
    """Get user memory/preferences"""
    try:
        filter_dict = {"user_id": user_id}
        if category:
            filter_dict["category"] = category
        memories = await db.user_memory.find(filter_dict).to_list(100)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unity-specific endpoints
@app.post("/api/generate-script")
async def generate_unity_script(request: Dict[str, Any]):
    """Generate Unity C# script based on requirements"""
    try:
        user_id = request.get("user_id")
        script_type = request.get("script_type")
        description = request.get("description")
        
        # Get user's coding preferences from memory
        preferences = await db.user_memory.find({
            "user_id": user_id,
            "category": "coding_preferences"
        }).to_list(10)
        
        # Here you would typically call the AI to generate the script
        # For now, return a template response
        script_template = f"""using UnityEngine;

public class {script_type} : MonoBehaviour
{{
    // {description}
    
    void Start()
    {{
        // Initialization code here
    }}
    
    void Update()
    {{
        // Update logic here
    }}
}}"""
        
        return {
            "status": "success",
            "script": script_template,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Voice Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)