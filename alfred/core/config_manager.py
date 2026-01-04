"""
Alfred Config Manager - Zero-Config Setup

Automatically detects and configures all services.
User only needs to provide an LLM API key - everything else is auto-configured.
"""

import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class DatabaseType(Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"


class KnowledgeGraphType(Enum):
    NEO4J = "neo4j"
    EMBEDDED = "embedded"  # DuckDB-based


class VectorStoreType(Enum):
    QDRANT = "qdrant"
    CHROMA = "chroma"  # Embedded


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: LLMProvider
    api_key: Optional[str] = None
    model: str = "gpt-4o"
    base_url: Optional[str] = None  # For Ollama or custom endpoints

    @property
    def is_valid(self) -> bool:
        if self.provider == LLMProvider.OLLAMA:
            return True  # No API key needed
        return bool(self.api_key)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: DatabaseType
    url: Optional[str] = None  # For Postgres
    path: Optional[str] = None  # For SQLite

    @property
    def connection_string(self) -> str:
        if self.type == DatabaseType.POSTGRES:
            return self.url or ""
        return f"sqlite:///{self.path}"


@dataclass
class KnowledgeGraphConfig:
    """Knowledge graph configuration."""
    type: KnowledgeGraphType
    uri: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None  # For embedded


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    type: VectorStoreType
    url: Optional[str] = None  # For Qdrant
    path: Optional[str] = None  # For Chroma embedded


@dataclass
class AlfredConfig:
    """Complete Alfred configuration."""
    llm: LLMConfig
    database: DatabaseConfig
    knowledge_graph: KnowledgeGraphConfig
    vector_store: VectorStoreConfig
    secret_key: str
    data_dir: Path

    # Feature flags
    enable_knowledge_graph: bool = True
    enable_vector_search: bool = True
    enable_proactive: bool = True


class ConfigValidationError(Exception):
    """Raised when configuration is invalid."""
    pass


class AlfredConfigManager:
    """
    Zero-config manager that:
    1. Auto-detects what's available
    2. Falls back to embedded alternatives
    3. Validates on startup
    4. Provides a single source of truth for all configuration

    Usage:
        config_manager = AlfredConfigManager()
        config = config_manager.get_config()

        # Or with explicit API key:
        config_manager = AlfredConfigManager(openai_api_key="sk-...")
    """

    DEFAULT_DATA_DIR = Path.home() / ".alfred"

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        data_dir: Optional[Path] = None,
        force_embedded: bool = False  # Force embedded services even if external available
    ):
        self.data_dir = Path(data_dir or self.DEFAULT_DATA_DIR).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._openai_key = openai_api_key
        self._anthropic_key = anthropic_api_key
        self._force_embedded = force_embedded

        self._config: Optional[AlfredConfig] = None

    def get_config(self) -> AlfredConfig:
        """Get the complete Alfred configuration."""
        if self._config is None:
            self._config = self._build_config()
        return self._config

    def _build_config(self) -> AlfredConfig:
        """Build complete configuration with auto-detection."""
        return AlfredConfig(
            llm=self._configure_llm(),
            database=self._configure_database(),
            knowledge_graph=self._configure_knowledge_graph(),
            vector_store=self._configure_vector_store(),
            secret_key=self._get_or_generate_secret(),
            data_dir=self.data_dir,
            enable_knowledge_graph=True,
            enable_vector_search=True,
            enable_proactive=True,
        )

    def _configure_llm(self) -> LLMConfig:
        """Configure LLM provider with fallback."""
        # Priority: Explicit key > Environment > Ollama fallback

        # Check for OpenAI
        openai_key = self._openai_key or os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = os.getenv("ALFRED_MODEL", "gpt-4o")
            return LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=openai_key,
                model=model
            )

        # Check for Anthropic
        anthropic_key = self._anthropic_key or os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            model = os.getenv("ALFRED_MODEL", "claude-sonnet-4-20250514")
            return LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key=anthropic_key,
                model=model
            )

        # Check for Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        if self._check_ollama_available(ollama_url):
            model = os.getenv("ALFRED_MODEL", "llama3.2")
            return LLMConfig(
                provider=LLMProvider.OLLAMA,
                model=model,
                base_url=ollama_url
            )

        # No LLM available - this is a critical error
        raise ConfigValidationError(
            "No LLM provider configured. Please provide an OpenAI API key, "
            "Anthropic API key, or ensure Ollama is running."
        )

    def _configure_database(self) -> DatabaseConfig:
        """Configure database with fallback to SQLite."""
        if self._force_embedded:
            return self._get_sqlite_config()

        # Check for Postgres
        postgres_url = os.getenv("DATABASE_URL")
        if postgres_url:
            return DatabaseConfig(
                type=DatabaseType.POSTGRES,
                url=postgres_url
            )

        # Fallback to SQLite
        return self._get_sqlite_config()

    def _get_sqlite_config(self) -> DatabaseConfig:
        """Get SQLite configuration."""
        db_path = self.data_dir / "alfred.db"
        return DatabaseConfig(
            type=DatabaseType.SQLITE,
            path=str(db_path)
        )

    def _configure_knowledge_graph(self) -> KnowledgeGraphConfig:
        """Configure knowledge graph with fallback to embedded."""
        if self._force_embedded:
            return self._get_embedded_graph_config()

        # Check for Neo4j
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri:
            return KnowledgeGraphConfig(
                type=KnowledgeGraphType.NEO4J,
                uri=neo4j_uri,
                user=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD")
            )

        # Fallback to embedded
        return self._get_embedded_graph_config()

    def _get_embedded_graph_config(self) -> KnowledgeGraphConfig:
        """Get embedded knowledge graph configuration."""
        graph_path = self.data_dir / "knowledge.duckdb"
        return KnowledgeGraphConfig(
            type=KnowledgeGraphType.EMBEDDED,
            path=str(graph_path)
        )

    def _configure_vector_store(self) -> VectorStoreConfig:
        """Configure vector store with fallback to embedded."""
        if self._force_embedded:
            return self._get_chroma_config()

        # Check for Qdrant
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            return VectorStoreConfig(
                type=VectorStoreType.QDRANT,
                url=qdrant_url
            )

        # Fallback to Chroma embedded
        return self._get_chroma_config()

    def _get_chroma_config(self) -> VectorStoreConfig:
        """Get Chroma embedded configuration."""
        chroma_path = self.data_dir / "vectors"
        chroma_path.mkdir(parents=True, exist_ok=True)
        return VectorStoreConfig(
            type=VectorStoreType.CHROMA,
            path=str(chroma_path)
        )

    def _get_or_generate_secret(self) -> str:
        """Get or generate a secure secret key."""
        # Check environment first
        env_secret = os.getenv("SECRET_KEY")
        if env_secret and env_secret != "supersecretkey":
            return env_secret

        # Check for persisted secret
        secret_file = self.data_dir / ".secret"
        if secret_file.exists():
            return secret_file.read_text().strip()

        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        secret_file.write_text(new_secret)
        secret_file.chmod(0o600)  # Owner read/write only
        return new_secret

    def _check_ollama_available(self, url: str) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            import httpx
            response = httpx.get(f"{url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def validate(self) -> Dict[str, Any]:
        """
        Validate the configuration and return a status report.

        Returns:
            Dict with validation status for each component.
        """
        config = self.get_config()

        return {
            "llm": {
                "provider": config.llm.provider.value,
                "model": config.llm.model,
                "valid": config.llm.is_valid,
            },
            "database": {
                "type": config.database.type.value,
                "location": config.database.url or config.database.path,
            },
            "knowledge_graph": {
                "type": config.knowledge_graph.type.value,
                "location": config.knowledge_graph.uri or config.knowledge_graph.path,
            },
            "vector_store": {
                "type": config.vector_store.type.value,
                "location": config.vector_store.url or config.vector_store.path,
            },
            "data_dir": str(config.data_dir),
            "ready": config.llm.is_valid,
        }

    def get_setup_instructions(self) -> str:
        """Get setup instructions for missing configuration."""
        try:
            config = self.get_config()
            if config.llm.is_valid:
                return "Alfred is fully configured and ready to use!"
        except ConfigValidationError:
            pass

        return """
Alfred Setup Required
=====================

Alfred needs an AI brain to work. Choose one option:

Option 1: OpenAI (Recommended)
------------------------------
1. Go to https://platform.openai.com
2. Create an API key
3. Set environment variable:
   export OPENAI_API_KEY="sk-your-key-here"

Option 2: Anthropic Claude
--------------------------
1. Go to https://console.anthropic.com
2. Create an API key
3. Set environment variable:
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"

Option 3: Ollama (Free, Local)
------------------------------
1. Install Ollama: https://ollama.ai
2. Run: ollama run llama3.2
3. Alfred will auto-detect it

Then restart Alfred!
"""


# Singleton instance for easy access
_config_manager: Optional[AlfredConfigManager] = None


def get_config_manager(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    force_new: bool = False
) -> AlfredConfigManager:
    """Get the global config manager instance."""
    global _config_manager

    if _config_manager is None or force_new:
        _config_manager = AlfredConfigManager(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        )

    return _config_manager


def get_config() -> AlfredConfig:
    """Convenience function to get the current configuration."""
    return get_config_manager().get_config()
