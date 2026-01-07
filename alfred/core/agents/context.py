"""
Agent Context Builder.

Builds rich context for agent execution including:
- User information and preferences
- Relevant knowledge from the knowledge graph
- Recent conversation history
- Current time and environment info
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """User-specific context."""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_string(self) -> str:
        """Convert to string for inclusion in prompts."""
        parts = [f"User: {self.name or 'Unknown'}"]
        if self.timezone:
            parts.append(f"Timezone: {self.timezone}")

        if self.preferences:
            pref_str = ", ".join(f"{k}: {v}" for k, v in self.preferences.items())
            parts.append(f"Preferences: {pref_str}")

        return "\n".join(parts)


@dataclass
class KnowledgeContext:
    """Knowledge graph context."""
    facts: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    def to_prompt_string(self) -> str:
        """Convert to string for inclusion in prompts."""
        if not self.facts and not self.entities:
            return ""

        parts = ["Relevant knowledge:"]

        for fact in self.facts[:5]:  # Limit facts
            subject = fact.get("subject", "")
            predicate = fact.get("predicate", "")
            obj = fact.get("object", "")
            parts.append(f"- {subject} {predicate} {obj}")

        for entity in self.entities[:5]:
            name = entity.get("name", "")
            etype = entity.get("type", "")
            parts.append(f"- {name} ({etype})")

        return "\n".join(parts)


@dataclass
class EnvironmentContext:
    """Environment and temporal context."""
    current_time: datetime = field(default_factory=datetime.utcnow)
    day_of_week: str = ""
    is_morning: bool = False
    is_evening: bool = False
    is_weekend: bool = False

    def __post_init__(self):
        self.day_of_week = self.current_time.strftime("%A")
        hour = self.current_time.hour
        self.is_morning = 5 <= hour < 12
        self.is_evening = 17 <= hour < 22
        self.is_weekend = self.current_time.weekday() >= 5

    def to_prompt_string(self) -> str:
        """Convert to string for inclusion in prompts."""
        time_str = self.current_time.strftime("%I:%M %p")
        date_str = self.current_time.strftime("%B %d, %Y")

        parts = [
            f"Current time: {time_str}",
            f"Date: {date_str} ({self.day_of_week})",
        ]

        if self.is_morning:
            parts.append("Time of day: Morning")
        elif self.is_evening:
            parts.append("Time of day: Evening")

        if self.is_weekend:
            parts.append("It's the weekend")

        return "\n".join(parts)


@dataclass
class ConversationContext:
    """Conversation history context."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    summary: Optional[str] = None

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get the most recent messages."""
        return self.messages[-limit:]

    def to_prompt_string(self) -> str:
        """Convert to string for inclusion in prompts."""
        if self.summary:
            return f"Conversation summary: {self.summary}"
        return ""


class ContextBuilder:
    """
    Builds comprehensive context for agent execution.

    Aggregates information from:
    - Storage (user profile, preferences)
    - Knowledge graph (facts, entities)
    - Conversation history
    - Environment (time, date)
    """

    def __init__(
        self,
        storage: Any = None,
        knowledge_graph: Any = None,
    ):
        """
        Initialize context builder.

        Args:
            storage: MemoryStorage instance
            knowledge_graph: KnowledgeGraphProvider instance
        """
        self.storage = storage
        self.knowledge_graph = knowledge_graph

    async def build_user_context(self, user_id: str) -> UserContext:
        """Build user context from storage."""
        context = UserContext(user_id=user_id)

        if self.storage:
            try:
                profile = self.storage.get_user_profile(user_id)
                if profile:
                    context.name = profile.get("name")
                    context.email = profile.get("email")
                    context.timezone = profile.get("preferences", {}).get("timezone", "UTC")

                preferences = self.storage.get_preferences(user_id)
                if preferences:
                    context.preferences = preferences

            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

        return context

    async def build_knowledge_context(
        self,
        user_id: str,
        query: Optional[str] = None,
    ) -> KnowledgeContext:
        """Build knowledge context from knowledge graph."""
        context = KnowledgeContext()

        if self.knowledge_graph and query:
            try:
                # Get relevant facts
                kg_context = self.knowledge_graph.get_user_context(
                    user_id=user_id,
                    topic=query,
                )
                if kg_context:
                    context.facts = kg_context.get("facts", [])
                    context.entities = kg_context.get("entities", [])
                    context.relationships = kg_context.get("relationships", [])

            except Exception as e:
                logger.warning(f"Failed to load knowledge context: {e}")

        return context

    async def build_environment_context(
        self,
        timezone: str = "UTC",
    ) -> EnvironmentContext:
        """Build environment context."""
        import pytz

        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
        except Exception:
            current_time = datetime.utcnow()

        return EnvironmentContext(current_time=current_time)

    async def build_full_context(
        self,
        user_id: str,
        query: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Build full context for agent execution.

        Returns a dictionary with all context components.
        """
        # Build individual contexts
        user_context = await self.build_user_context(user_id)
        knowledge_context = await self.build_knowledge_context(user_id, query)
        env_context = await self.build_environment_context(user_context.timezone)

        conversation_context = ConversationContext(
            messages=conversation_history or []
        )

        return {
            "user": user_context,
            "knowledge": knowledge_context,
            "environment": env_context,
            "conversation": conversation_context,
        }

    def build_system_prompt_context(
        self,
        user_context: UserContext,
        knowledge_context: KnowledgeContext,
        env_context: EnvironmentContext,
    ) -> str:
        """
        Build context string for system prompt.

        Creates a formatted string with all relevant context
        for inclusion in the system prompt.
        """
        parts = []

        # User info
        user_str = user_context.to_prompt_string()
        if user_str:
            parts.append(f"## User Information\n{user_str}")

        # Environment
        env_str = env_context.to_prompt_string()
        if env_str:
            parts.append(f"## Current Context\n{env_str}")

        # Knowledge
        knowledge_str = knowledge_context.to_prompt_string()
        if knowledge_str:
            parts.append(f"## Relevant Knowledge\n{knowledge_str}")

        return "\n\n".join(parts)
