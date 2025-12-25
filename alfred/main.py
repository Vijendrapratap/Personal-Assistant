import os
import sys

# Ensure module path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from alfred.config import get_llm_provider
from alfred.core.butler import Alfred
from alfred.infrastructure.storage.postgres_db import PostgresAdapter
from alfred.api import auth

app = FastAPI(title="Alfred - The Digital Butler")

# --- Composition Root ---
# 1. Initialize Infrastructure
try:
    llm_provider = get_llm_provider()
    
    # Check if DB_URL is set, otherwise fall back to in-memory (None)
    db_url = os.getenv("DATABASE_URL")
    storage_provider = PostgresAdapter(db_url) if db_url else None
    
    # 2. Initialize Core
    alfred = Alfred(brain=llm_provider, storage=storage_provider)
    print(f"Alfred initialized with Brain: {type(llm_provider).__name__}, Storage: {type(storage_provider).__name__}")

    # Include Auth Router
    app.include_router(auth.router)

except Exception as e:
    print(f"CRITICAL ERROR Initializing Alfred: {e}")
    # In production we might exit, but here we can allow app to run with limited functionality or just raising
    raise e

# --- API Layer ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user_id: str = Depends(auth.get_current_user)):
    try:
        response_text = alfred.ask(req.message, current_user_id)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "online", "brain": type(llm_provider).__name__}
