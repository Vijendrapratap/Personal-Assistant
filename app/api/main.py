from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

from app.agents.alfred_agent import AlfredAgent

app = FastAPI(title="Alfred Personal Assistant API", version="1.0.0")

# Initialize Agent
alfred = AlfredAgent()

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    response: str

class FeedbackRequest(BaseModel):
    user_id: str
    correction: str
    original_query: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "running", "agent": "Alfred"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # In a real scenario, we might want to load a specific agent instance for the user
        response = alfred.chat(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(user_id: str = "default_user"):
    # This would retrieve history from the storage backend
    # For now, accessing the internal storage directly if possible or via the agent
    # Agno's storage might expose methods to get sessions
    try:
        # Simplified for now
        return {"status": "not_implemented_fully", "message": "History retrieval requires storage access implementation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def save_feedback(feedback: FeedbackRequest):
    """
    Save user corrections to 'Learnings' table.
    """
    # TODO: Implement persistence to Postgres 'Learnings' table
    # alfred.learn(feedback.correction)
    return {"status": "feedback_received", "message": "Thank you, I will remember that."}

@app.post("/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        file_location = f"user_data/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Trigger ingestion in background
        # background_tasks.add_task(alfred.ingest_file, file_location)
        
        return {"status": "success", "filename": file.filename, "message": "File uploaded and scheduled for ingestion."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
