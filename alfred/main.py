import os
import sys

# Ensure module path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load env vars
load_dotenv()

from alfred.config import get_llm_provider
from alfred.core.butler import Alfred
from alfred.infrastructure.storage.postgres_db import PostgresAdapter

# Global references for dependency injection
llm_provider = None
storage_provider = None
alfred = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global llm_provider, storage_provider, alfred

    # Startup
    try:
        llm_provider = get_llm_provider()

        # Check if DB_URL is set, otherwise fall back to in-memory (None)
        db_url = os.getenv("DATABASE_URL")
        storage_provider = PostgresAdapter(db_url) if db_url else None

        # Initialize Core
        alfred = Alfred(brain=llm_provider, storage=storage_provider)
        print(f"Alfred initialized with Brain: {type(llm_provider).__name__}, Storage: {type(storage_provider).__name__ if storage_provider else 'None'}")

    except Exception as e:
        print(f"CRITICAL ERROR Initializing Alfred: {e}")
        raise e

    yield

    # Shutdown
    print("Alfred shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Alfred - The Digital Butler",
    description="A proactive, intelligent personal assistant that manages your time, tasks, and habits.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for mobile/web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from alfred.api import auth, projects, tasks, habits, dashboard, notifications

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(habits.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)


# --- API Layer ---
class ChatRequest(BaseModel):
    message: str
    context: dict = None  # Optional additional context


class ChatResponse(BaseModel):
    response: str
    metadata: dict = None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user_id: str = Depends(auth.get_current_user)):
    """Chat with Alfred."""
    global alfred
    if not alfred:
        raise HTTPException(status_code=503, detail="Alfred not initialized")

    try:
        response_text = alfred.ask(req.message, current_user_id)
        return ChatResponse(response=response_text, metadata={})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "online",
        "brain": type(llm_provider).__name__ if llm_provider else "Not initialized",
        "storage": type(storage_provider).__name__ if storage_provider else "Not initialized"
    }


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Alfred - The Digital Butler",
        "version": "2.0.0",
        "description": "Your proactive personal assistant",
        "endpoints": {
            "auth": "/auth",
            "chat": "/chat",
            "projects": "/projects",
            "tasks": "/tasks",
            "habits": "/habits",
            "dashboard": "/dashboard",
            "notifications": "/notifications"
        }
    }


# Run with: uvicorn alfred.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
