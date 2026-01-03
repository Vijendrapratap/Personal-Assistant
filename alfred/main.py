import os
import sys

# Ensure module path alignment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load env vars
load_dotenv()

from alfred.config import get_llm_provider
from alfred.core.butler import Alfred
from alfred.infrastructure.storage.postgres_db import PostgresAdapter
from alfred.core.proactive_engine import ProactiveEngine
from alfred.infrastructure.notifications.expo_push import ExpoPushService
from alfred.infrastructure.scheduler.scheduler import get_scheduler

# Global references for dependency injection
llm_provider = None
storage_provider = None
alfred = None
proactive_engine = None
push_service = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global llm_provider, storage_provider, alfred, proactive_engine, push_service, scheduler

    # Startup
    try:
        llm_provider = get_llm_provider()

        # Check if DB_URL is set, otherwise fall back to in-memory (None)
        db_url = os.getenv("DATABASE_URL")
        storage_provider = PostgresAdapter(db_url) if db_url else None

        # Initialize Core
        alfred = Alfred(brain=llm_provider, storage=storage_provider)
        print(f"Alfred initialized with Brain: {type(llm_provider).__name__}, Storage: {type(storage_provider).__name__ if storage_provider else 'None'}")

        # Initialize proactive components
        if storage_provider:
            proactive_engine = ProactiveEngine(storage=storage_provider, llm=llm_provider)
            push_service = ExpoPushService()

            # Initialize and start the scheduler
            scheduler = get_scheduler()
            if scheduler.initialize(
                storage=storage_provider,
                proactive_engine=proactive_engine,
                push_service=push_service
            ):
                scheduler.start()
                print("Alfred Scheduler started with proactive intelligence")
            else:
                print("Warning: Scheduler could not be initialized (APScheduler may not be installed)")

    except Exception as e:
        print(f"CRITICAL ERROR Initializing Alfred: {e}")
        raise e

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown()
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
from alfred.api import auth, projects, tasks, habits, dashboard, notifications, proactive, knowledge, voice

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(habits.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(proactive.router)
app.include_router(knowledge.router)
app.include_router(voice.router)


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


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, current_user_id: str = Depends(auth.get_current_user)):
    """
    Stream chat response with thinking steps for transparency.
    Uses Server-Sent Events (SSE) to stream progress in real-time.
    """
    global alfred

    if not alfred:
        raise HTTPException(status_code=503, detail="Alfred not initialized")

    async def generate_stream():
        try:
            # Stream thinking steps
            thinking_steps = [
                {"step": "Understanding your request", "status": "in_progress"},
                {"step": "Analyzing context", "status": "pending"},
                {"step": "Formulating response", "status": "pending"},
            ]

            # Step 1: Understanding
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[0]})}\n\n"
            await asyncio.sleep(0.3)
            thinking_steps[0]["status"] = "completed"
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[0]})}\n\n"

            # Step 2: Analyzing
            thinking_steps[1]["status"] = "in_progress"
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[1]})}\n\n"
            await asyncio.sleep(0.3)
            thinking_steps[1]["status"] = "completed"
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[1]})}\n\n"

            # Step 3: Formulating
            thinking_steps[2]["status"] = "in_progress"
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[2]})}\n\n"

            # Get actual response
            response_text = alfred.ask(req.message, current_user_id)

            thinking_steps[2]["status"] = "completed"
            yield f"data: {json.dumps({'type': 'thinking', 'step': thinking_steps[2]})}\n\n"

            # Stream the response
            yield f"data: {json.dumps({'type': 'response', 'content': response_text})}\n\n"

            # Signal completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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
            "chat_stream": "/chat/stream",
            "projects": "/projects",
            "tasks": "/tasks",
            "habits": "/habits",
            "dashboard": "/dashboard",
            "notifications": "/notifications",
            "proactive": "/proactive",
            "knowledge": "/knowledge",
            "voice": "/voice"
        }
    }


# Run with: uvicorn alfred.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
