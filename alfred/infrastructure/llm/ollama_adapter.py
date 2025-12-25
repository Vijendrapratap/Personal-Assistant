from typing import List, Dict
import requests
from alfred.core.interfaces import LLMProvider

class OllamaAdapter(LLMProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        # Construct the prompt using history if needed, or send as context
        # Simplified Ollama API mostly handles one prompt, but chat endpoint exists.
        # Using the generate endpoint as per user example, but adapting slightly if history is needed.
        # For strict compliance with user snippet which used /api/generate with just prompt:
        
        # NOTE: User snippet used /api/generate which is single turn. 
        # For multi-turn, /api/chat is better, but I will stick to their snippet logic 
        # but perhaps concatenate history if I strictly use generate, or just switch to /api/chat if permitted.
        # User snippet:
        # payload = {"model": "llama3", "prompt": prompt, "stream": False}
        
        # If I want to support history, I should probably concatenate it into the prompt 
        # or use the /api/chat endpoint. 
        # I'll stick to the user's explicit request for the structure, but upgrade to /api/chat for correctness
        # OR just follow the snippet exactly.
        # The user snippet was: res = requests.post("http://localhost:11434/api/generate", json=payload)
        
        # I will use /api/chat to support history properly while keeping the class structure.
        
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }
        
        try:
            res = requests.post(f"{self.base_url}/api/chat", json=payload)
            res.raise_for_status()
            # /api/chat response structure
            return res.json()['message']['content']
        except Exception:
            # Fallback to the user's exact snippet if /chat fails or just for safety?
            # User snippet was /api/generate. Let's support that as fallback or alternative.
            payload_gen = {
                "model": self.model_name, 
                "prompt": prompt, 
                "stream": False
            }
            res = requests.post(f"{self.base_url}/api/generate", json=payload_gen)
            return res.json()['response']
