"""
Alfred - The Digital Butler

Main FastAPI application entry point with modern architecture.
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load env vars
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("alfred")

# Legacy imports
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

# Knowledge graph and vector store imports
from alfred.infrastructure.knowledge.neo4j_graph import Neo4jKnowledgeGraph
from alfred.infrastructure.vector.qdrant import QdrantVectorStore
from alfred.infrastructure.vector.embeddings import get_embedding_provider

# Middleware imports
from alfred.api.middleware import (
    JWTAuthMiddleware,
    AuthConfig,
    RequestLoggingMiddleware,
    LoggingConfig,
    RateLimitMiddleware,
    RateLimitConfig,
    ErrorHandlerMiddleware,
)

# Services imports
from alfred.core.services import (
    ChatService,
    TaskService,
    HabitService,
    ProjectService,
    BriefingService,
)

# Connectors imports
from alfred.core.connectors import ConnectorManager, get_connector_registry

# Global service instances
llm_provider = None
storage_provider = None
alfred = None  # Deprecated, kept for backward compatibility
orchestrator = None
proactive_engine = None
push_service = None
scheduler = None
config_manager = None

# Knowledge graph and vector store instances
knowledge_graph: Optional[Neo4jKnowledgeGraph] = None
vector_store: Optional[QdrantVectorStore] = None

# New architecture services
chat_service: Optional[ChatService] = None
task_service: Optional[TaskService] = None
habit_service: Optional[HabitService] = None
project_service: Optional[ProjectService] = None
briefing_service: Optional[BriefingService] = None
connector_manager: Optional[ConnectorManager] = None

# Debug mode
DEBUG = os.getenv("ALFRED_DEBUG", "false").lower() == "true"


def init_services(storage, llm, notification_provider=None, knowledge_graph=None, vector_store=None):
    """Initialize all service layer components."""
    global chat_service, task_service, habit_service, project_service, briefing_service

    common_kwargs = {
        "storage": storage,
        "knowledge_graph": knowledge_graph,
        "notification_provider": notification_provider,
    }

    task_service = TaskService(**common_kwargs)
    task_service.vector_store = vector_store  # Add vector store for indexing
    habit_service = HabitService(**common_kwargs)
    project_service = ProjectService(**common_kwargs)
    briefing_service = BriefingService(**common_kwargs)
    chat_service = ChatService(llm_provider=llm, vector_store=vector_store, **common_kwargs)

    logger.info("Service layer initialized")


def init_connectors(storage):
    """Initialize connector manager."""
    global connector_manager

    connector_manager = ConnectorManager(storage=storage)

    # Register built-in connectors
    registry = get_connector_registry()
    logger.info(f"Connector registry initialized with {len(registry.connector_types)} types")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global llm_provider, storage_provider, alfred, orchestrator, proactive_engine
    global push_service, scheduler, config_manager, connector_manager
    global knowledge_graph, vector_store

    # Startup
    try:
        # Try new config manager first
        try:
            config_manager = get_config_manager()
            config = config_manager.get_config()
            logger.info(f"Alfred Config: {config_manager.validate()}")
        except ConfigValidationError as e:
            logger.warning(f"Config validation failed: {e}")
            logger.info(config_manager.get_setup_instructions() if config_manager else "")
            config_manager = None

        # Initialize LLM provider
        llm_provider = get_llm_provider()

        # Initialize storage (Postgres if available, SQLite fallback)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            storage_provider = PostgresAdapter(db_url)
            logger.info("Using PostgreSQL database")
        else:
            # Fallback to SQLite - zero config!
            storage_provider = SQLiteAdapter()
            logger.info(f"Using SQLite database at {storage_provider.db_path}")

        # Initialize Knowledge Graph (Neo4j) - optional
        if os.getenv("NEO4J_URI"):
            try:
                knowledge_graph = Neo4jKnowledgeGraph()
                if knowledge_graph.enabled:
                    logger.info("Neo4j knowledge graph connected")
                else:
                    logger.warning("Neo4j configured but not connected")
                    knowledge_graph = None
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j: {e}")
                knowledge_graph = None

        # Initialize Vector Store (Qdrant) - optional
        if os.getenv("QDRANT_URL") or os.getenv("OPENAI_API_KEY"):
            try:
                embedding_provider = get_embedding_provider("openai")
                vector_store = QdrantVectorStore(embedding_provider=embedding_provider)
                if await vector_store.initialize():
                    logger.info("Qdrant vector store initialized")
                else:
                    logger.warning("Qdrant could not be initialized")
                    vector_store = None
            except Exception as e:
                logger.warning(f"Failed to initialize Qdrant: {e}")
                vector_store = None

        # Initialize the orchestrator (primary chat engine)
        if storage_provider:
            orchestrator = Orchestrator(
                llm=llm_provider,
                storage=storage_provider,
                config=OrchestratorConfig(
                    enable_learning=True,
                )
            )
            logger.info(f"Alfred Orchestrator initialized with {len(orchestrator.get_available_agents())} agents")

        # Initialize legacy butler for backward compatibility (deprecated)
        alfred = Alfred(brain=llm_provider, storage=storage_provider)
        logger.info(f"Alfred initialized with Brain: {type(llm_provider).__name__}, "
                    f"Storage: {type(storage_provider).__name__ if storage_provider else 'None'}")

        # Initialize notification service
        push_service = ExpoPushService()

        # Initialize service layer
        if storage_provider:
            init_services(
                storage=storage_provider,
                llm=llm_provider,
                notification_provider=push_service,
                knowledge_graph=knowledge_graph,
                vector_store=vector_store,
            )

            # Initialize connectors
            init_connectors(storage=storage_provider)
            if connector_manager:
                await connector_manager.initialize()

        # Initialize proactive components
        if storage_provider:
            proactive_engine = ProactiveEngine(storage=storage_provider, llm=llm_provider)

            # Initialize and start the scheduler
            scheduler = get_scheduler()
            if scheduler.initialize(
                storage=storage_provider,
                proactive_engine=proactive_engine,
                push_service=push_service
            ):
                scheduler.start()
                logger.info("Alfred Scheduler started with proactive intelligence")
            else:
                logger.warning("Scheduler could not be initialized (APScheduler may not be installed)")

    except Exception as e:
        logger.error(f"CRITICAL ERROR Initializing Alfred: {e}")
        raise e

    yield

    # Shutdown
    logger.info("Alfred shutting down...")

    if connector_manager:
        await connector_manager.shutdown()

    if scheduler:
        scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Alfred - The Digital Butler",
    description="A proactive, intelligent personal assistant that manages your time, tasks, and habits.",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# =========================================
# Middleware Configuration
# =========================================

# Error handling (outermost - catches all errors)
app.add_middleware(ErrorHandlerMiddleware, debug=DEBUG)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    config=RateLimitConfig(
        requests_per_minute=60,
        burst_size=10,
        endpoint_limits={
            "/chat": 30,
            "/chat/stream": 30,
            "/voice/transcribe": 20,
            "/auth/login": 10,
            "/auth/signup": 5,
        },
    ),
)

# Request logging
app.add_middleware(
    RequestLoggingMiddleware,
    config=LoggingConfig(
        log_request_body=DEBUG,
        log_response_body=DEBUG,
        slow_request_threshold_ms=2000.0,
    ),
)

# JWT Authentication
app.add_middleware(
    JWTAuthMiddleware,
    config=AuthConfig(
        public_paths=(
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/signup",
            "/auth/refresh",
            "/setup/status",
            "/setup/integrations",
        ),
    ),
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
from alfred.api import connectors as connectors_api

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(habits.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(proactive.router)
app.include_router(knowledge.router)
app.include_router(voice.router)
app.include_router(connectors_api.router)


# =========================================
# API Models
# =========================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SetupStatusResponse(BaseModel):
    """Response for setup status check."""
    is_configured: bool
    llm_provider: Optional[str] = None
    database_type: Optional[str] = None
    knowledge_graph: Optional[str] = None
    missing: list = []
    instructions: Optional[str] = None


class SetupRequest(BaseModel):
    """Request to configure Alfred."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


# =========================================
# Chat Endpoints
# =========================================

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    """
    Chat with Alfred using multi-agent orchestration.

    Uses ChatService with Orchestrator for intelligent responses.
    """
    global orchestrator, chat_service

    # Get user from request state (set by auth middleware)
    current_user_id = getattr(request.state, "user_id", None)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use chat service (primary path)
    if chat_service:
        try:
            result = await chat_service.process_message(
                user_id=current_user_id,
                message=req.message,
                conversation_id=req.conversation_id,
            )
            return ChatResponse(
                response=result["response"],
                conversation_id=result.get("conversation_id"),
                metadata={
                    "engine": "orchestrator",
                    "tool_calls": result.get("tool_calls_made", 0),
                },
            )
        except Exception as e:
            logger.error(f"ChatService error: {e}")
            # Fall back to direct orchestrator call
            if orchestrator:
                try:
                    response_text = await orchestrator.process(req.message, current_user_id)
                    return ChatResponse(
                        response=response_text,
                        metadata={"engine": "orchestrator_fallback"}
                    )
                except Exception as oe:
                    logger.error(f"Orchestrator fallback error: {oe}")
                    raise HTTPException(status_code=500, detail=str(oe))

    # No chat service available
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Alfred not initialized")

    try:
        response_text = await orchestrator.process(req.message, current_user_id)
        return ChatResponse(response=response_text, metadata={"engine": "orchestrator"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """
    Stream chat response with thinking steps for transparency.
    Uses Server-Sent Events (SSE) to stream progress in real-time.
    """
    global orchestrator, chat_service

    current_user_id = getattr(request.state, "user_id", None)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    async def generate_stream():
        try:
            # Try streaming via chat service
            if chat_service:
                try:
                    # Yield thinking steps
                    yield f"data: {json.dumps({'type': 'thinking', 'step': {'step': 'Processing request', 'status': 'in_progress'}})}\n\n"

                    full_response = []
                    async for token in chat_service.process_message_streaming(
                        user_id=current_user_id,
                        message=req.message,
                        conversation_id=req.conversation_id,
                    ):
                        full_response.append(token)
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

                    yield f"data: {json.dumps({'type': 'response', 'content': ''.join(full_response)})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                except Exception as e:
                    logger.warning(f"ChatService streaming error: {e}")

            # Fallback to orchestrator with simulated streaming
            if not orchestrator:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Alfred not initialized'})}\n\n"
                return

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

            # Get actual response from orchestrator
            response_text = await orchestrator.process(req.message, current_user_id)

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


# =========================================
# Health & Status Endpoints
# =========================================

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "online",
        "version": "2.2.0",
        "brain": type(llm_provider).__name__ if llm_provider else "Not initialized",
        "storage": type(storage_provider).__name__ if storage_provider else "Not initialized",
        "orchestrator": "active" if orchestrator else "inactive",
        "agents": [a.value for a in orchestrator.get_available_agents()] if orchestrator else [],
        "services": {
            "chat": chat_service is not None,
            "tasks": task_service is not None,
            "habits": habit_service is not None,
            "projects": project_service is not None,
            "briefing": briefing_service is not None,
        },
        "integrations": {
            "knowledge_graph": knowledge_graph.enabled if knowledge_graph else False,
            "vector_store": vector_store is not None,
        },
        "connectors": {
            "manager": connector_manager is not None,
            "types": get_connector_registry().connector_types if connector_manager else [],
        },
    }


# =========================================
# Setup & Onboarding Endpoints
# =========================================

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
        database_type="postgres" if os.getenv("DATABASE_URL") else "sqlite",
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
    from alfred.core.connectors.registry import ConnectorCatalog

    # Get from connector catalog
    return {
        "available": ConnectorCatalog.get_all(),
        "categories": {
            "productivity": ConnectorCatalog.PRODUCTIVITY,
            "communication": ConnectorCatalog.COMMUNICATION,
            "development": ConnectorCatalog.DEVELOPMENT,
            "smart_home": ConnectorCatalog.SMART_HOME,
        },
    }


# =========================================
# Root Endpoint
# =========================================

@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Alfred - The Digital Butler",
        "version": "2.1.0",
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
            "voice": "/voice",
            "connectors": "/connectors",
            "setup": "/setup/status",
        }
    }


# Run with: uvicorn alfred.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
