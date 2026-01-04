"""
Knowledge Extractor - Automatic Learning from Conversations

Extracts entities, relationships, and facts from every conversation
to build a rich knowledge graph about the user's world.
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntityType(Enum):
    """Types of entities that can be extracted."""
    PERSON = "person"
    COMPANY = "company"
    PROJECT = "project"
    PRODUCT = "product"
    PLACE = "place"
    EVENT = "event"
    CONCEPT = "concept"


class RelationshipType(Enum):
    """Types of relationships between entities."""
    WORKS_AT = "works_at"
    WORKS_ON = "works_on"
    MANAGES = "manages"
    REPORTS_TO = "reports_to"
    KNOWS = "knows"
    MET = "met"
    INTERESTED_IN = "interested_in"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    OWNS = "owns"
    USES = "uses"
    CREATED = "created"


@dataclass
class ExtractedEntity:
    """An entity extracted from conversation."""
    name: str
    type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class ExtractedRelationship:
    """A relationship between entities."""
    from_entity: str
    relationship: RelationshipType
    to_entity: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ExtractedFact:
    """A fact about an entity."""
    subject: str
    predicate: str
    object_value: str
    confidence: float = 1.0
    temporal: Optional[str] = None  # past, present, future


@dataclass
class ExtractionResult:
    """Complete extraction result from a conversation."""
    entities: List[ExtractedEntity] = field(default_factory=list)
    relationships: List[ExtractedRelationship] = field(default_factory=list)
    facts: List[ExtractedFact] = field(default_factory=list)
    preferences: List[Dict[str, Any]] = field(default_factory=list)
    temporal_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [
                {"name": e.name, "type": e.type.value, "attributes": e.attributes}
                for e in self.entities
            ],
            "relationships": [
                {
                    "from": r.from_entity,
                    "type": r.relationship.value,
                    "to": r.to_entity,
                    "properties": r.properties
                }
                for r in self.relationships
            ],
            "facts": [
                {"subject": f.subject, "predicate": f.predicate, "object": f.object_value}
                for f in self.facts
            ],
            "preferences": self.preferences,
            "temporal_events": self.temporal_events
        }


class KnowledgeExtractor:
    """
    Extracts structured knowledge from conversations.

    Uses a combination of:
    1. Pattern matching for common structures
    2. LLM for complex extraction
    3. Validation and deduplication
    """

    EXTRACTION_PROMPT = """
    Extract structured knowledge from this conversation between a user and their AI assistant.

    User: {user_input}
    Assistant: {response}

    Extract the following (be thorough but only extract what's explicitly stated or clearly implied):

    1. ENTITIES - People, companies, projects, products, places mentioned
    2. RELATIONSHIPS - How entities relate to each other
    3. FACTS - Specific facts about entities
    4. PREFERENCES - User preferences or habits revealed
    5. TEMPORAL - Events with time context (past meetings, future deadlines)

    Return JSON:
    {{
        "entities": [
            {{
                "name": "entity name",
                "type": "person|company|project|product|place|event|concept",
                "attributes": {{"role": "CTO", "company": "TechCorp"}},
                "confidence": 0.9
            }}
        ],
        "relationships": [
            {{
                "from": "entity1",
                "type": "works_at|works_on|manages|knows|met|interested_in|part_of|owns|uses|created",
                "to": "entity2",
                "properties": {{"since": "2024"}}
            }}
        ],
        "facts": [
            {{
                "subject": "entity",
                "predicate": "what about it",
                "object": "the value/fact",
                "confidence": 0.9
            }}
        ],
        "preferences": [
            {{
                "key": "preference_name",
                "value": "preference_value",
                "confidence": 0.9
            }}
        ],
        "temporal_events": [
            {{
                "entity": "what/who",
                "event": "what happened/will happen",
                "time": "when (relative or absolute)",
                "type": "past|future|recurring"
            }}
        ]
    }}

    If nothing to extract, return empty arrays. Only extract high-confidence information.
    """

    # Patterns for quick extraction (before LLM)
    PERSON_PATTERNS = [
        r"(?:met with|talked to|spoke with|meeting with|call with) (\w+(?:\s+\w+)?)",
        r"(\w+(?:\s+\w+)?) (?:is|was) (?:the |a |an )?(?:CEO|CTO|VP|Director|Manager|Lead|Head|Chief)",
        r"(\w+(?:\s+\w+)?) from (\w+(?:\s+\w+)?)",
        r"(?:my |our )(?:colleague|friend|boss|manager|client) (\w+(?:\s+\w+)?)",
    ]

    COMPANY_PATTERNS = [
        r"(?:at|from|with) (\w+(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Co\.))?)",
        r"(\w+(?:\s+\w+)?) (?:is a|is an) (?:company|startup|firm|client|vendor)",
    ]

    PREFERENCE_PATTERNS = [
        (r"(?:i |we )(?:always|usually|prefer to|like to) (.+)", "habit"),
        (r"(?:i |we )(?:never|don't like|hate|avoid) (.+)", "avoidance"),
        (r"(?:i |we )prefer (.+?) (?:over|to|instead)", "preference"),
    ]

    def __init__(self, llm):
        """
        Initialize the knowledge extractor.

        Args:
            llm: LLM provider for complex extraction
        """
        self.llm = llm

    async def extract(
        self,
        user_input: str,
        response: str,
        existing_context: Dict[str, Any] = None
    ) -> ExtractionResult:
        """
        Extract knowledge from a conversation turn.

        Args:
            user_input: What the user said
            response: What Alfred responded
            existing_context: Existing entities/facts for deduplication

        Returns:
            ExtractionResult with all extracted knowledge
        """
        result = ExtractionResult()

        # Step 1: Quick pattern-based extraction
        pattern_result = self._pattern_extract(user_input)
        result.entities.extend(pattern_result.entities)
        result.preferences.extend(pattern_result.preferences)

        # Step 2: LLM-based extraction for deeper understanding
        llm_result = await self._llm_extract(user_input, response)

        # Merge results (deduplicate)
        result = self._merge_results(result, llm_result)

        # Step 3: Validate and clean
        result = self._validate_and_clean(result, existing_context)

        return result

    def _pattern_extract(self, text: str) -> ExtractionResult:
        """Extract using regex patterns (fast path)."""
        result = ExtractionResult()
        text_lower = text.lower()

        # Extract persons
        for pattern in self.PERSON_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if len(name) > 1 and not name.lower() in ['i', 'me', 'my', 'we', 'our']:
                    # Check for additional context in match
                    attributes = {}
                    if len(match.groups()) > 1 and match.group(2):
                        attributes["company"] = match.group(2).strip()

                    result.entities.append(ExtractedEntity(
                        name=name.title(),
                        type=EntityType.PERSON,
                        attributes=attributes,
                        confidence=0.7,
                        source_text=match.group(0)
                    ))

        # Extract companies
        for pattern in self.COMPANY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                # Filter out common false positives
                if len(name) > 2 and name.lower() not in ['the', 'a', 'an', 'home', 'work']:
                    result.entities.append(ExtractedEntity(
                        name=name.title(),
                        type=EntityType.COMPANY,
                        confidence=0.6,
                        source_text=match.group(0)
                    ))

        # Extract preferences
        for pattern, pref_type in self.PREFERENCE_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value = match.group(1).strip()
                if len(value) > 3:
                    result.preferences.append({
                        "key": pref_type,
                        "value": value,
                        "confidence": 0.7
                    })

        return result

    async def _llm_extract(self, user_input: str, response: str) -> ExtractionResult:
        """Extract using LLM for complex understanding."""
        result = ExtractionResult()

        # Skip LLM for very short messages
        if len(user_input) < 20 and len(response) < 50:
            return result

        try:
            prompt = self.EXTRACTION_PROMPT.format(
                user_input=user_input,
                response=response
            )

            llm_response = self.llm.generate_response(prompt, [])

            # Parse JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                # Parse entities
                for e in data.get("entities", []):
                    try:
                        entity_type = EntityType(e.get("type", "concept").lower())
                        result.entities.append(ExtractedEntity(
                            name=e.get("name", ""),
                            type=entity_type,
                            attributes=e.get("attributes", {}),
                            confidence=e.get("confidence", 0.8)
                        ))
                    except (ValueError, KeyError):
                        pass

                # Parse relationships
                for r in data.get("relationships", []):
                    try:
                        rel_type = RelationshipType(r.get("type", "knows").lower())
                        result.relationships.append(ExtractedRelationship(
                            from_entity=r.get("from", ""),
                            relationship=rel_type,
                            to_entity=r.get("to", ""),
                            properties=r.get("properties", {}),
                            confidence=r.get("confidence", 0.8)
                        ))
                    except (ValueError, KeyError):
                        pass

                # Parse facts
                for f in data.get("facts", []):
                    result.facts.append(ExtractedFact(
                        subject=f.get("subject", ""),
                        predicate=f.get("predicate", ""),
                        object_value=f.get("object", ""),
                        confidence=f.get("confidence", 0.8)
                    ))

                # Parse preferences
                result.preferences.extend(data.get("preferences", []))

                # Parse temporal events
                result.temporal_events.extend(data.get("temporal_events", []))

        except json.JSONDecodeError as e:
            print(f"JSON parsing error in extraction: {e}")
        except Exception as e:
            print(f"LLM extraction error: {e}")

        return result

    def _merge_results(
        self,
        result1: ExtractionResult,
        result2: ExtractionResult
    ) -> ExtractionResult:
        """Merge two extraction results, deduplicating."""
        merged = ExtractionResult()

        # Merge entities (dedupe by name)
        seen_entities = {}
        for e in result1.entities + result2.entities:
            key = e.name.lower()
            if key not in seen_entities or e.confidence > seen_entities[key].confidence:
                seen_entities[key] = e
        merged.entities = list(seen_entities.values())

        # Merge relationships (dedupe by from+type+to)
        seen_rels = {}
        for r in result1.relationships + result2.relationships:
            key = f"{r.from_entity}|{r.relationship.value}|{r.to_entity}".lower()
            if key not in seen_rels or r.confidence > seen_rels[key].confidence:
                seen_rels[key] = r
        merged.relationships = list(seen_rels.values())

        # Merge facts (dedupe by subject+predicate)
        seen_facts = {}
        for f in result1.facts + result2.facts:
            key = f"{f.subject}|{f.predicate}".lower()
            if key not in seen_facts or f.confidence > seen_facts[key].confidence:
                seen_facts[key] = f
        merged.facts = list(seen_facts.values())

        # Merge preferences (dedupe by key)
        seen_prefs = {}
        for p in result1.preferences + result2.preferences:
            key = p.get("key", "")
            if key and (key not in seen_prefs or p.get("confidence", 0) > seen_prefs[key].get("confidence", 0)):
                seen_prefs[key] = p
        merged.preferences = list(seen_prefs.values())

        # Merge temporal events
        merged.temporal_events = result1.temporal_events + result2.temporal_events

        return merged

    def _validate_and_clean(
        self,
        result: ExtractionResult,
        existing_context: Dict[str, Any] = None
    ) -> ExtractionResult:
        """Validate and clean extraction results."""
        # Filter out low-confidence extractions
        result.entities = [e for e in result.entities if e.confidence >= 0.5]
        result.relationships = [r for r in result.relationships if r.confidence >= 0.5]
        result.facts = [f for f in result.facts if f.confidence >= 0.5]

        # Filter out entities with very short names (likely false positives)
        result.entities = [e for e in result.entities if len(e.name) > 1]

        # Normalize entity names (title case)
        for e in result.entities:
            e.name = e.name.strip().title()

        # TODO: Cross-reference with existing_context to update rather than duplicate

        return result


class KnowledgeStore:
    """
    Stores extracted knowledge in the appropriate backends.

    Supports:
    - PostgreSQL for structured storage
    - Neo4j for graph relationships
    - Vector store for semantic search
    """

    def __init__(self, storage, graph=None, vector_store=None):
        """
        Initialize the knowledge store.

        Args:
            storage: Main storage adapter (PostgreSQL)
            graph: Optional knowledge graph adapter (Neo4j)
            vector_store: Optional vector store for semantic search
        """
        self.storage = storage
        self.graph = graph
        self.vector_store = vector_store

    async def store(self, user_id: str, result: ExtractionResult) -> Dict[str, int]:
        """
        Store extraction results in all backends.

        Returns:
            Counts of what was stored
        """
        counts = {
            "entities": 0,
            "relationships": 0,
            "facts": 0,
            "preferences": 0
        }

        # Store preferences in main storage
        if self.storage:
            for pref in result.preferences:
                try:
                    self.storage.save_preference(
                        user_id=user_id,
                        key=pref.get("key", ""),
                        value=pref.get("value", ""),
                        confidence=pref.get("confidence", 0.8)
                    )
                    counts["preferences"] += 1
                except Exception as e:
                    print(f"Error storing preference: {e}")

        # Store in knowledge graph if available
        if self.graph:
            # Store entities
            for entity in result.entities:
                try:
                    self.graph.upsert_entity(
                        user_id=user_id,
                        name=entity.name,
                        type=entity.type.value,
                        attributes=entity.attributes
                    )
                    counts["entities"] += 1
                except Exception as e:
                    print(f"Error storing entity: {e}")

            # Store relationships
            for rel in result.relationships:
                try:
                    self.graph.create_relationship(
                        user_id=user_id,
                        from_entity=rel.from_entity,
                        relationship=rel.relationship.value,
                        to_entity=rel.to_entity,
                        properties=rel.properties
                    )
                    counts["relationships"] += 1
                except Exception as e:
                    print(f"Error storing relationship: {e}")

            # Store facts
            for fact in result.facts:
                try:
                    self.graph.add_fact(
                        user_id=user_id,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        object_value=fact.object_value,
                        confidence=fact.confidence
                    )
                    counts["facts"] += 1
                except Exception as e:
                    print(f"Error storing fact: {e}")

        # Index in vector store for semantic search
        if self.vector_store:
            # Create searchable text from extraction
            for entity in result.entities:
                text = f"{entity.name} ({entity.type.value})"
                if entity.attributes:
                    text += f": {json.dumps(entity.attributes)}"

                try:
                    self.vector_store.upsert(
                        doc_id=f"entity_{user_id}_{entity.name}",
                        content=text,
                        metadata={
                            "user_id": user_id,
                            "type": "entity",
                            "entity_type": entity.type.value,
                            "name": entity.name
                        }
                    )
                except Exception as e:
                    print(f"Error indexing entity: {e}")

        return counts
