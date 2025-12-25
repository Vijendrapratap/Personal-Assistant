import os
import sys

# Ensure we can find the modules if running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alfred.infrastructure.llm.openai_adapter import OpenAIAdapter
from alfred.infrastructure.llm.ollama_adapter import OllamaAdapter
from alfred.core.interfaces import LLMProvider

# SETTING: Choose your brain
# MODEL_TYPE = "OLLAMA"
MODEL_TYPE = os.getenv("ALFRED_MODEL_TYPE", "OPENAI") 

def get_llm_provider() -> LLMProvider:
    if MODEL_TYPE == "OPENAI":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        return OpenAIAdapter(api_key=api_key)
    elif MODEL_TYPE == "OLLAMA":
        return OllamaAdapter()
    else:
        raise ValueError(f"Unknown MODEL_TYPE: {MODEL_TYPE}")
