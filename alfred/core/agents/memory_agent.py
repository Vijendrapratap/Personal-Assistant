"""
Memory Agent - Handles knowledge retrieval and storage

Responsibilities:
- Recall facts about people, companies, projects
- Store and retrieve user preferences
- Query knowledge graph for relationships
- Find related entities and context
- Maintain conversation memory
"""

from typing import Set, Dict, Any, List, Optional
from datetime import datetime
import json
import re

from alfred.core.agents.base import (
    BaseAgent,
    AgentType,
    AgentCapability,
    AgentContext,
    AgentResult,
    AgentAction
)


class MemoryAgent(BaseAgent):
    """Agent specialized in memory and knowledge retrieval."""

    MEMORY_KEYWORDS = [
        "remember", "recall", "forgot", "forget",
        "what do you know", "tell me about",
        "who is", "what is", "when did",
        "last time", "previously", "before",
        "history", "past", "mentioned",
        "preference", "prefer", "like", "dislike",
        "always", "never", "usually"
    ]

    RECALL_PROMPT = """
    The user is asking about something from memory. Analyze and determine what to recall.

    User message: {user_input}

    Known entities (people, companies, projects):
    {entities}

    Recent conversation context:
    {recent_context}

    Determine:
    1. What type of recall is needed (person, company, project, preference, fact, conversation)
    2. The specific entity or topic
    3. What information would be most relevant

    Return JSON:
    {{
        "recall_type": "person|company|project|preference|fact|conversation|general",
        "entity": "name of entity if applicable",
        "query": "what to look for",
        "time_context": "recent|specific_date|all_time",
        "confidence": 0.0-1.0
    }}
    """

    PREFERENCE_EXTRACTION_PROMPT = """
    Analyze this conversation for any user preferences or facts to remember.

    User said: {user_input}
    Alfred responded: {response}

    Extract any:
    1. Preferences (likes, dislikes, habits)
    2. Facts about people the user knows
    3. Facts about companies or projects
    4. Personal information the user shared

    Return JSON:
    {{
        "preferences": [
            {{"key": "preference_name", "value": "preference_value", "confidence": 0.9}}
        ],
        "facts": [
            {{"subject": "entity", "predicate": "relationship", "object": "value"}}
        ],
        "entities": [
            {{"name": "...", "type": "person|company|project", "attributes": {{}}}}
        ]
    }}

    If nothing to extract, return {{"preferences": [], "facts": [], "entities": []}}
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.MEMORY

    @property
    def capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.RECALL_FACTS,
            AgentCapability.STORE_PREFERENCE,
            AgentCapability.QUERY_KNOWLEDGE,
            AgentCapability.FIND_RELATED,
        }

    def _has_relevant_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.MEMORY_KEYWORDS)

    async def can_handle(self, context: AgentContext) -> float:
        """Determine confidence for handling this request."""
        text = context.user_input.lower()

        # Check for explicit memory keywords
        keyword_matches = sum(1 for kw in self.MEMORY_KEYWORDS if kw in text)

        if keyword_matches >= 2:
            return 0.9
        elif keyword_matches >= 1:
            return 0.7

        # Check for question patterns about entities
        question_patterns = [
            r"who (?:is|was) (\w+)",
            r"what (?:is|do you know about) (\w+)",
            r"tell me about (\w+)",
            r"when did (?:i|we) (?:last |)(?:meet|talk|speak|see)",
            r"do you remember",
        ]

        for pattern in question_patterns:
            if re.search(pattern, text):
                return 0.8

        # Memory agent should always participate to provide context
        return 0.3  # Low baseline - always contributes context

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute memory retrieval or storage."""
        try:
            # Determine what kind of memory operation is needed
            recall_intent = await self._analyze_recall_intent(context)

            # Always gather relevant context
            memory_context = await self._gather_context(context, recall_intent)

            # If this is an explicit recall request, do the lookup
            if recall_intent.get("recall_type") != "general":
                return await self._handle_recall(context, recall_intent, memory_context)

            # Otherwise, just provide context for other agents
            return self._create_result(
                success=True,
                data={"context": memory_context},
                response_fragments=[]
            )

        except Exception as e:
            return self._create_result(
                success=False,
                error=str(e)
            )

    async def _analyze_recall_intent(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze what the user wants to recall."""
        # Get known entities for context
        entities = []
        if context.related_entities:
            entities = [f"{e.get('name', '')} ({e.get('type', '')})"
                       for e in context.related_entities[:20]]

        # Get recent context
        recent = []
        if context.conversation_history:
            recent = [f"{m['role']}: {m['content'][:100]}..."
                     for m in context.conversation_history[-5:]]

        prompt = self.RECALL_PROMPT.format(
            user_input=context.user_input,
            entities="\n".join(entities) if entities else "None known",
            recent_context="\n".join(recent) if recent else "No recent context"
        )

        response = await self._generate_with_llm(prompt)

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {"recall_type": "general", "confidence": 0.5}

    async def _gather_context(
        self,
        context: AgentContext,
        recall_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather relevant context from all memory sources."""
        memory_context = {
            "preferences": {},
            "entities": [],
            "facts": [],
            "recent_interactions": [],
            "related_projects": [],
            "related_tasks": []
        }

        if not self.storage:
            return memory_context

        try:
            # Get user preferences
            prefs = self.storage.get_preferences(context.user_id)
            memory_context["preferences"] = prefs

            # Get recent chat history
            history = self.storage.get_chat_history(context.user_id, limit=10)
            memory_context["recent_interactions"] = history

            # Get active projects for context
            projects = self.storage.get_projects(context.user_id, status="active")
            memory_context["related_projects"] = projects[:5]

            # Get high priority tasks
            tasks = self.storage.get_tasks(context.user_id, priority="high")
            memory_context["related_tasks"] = [
                t for t in tasks
                if t.get("status") not in ["completed", "cancelled"]
            ][:5]

            # If looking for specific entity, try to find it
            entity_name = recall_intent.get("entity")
            if entity_name:
                # Search in projects
                for p in projects:
                    if entity_name.lower() in p["name"].lower():
                        memory_context["entities"].append({
                            "type": "project",
                            "name": p["name"],
                            "data": p
                        })

                # TODO: Search in knowledge graph when implemented

        except Exception as e:
            memory_context["error"] = str(e)

        return memory_context

    async def _handle_recall(
        self,
        context: AgentContext,
        recall_intent: Dict[str, Any],
        memory_context: Dict[str, Any]
    ) -> AgentResult:
        """Handle an explicit recall request."""
        recall_type = recall_intent.get("recall_type", "general")
        entity = recall_intent.get("entity", "")

        fragments = []
        data = {"recall_type": recall_type, "entity": entity}

        if recall_type == "person":
            # Look up person in knowledge
            person_info = self._find_person(entity, memory_context)
            if person_info:
                fragments.append(f"Here's what I know about {entity}:")
                for key, value in person_info.items():
                    if key != "name":
                        fragments.append(f"  - {key}: {value}")
                data["person"] = person_info
            else:
                fragments.append(f"I don't have any stored information about {entity}.")

        elif recall_type == "company":
            # Look up company
            company_info = self._find_company(entity, memory_context)
            if company_info:
                fragments.append(f"About {entity}:")
                data["company"] = company_info
            else:
                fragments.append(f"I don't have information about {entity} stored.")

        elif recall_type == "project":
            # Look up project
            project_info = self._find_project(entity, memory_context)
            if project_info:
                fragments.append(f"Project: {project_info.get('name', entity)}")
                if project_info.get("status"):
                    fragments.append(f"  Status: {project_info['status']}")
                if project_info.get("role"):
                    fragments.append(f"  Your role: {project_info['role']}")
                data["project"] = project_info
            else:
                fragments.append(f"I couldn't find a project matching '{entity}'.")

        elif recall_type == "preference":
            # Look up preferences
            prefs = memory_context.get("preferences", {})
            if entity and entity in prefs:
                fragments.append(f"Your preference for {entity}: {prefs[entity]}")
            elif prefs:
                fragments.append("Your stored preferences:")
                for k, v in list(prefs.items())[:5]:
                    fragments.append(f"  - {k}: {v}")
            else:
                fragments.append("I haven't learned any preferences yet.")
            data["preferences"] = prefs

        elif recall_type == "conversation":
            # Recall from conversation history
            history = memory_context.get("recent_interactions", [])
            if history:
                fragments.append("From our recent conversations:")
                # Summarize recent relevant conversations
                for msg in history[-3:]:
                    role = "You" if msg["role"] == "user" else "I"
                    fragments.append(f"  {role}: {msg['content'][:80]}...")
            data["history"] = history

        return self._create_result(
            success=True,
            data=data,
            response_fragments=fragments
        )

    def _find_person(self, name: str, context: Dict) -> Optional[Dict]:
        """Find person in memory context."""
        for entity in context.get("entities", []):
            if entity.get("type") == "person" and name.lower() in entity.get("name", "").lower():
                return entity.get("data", entity)
        return None

    def _find_company(self, name: str, context: Dict) -> Optional[Dict]:
        """Find company in memory context."""
        for entity in context.get("entities", []):
            if entity.get("type") == "company" and name.lower() in entity.get("name", "").lower():
                return entity.get("data", entity)
        return None

    def _find_project(self, name: str, context: Dict) -> Optional[Dict]:
        """Find project in memory context."""
        for project in context.get("related_projects", []):
            if name.lower() in project.get("name", "").lower():
                return project
        return None

    async def store_interaction(
        self,
        user_id: str,
        user_input: str,
        response: str,
        actions: List[List[str]]
    ) -> None:
        """
        Store interaction and extract learnings.
        Called by orchestrator after each interaction.
        """
        if not self.storage:
            return

        try:
            # Save the conversation
            self.storage.save_chat(user_id, "user", user_input)
            self.storage.save_chat(user_id, "assistant", response)

            # Extract preferences and facts
            extraction = await self._extract_learnings(user_input, response)

            # Store preferences
            for pref in extraction.get("preferences", []):
                self.storage.save_preference(
                    user_id,
                    pref["key"],
                    pref["value"],
                    pref.get("confidence", 0.8)
                )

            # TODO: Store facts in knowledge graph when implemented

        except Exception as e:
            print(f"Error storing interaction: {e}")

    async def _extract_learnings(
        self,
        user_input: str,
        response: str
    ) -> Dict[str, Any]:
        """Extract learnable information from an interaction."""
        prompt = self.PREFERENCE_EXTRACTION_PROMPT.format(
            user_input=user_input,
            response=response
        )

        llm_response = await self._generate_with_llm(prompt)

        try:
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {"preferences": [], "facts": [], "entities": []}

    async def get_context_for_topic(
        self,
        user_id: str,
        topic: str
    ) -> Dict[str, Any]:
        """
        Get relevant context for a specific topic.
        Used by orchestrator to enrich context for other agents.
        """
        context = AgentContext(
            user_id=user_id,
            user_input=f"What do you know about {topic}?"
        )

        recall_intent = {
            "recall_type": "general",
            "entity": topic,
            "query": topic,
            "confidence": 1.0
        }

        return await self._gather_context(context, recall_intent)
