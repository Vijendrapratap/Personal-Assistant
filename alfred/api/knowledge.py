"""
Knowledge API - Entity management and knowledge graph endpoints.

Provides endpoints for:
- Browsing people and companies entities
- Viewing entity details with relationships
- Knowledge stats (what Alfred knows)
- Learned preferences
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# ============================================
# PYDANTIC MODELS
# ============================================

class EntityRelationship(BaseModel):
    type: str
    target_id: str
    target_name: str


class Entity(BaseModel):
    entity_id: str
    entity_type: str  # 'person', 'company', 'topic'
    name: str
    properties: Dict[str, Any] = {}
    relationships: List[EntityRelationship] = []
    created_at: str
    updated_at: str


class EntitiesResponse(BaseModel):
    entities: List[Entity]
    total: int


class KnowledgeStats(BaseModel):
    people: int
    companies: int
    projects: int
    preferences: int
    total_facts: int


class Preference(BaseModel):
    key: str
    value: str
    confidence: float
    source: str


class PreferencesResponse(BaseModel):
    preferences: List[Preference]


# ============================================
# IN-MEMORY STORAGE (for demo/development)
# In production, this would use Neo4j
# ============================================

# Mock entity storage per user
_entities_store: Dict[str, Dict[str, Entity]] = {}
_preferences_store: Dict[str, List[Preference]] = {}


def _get_user_entities(user_id: str) -> Dict[str, Entity]:
    """Get or initialize entity store for user."""
    if user_id not in _entities_store:
        # Initialize with some demo data
        now = datetime.utcnow().isoformat() + "Z"
        _entities_store[user_id] = {
            "p1": Entity(
                entity_id="p1",
                entity_type="person",
                name="Sarah Chen",
                properties={
                    "role": "Engineering Manager",
                    "company": "TechCorp",
                    "email": "sarah@techcorp.com",
                    "notes": "Met at conference in 2024. Expert in distributed systems."
                },
                relationships=[
                    EntityRelationship(type="works_at", target_id="c1", target_name="TechCorp"),
                    EntityRelationship(type="knows", target_id="p3", target_name="Elena Rodriguez"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "p2": Entity(
                entity_id="p2",
                entity_type="person",
                name="Marcus Johnson",
                properties={
                    "role": "Product Designer",
                    "company": "DesignStudio",
                },
                relationships=[
                    EntityRelationship(type="works_at", target_id="c3", target_name="DesignStudio"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "p3": Entity(
                entity_id="p3",
                entity_type="person",
                name="Elena Rodriguez",
                properties={
                    "role": "CEO",
                    "company": "StartupX",
                },
                relationships=[
                    EntityRelationship(type="leads", target_id="c2", target_name="StartupX"),
                    EntityRelationship(type="knows", target_id="p1", target_name="Sarah Chen"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "p4": Entity(
                entity_id="p4",
                entity_type="person",
                name="David Kim",
                properties={
                    "role": "Software Engineer",
                    "company": "TechCorp",
                },
                relationships=[
                    EntityRelationship(type="works_at", target_id="c1", target_name="TechCorp"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "p5": Entity(
                entity_id="p5",
                entity_type="person",
                name="Lisa Wang",
                properties={
                    "role": "Investor",
                    "company": "VentureCapital",
                },
                relationships=[
                    EntityRelationship(type="invested_in", target_id="c2", target_name="StartupX"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "c1": Entity(
                entity_id="c1",
                entity_type="company",
                name="TechCorp",
                properties={
                    "industry": "Technology",
                    "size": "500+ employees",
                    "website": "techcorp.com",
                },
                relationships=[
                    EntityRelationship(type="employs", target_id="p1", target_name="Sarah Chen"),
                    EntityRelationship(type="employs", target_id="p4", target_name="David Kim"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "c2": Entity(
                entity_id="c2",
                entity_type="company",
                name="StartupX",
                properties={
                    "industry": "SaaS",
                    "size": "10-50 employees",
                },
                relationships=[
                    EntityRelationship(type="led_by", target_id="p3", target_name="Elena Rodriguez"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "c3": Entity(
                entity_id="c3",
                entity_type="company",
                name="DesignStudio",
                properties={
                    "industry": "Design Agency",
                    "size": "10-50 employees",
                },
                relationships=[
                    EntityRelationship(type="employs", target_id="p2", target_name="Marcus Johnson"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "c4": Entity(
                entity_id="c4",
                entity_type="company",
                name="VentureCapital",
                properties={
                    "industry": "Finance",
                    "size": "50-100 employees",
                },
                relationships=[
                    EntityRelationship(type="employs", target_id="p5", target_name="Lisa Wang"),
                ],
                created_at=now,
                updated_at=now,
            ),
            "c5": Entity(
                entity_id="c5",
                entity_type="company",
                name="HealthFirst",
                properties={
                    "industry": "Healthcare",
                    "size": "1000+ employees",
                },
                relationships=[],
                created_at=now,
                updated_at=now,
            ),
        }
    return _entities_store[user_id]


def _get_user_preferences(user_id: str) -> List[Preference]:
    """Get or initialize preferences for user."""
    if user_id not in _preferences_store:
        _preferences_store[user_id] = [
            Preference(
                key="communication_style",
                value="Concise and direct",
                confidence=0.85,
                source="conversation",
            ),
            Preference(
                key="preferred_work_hours",
                value="Morning (6am - 12pm)",
                confidence=0.92,
                source="observation",
            ),
            Preference(
                key="meeting_preference",
                value="Prefers async communication",
                confidence=0.78,
                source="inferred",
            ),
        ]
    return _preferences_store[user_id]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats(current_user_id: str = Depends(get_current_user)):
    """Get statistics about what Alfred knows."""
    entities = _get_user_entities(current_user_id)
    preferences = _get_user_preferences(current_user_id)

    people_count = sum(1 for e in entities.values() if e.entity_type == "person")
    companies_count = sum(1 for e in entities.values() if e.entity_type == "company")

    return KnowledgeStats(
        people=people_count,
        companies=companies_count,
        projects=3,  # Would come from projects API
        preferences=len(preferences),
        total_facts=people_count + companies_count + len(preferences) + 12,  # +12 for other facts
    )


@router.get("/entities", response_model=EntitiesResponse)
async def get_entities(
    entity_type: Optional[str] = Query(None, description="Filter by type: person, company, topic"),
    limit: int = Query(50, ge=1, le=100),
    current_user_id: str = Depends(get_current_user),
):
    """Get entities from the knowledge graph."""
    entities = _get_user_entities(current_user_id)

    result = list(entities.values())

    if entity_type:
        result = [e for e in result if e.entity_type == entity_type]

    result = result[:limit]

    return EntitiesResponse(
        entities=result,
        total=len(result),
    )


@router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Get a specific entity by ID."""
    entities = _get_user_entities(current_user_id)

    if entity_id not in entities:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entities[entity_id]


@router.get("/search")
async def search_entities(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: str = Depends(get_current_user),
):
    """Search entities by name or properties."""
    entities = _get_user_entities(current_user_id)
    query = q.lower()

    results = []
    for entity in entities.values():
        # Search in name
        if query in entity.name.lower():
            results.append(entity)
            continue

        # Search in properties
        for value in entity.properties.values():
            if isinstance(value, str) and query in value.lower():
                results.append(entity)
                break

    return EntitiesResponse(
        entities=results[:limit],
        total=len(results),
    )


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    current_user_id: str = Depends(get_current_user),
):
    """Get learned user preferences."""
    preferences = _get_user_preferences(current_user_id)
    return PreferencesResponse(preferences=preferences)


@router.post("/entities")
async def create_entity(
    entity_type: str,
    name: str,
    properties: Dict[str, Any] = {},
    current_user_id: str = Depends(get_current_user),
):
    """Create a new entity."""
    entities = _get_user_entities(current_user_id)

    entity_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat() + "Z"

    entity = Entity(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        properties=properties,
        relationships=[],
        created_at=now,
        updated_at=now,
    )

    entities[entity_id] = entity
    return entity


@router.put("/entities/{entity_id}")
async def update_entity(
    entity_id: str,
    name: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    current_user_id: str = Depends(get_current_user),
):
    """Update an entity."""
    entities = _get_user_entities(current_user_id)

    if entity_id not in entities:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity = entities[entity_id]

    if name:
        entity.name = name
    if properties:
        entity.properties.update(properties)

    entity.updated_at = datetime.utcnow().isoformat() + "Z"

    return entity


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Delete an entity."""
    entities = _get_user_entities(current_user_id)

    if entity_id not in entities:
        raise HTTPException(status_code=404, detail="Entity not found")

    del entities[entity_id]
    return {"message": "Entity deleted", "entity_id": entity_id}
