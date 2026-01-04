"""
Base Agent - Foundation for all Alfred agents

Each agent is a specialist that handles a specific domain of tasks.
The Orchestrator coordinates them to fulfill user requests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime


class AgentType(Enum):
    """Types of specialized agents in Alfred."""
    TASK = "task"           # Task creation, updates, prioritization
    MEMORY = "memory"       # Recall, preferences, knowledge graph queries
    PLANNING = "planning"   # Goal breakdown, strategy, next steps
    CALENDAR = "calendar"   # Scheduling, availability, events
    EMAIL = "email"         # Email drafting, summarization, inbox management
    RESEARCH = "research"   # Web search, information gathering
    PROJECT = "project"     # Project management, updates, health tracking


class AgentCapability(Enum):
    """Specific capabilities an agent can have."""
    # Task capabilities
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    QUERY_TASKS = "query_tasks"
    PRIORITIZE = "prioritize"

    # Memory capabilities
    RECALL_FACTS = "recall_facts"
    STORE_PREFERENCE = "store_preference"
    QUERY_KNOWLEDGE = "query_knowledge"
    FIND_RELATED = "find_related"

    # Planning capabilities
    BREAK_DOWN_GOAL = "break_down_goal"
    SUGGEST_NEXT_STEPS = "suggest_next_steps"
    ESTIMATE_EFFORT = "estimate_effort"

    # Calendar capabilities
    CHECK_AVAILABILITY = "check_availability"
    CREATE_EVENT = "create_event"
    FIND_FREE_SLOTS = "find_free_slots"

    # Email capabilities
    DRAFT_EMAIL = "draft_email"
    SUMMARIZE_INBOX = "summarize_inbox"
    FIND_EMAILS = "find_emails"

    # Research capabilities
    WEB_SEARCH = "web_search"
    SUMMARIZE_CONTENT = "summarize_content"
    COMPARE_OPTIONS = "compare_options"


@dataclass
class AgentContext:
    """
    Context passed to agents for execution.

    Contains everything an agent needs to understand the request
    and the user's current state.
    """
    user_id: str
    user_input: str
    intent: str = ""  # Classified intent from router
    topic: str = ""   # Main topic of the request
    entities: List[str] = field(default_factory=list)  # Mentioned entities

    # User context from memory
    user_profile: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, str] = field(default_factory=dict)
    recent_context: List[Dict[str, Any]] = field(default_factory=list)

    # Related data
    related_tasks: List[Dict[str, Any]] = field(default_factory=list)
    related_projects: List[Dict[str, Any]] = field(default_factory=list)
    related_entities: List[Dict[str, Any]] = field(default_factory=list)

    # Conversation history
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "chat"  # chat, voice, proactive, etc.


@dataclass
class AgentAction:
    """An action taken by an agent."""
    action_type: str  # e.g., "created_task", "scheduled_event"
    description: str  # Human-readable description
    data: Dict[str, Any] = field(default_factory=dict)  # Action details
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentResult:
    """
    Result from an agent execution.

    Contains what the agent did, what it found, and suggestions.
    """
    agent_type: AgentType
    success: bool

    # What the agent found or produced
    data: Dict[str, Any] = field(default_factory=dict)

    # Actions taken (e.g., created task, scheduled event)
    actions: List[AgentAction] = field(default_factory=list)

    # Suggestions for the user
    suggestions: List[str] = field(default_factory=list)

    # Information to include in response
    response_fragments: List[str] = field(default_factory=list)

    # Error information
    error: Optional[str] = None

    # Metadata
    execution_time_ms: int = 0
    tokens_used: int = 0

    @property
    def actions_taken(self) -> List[str]:
        """Get list of action descriptions."""
        return [a.description for a in self.actions if a.success]


class BaseAgent(ABC):
    """
    Base class for all Alfred agents.

    Each agent specializes in a specific domain and can:
    1. Analyze user requests relevant to their domain
    2. Query relevant data sources
    3. Take actions (create, update, delete)
    4. Provide information for the response

    Agents are stateless - all context is passed via AgentContext.
    """

    def __init__(self, llm, storage, config):
        """
        Initialize the agent.

        Args:
            llm: LLM provider for generating responses
            storage: Storage adapter for data access
            config: Alfred configuration
        """
        self.llm = llm
        self.storage = storage
        self.config = config

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Set[AgentCapability]:
        """Return the capabilities this agent has."""
        pass

    @property
    def name(self) -> str:
        """Human-readable name for this agent."""
        return f"{self.agent_type.value.title()} Agent"

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's task based on context.

        This is the main entry point for agent execution.
        The agent should:
        1. Analyze the context to understand what's needed
        2. Query relevant data
        3. Take appropriate actions
        4. Return results

        Args:
            context: Full context for the request

        Returns:
            AgentResult with findings, actions, and suggestions
        """
        pass

    async def can_handle(self, context: AgentContext) -> float:
        """
        Determine how well this agent can handle the given context.

        Returns a confidence score from 0.0 to 1.0.
        Used by the orchestrator to route requests.

        Args:
            context: The request context

        Returns:
            Confidence score (0.0 = cannot handle, 1.0 = perfect match)
        """
        # Default implementation - override for better routing
        return 0.5 if self._has_relevant_keywords(context.user_input) else 0.0

    def _has_relevant_keywords(self, text: str) -> bool:
        """Check if text contains keywords relevant to this agent."""
        # Override in subclasses with agent-specific keywords
        return False

    async def _generate_with_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Helper to generate text with the LLM."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.llm.generate_response(prompt, messages)

    def _create_result(
        self,
        success: bool = True,
        data: Dict[str, Any] = None,
        actions: List[AgentAction] = None,
        suggestions: List[str] = None,
        response_fragments: List[str] = None,
        error: str = None
    ) -> AgentResult:
        """Helper to create an AgentResult."""
        return AgentResult(
            agent_type=self.agent_type,
            success=success,
            data=data or {},
            actions=actions or [],
            suggestions=suggestions or [],
            response_fragments=response_fragments or [],
            error=error
        )


class RoutingDecision:
    """Decision from the intent router about which agents to use."""

    def __init__(
        self,
        intent: str,
        topic: str,
        required_agents: List[AgentType],
        optional_agents: List[AgentType] = None,
        priority: str = "medium",
        entities: List[str] = None,
        confidence: float = 1.0
    ):
        self.intent = intent
        self.topic = topic
        self.required_agents = required_agents
        self.optional_agents = optional_agents or []
        self.priority = priority
        self.entities = entities or []
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "topic": self.topic,
            "required_agents": [a.value for a in self.required_agents],
            "optional_agents": [a.value for a in self.optional_agents],
            "priority": self.priority,
            "entities": self.entities,
            "confidence": self.confidence
        }
