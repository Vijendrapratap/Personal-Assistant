import os
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
from alfred.infrastructure.storage.sqlite_db import SQLiteAdapter
from alfred.core.proactive_engine import ProactiveEngine
from alfred.infrastructure.notifications.expo_push import ExpoPushService
from alfred.infrastructure.scheduler.scheduler import get_scheduler

# New architecture imports
from alfred.core.config_manager import get_config_manager, ConfigValidationError
from alfred.core.orchestrator import Orchestrator, OrchestratorConfig

# Global service instances
llm_provider = None
storage_provider = None
alfred = None
orchestrator = None
proactive_engine = None
push_service = None
scheduler = None
config_manager = None

# Use multi-agent orchestrator (default: true)
USE_ORCHESTRATOR = os.getenv("ALFRED_USE_ORCHESTRATOR", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global llm_provider, storage_provider, alfred, orchestrator, proactive_engine
    global push_service, scheduler, config_manager

    # Startup
    try:
        # Try new config manager first
        try:
            config_manager = get_config_manager()
            config = config_manager.get_config()
            print(f"Alfred Config: {config_manager.validate()}")
        except ConfigValidationError as e:
            print(f"Config validation failed: {e}")
            print(config_manager.get_setup_instructions() if config_manager else "")
            # Fall back to legacy config
            config_manager = None

        # Initialize LLM provider
        llm_provider = get_llm_provider()

        # Initialize storage (Postgres if available, SQLite fallback)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            storage_provider = PostgresAdapter(db_url)
            print("Using PostgreSQL database")
        else:
            # Fallback to SQLite - zero config!
            storage_provider = SQLiteAdapter()
            print(f"Using SQLite database at {storage_provider.db_path}")

        # Initialize the appropriate core
        if USE_ORCHESTRATOR and storage_provider:
            # New multi-agent orchestrator
            orchestrator = Orchestrator(
                llm=llm_provider,
                storage=storage_provider,
                config=OrchestratorConfig(
                    enable_learning=True,
                    alfred_personality="butler"
                )
            )
            print(f"Alfred Orchestrator initialized with {len(orchestrator.get_available_agents())} agents")

        # Always initialize legacy butler for backward compatibility
        alfred = Alfred(brain=llm_provider, storage=storage_provider)
        print(f"Alfred initialized with Brain: {type(llm_provider).__name__}, "
              f"Storage: {type(storage_provider).__name__ if storage_provider else 'None'}")

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
    """Chat with Alfred using multi-agent orchestration."""
    global alfred, orchestrator

    # Use orchestrator if available, fall back to legacy butler
    if USE_ORCHESTRATOR and orchestrator:
        try:
            response_text = await orchestrator.process(req.message, current_user_id)
            return ChatResponse(
                response=response_text,
                metadata={"engine": "orchestrator", "agents": len(orchestrator.get_available_agents())}
            )
        except Exception as e:
            print(f"Orchestrator error, falling back to butler: {e}")
            # Fall through to legacy butler

    # Legacy butler
    if not alfred:
        raise HTTPException(status_code=503, detail="Alfred not initialized")

    try:
        response_text = alfred.ask(req.message, current_user_id)
        return ChatResponse(response=response_text, metadata={"engine": "butler"})
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
        "storage": type(storage_provider).__name__ if storage_provider else "Not initialized",
        "orchestrator": "active" if orchestrator else "inactive",
        "agents": orchestrator.get_available_agents() if orchestrator else [],
        "use_orchestrator": USE_ORCHESTRATOR
    }


# =========================================
# Setup & Onboarding Endpoints
# =========================================

class SetupStatusResponse(BaseModel):
    """Response for setup status check."""
    is_configured: bool
    llm_provider: str = None
    database_type: str = None
    knowledge_graph: str = None
    missing: list = []
    instructions: str = None


class SetupRequest(BaseModel):
    """Request to configure Alfred."""
    openai_api_key: str = None
    anthropic_api_key: str = None


@app.get("/setup/status", response_model=SetupStatusResponse)
def get_setup_status():
    """Check if Alfred is properly configured."""
    global config_manager

    if config_manager:
        try:
            validation = config_manager.validate()
            return SetupStatusResponse(
                is_configured=validation.get("ready", False),
                llm_provider=validation.get("llm", {}).get("provider"),
                database_type=validation.get("database", {}).get("type"),
                knowledge_graph=validation.get("knowledge_graph", {}).get("type"),
                missing=[]
            )
        except Exception as e:
            return SetupStatusResponse(
                is_configured=False,
                missing=["llm_api_key"],
                instructions=str(e)
            )

    # Legacy check
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    missing = []
    if not has_openai and not has_anthropic:
        missing.append("llm_api_key")

    return SetupStatusResponse(
        is_configured=has_openai or has_anthropic,
        llm_provider="openai" if has_openai else ("anthropic" if has_anthropic else None),
        database_type="postgres" if os.getenv("DATABASE_URL") else "none",
        missing=missing,
        instructions="Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable" if missing else None
    )


@app.post("/setup/configure")
async def configure_alfred(req: SetupRequest):
    """
    Configure Alfred with API keys.

    Note: In production, this should securely store the keys.
    For now, it validates and returns instructions.
    """
    # Validate the provided keys
    if req.openai_api_key:
        if not req.openai_api_key.startswith("sk-"):
            raise HTTPException(status_code=400, detail="Invalid OpenAI API key format")

        # In production: securely store the key
        # For now, return success with instructions
        return {
            "success": True,
            "message": "OpenAI API key validated",
            "instructions": f"Set environment variable: OPENAI_API_KEY={req.openai_api_key[:10]}..."
        }

    if req.anthropic_api_key:
        if not req.anthropic_api_key.startswith("sk-ant-"):
            raise HTTPException(status_code=400, detail="Invalid Anthropic API key format")

        return {
            "success": True,
            "message": "Anthropic API key validated",
            "instructions": f"Set environment variable: ANTHROPIC_API_KEY={req.anthropic_api_key[:10]}..."
        }

    raise HTTPException(status_code=400, detail="Provide either openai_api_key or anthropic_api_key")


@app.get("/setup/integrations")
async def get_available_integrations():
    """Get list of available integrations."""
    # Return available integrations
    return {
        "available": [
            {
                "name": "google_calendar",
                "display_name": "Google Calendar",
                "description": "Sync with your Google Calendar",
                "status": "available",
                "requires_oauth": True
            },
            {
                "name": "gmail",
                "display_name": "Gmail",
                "description": "Read and send emails",
                "status": "coming_soon",
                "requires_oauth": True
            },
            {
                "name": "outlook",
                "display_name": "Microsoft Outlook",
                "description": "Calendar and email integration",
                "status": "coming_soon",
                "requires_oauth": True
            },
            {
                "name": "todoist",
                "display_name": "Todoist",
                "description": "Sync tasks with Todoist",
                "status": "coming_soon",
                "requires_api_key": True
            },
            {
                "name": "notion",
                "display_name": "Notion",
                "description": "Connect to your Notion workspace",
                "status": "coming_soon",
                "requires_oauth": True
            }
        ]
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
