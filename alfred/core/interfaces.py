from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Abstract Base Class (The Contract)
class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        """Takes text + history, returns text."""
        pass

class VectorDBProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> str:
        """Takes a query, returns context."""
        pass

# Retaining MemoryStorage from previous step to satisfy persistent storage requirement
class MemoryStorage(ABC):
    @abstractmethod
    def save_learning(self, user_id: str, content: str, original_query: Optional[str] = None):
        pass

    @abstractmethod
    def create_user(self, user_id: str, email: str, password_hash: str) -> bool:
        """Create a new user. Returns True if successful."""
        pass

    @abstractmethod
    def get_user_credentials(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user credentials by email (returns dict with user_id, password_hash)."""
        pass

    @abstractmethod
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile as a dictionary."""
        pass

    @abstractmethod
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update user profile fields."""
        pass
    
    @abstractmethod
    def get_chat_history(self, user_id: str) -> List[Dict[str, str]]:
    @abstractmethod
    def save_preference(self, user_id: str, key: str, value: str):
        pass

    @abstractmethod
    def get_preferences(self, user_id: str) -> Dict[str, str]:
        pass
