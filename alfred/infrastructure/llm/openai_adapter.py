from typing import List, Dict
import os
from alfred.core.interfaces import LLMProvider
from openai import OpenAI

class OpenAIAdapter(LLMProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        # Convert generic history to OpenAI format
        # Filter for keys that OpenAI expects (role, content) to avoid sending extra data
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content
