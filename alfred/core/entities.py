from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class UserPreference:
    key: str
    value: str

@dataclass
class Learning:
    topic: str
    content: str
    original_query: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class UserProfile:
    bio: str = ""
    work_type: str = ""
    voice_id: str = "default"
    personality_prompt: str = "Standard Butler"
    interaction_type: str = "formal" # formal, casual, terse

@dataclass
class UserCredentials:
    email: str
    password_hash: str

@dataclass
class UserContext:
    user_id: str
    preferences: Dict[str, str] = field(default_factory=dict)
    profile: Optional[UserProfile] = None
