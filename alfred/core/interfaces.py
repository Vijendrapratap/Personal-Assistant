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
    def save_chat(self, user_id: str, role: str, content: str):
        pass
    
    @abstractmethod
    def get_chat_history(self, user_id: str) -> List[Dict[str, str]]:
        pass
    
    @abstractmethod
    def save_preference(self, user_id: str, key: str, value: str):
        pass

    @abstractmethod
    def get_preferences(self, user_id: str) -> Dict[str, str]:
        pass
