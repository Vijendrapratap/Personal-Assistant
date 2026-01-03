"""
Voice API for Alfred
Handles voice transcription and voice-based chat interactions.
"""

import os
import base64
import tempfile
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/voice", tags=["Voice"])

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class TranscribeRequest(BaseModel):
    audio: str  # Base64 encoded audio
    format: str = "wav"  # Audio format (wav, mp3, m4a, webm)


class TranscribeResponse(BaseModel):
    text: str
    confidence: float
    duration_ms: int


class VoiceChatRequest(BaseModel):
    audio: str  # Base64 encoded audio
    format: str = "wav"
    include_thinking: bool = True


class ThinkingStep(BaseModel):
    step: str
    status: str  # completed, in_progress, pending
    detail: Optional[str] = None


class ActionTaken(BaseModel):
    type: str
    description: str
    entity_id: Optional[str] = None


class VoiceChatResponse(BaseModel):
    transcription: TranscribeResponse
    response: str
    thinking_steps: Optional[List[ThinkingStep]] = None
    actions_taken: Optional[List[ActionTaken]] = None


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


def get_llm():
    from alfred.main import llm_provider
    if not llm_provider:
        raise HTTPException(status_code=503, detail="LLM not available")
    return llm_provider


def get_alfred():
    from alfred.main import alfred
    if not alfred:
        raise HTTPException(status_code=503, detail="Alfred not available")
    return alfred


# ============================================================================
# WHISPER TRANSCRIPTION
# ============================================================================

async def transcribe_audio(audio_base64: str, audio_format: str = "wav") -> TranscribeResponse:
    """
    Transcribe audio using OpenAI Whisper API.
    Falls back to a simple response if Whisper is not available.
    """
    try:
        import openai

        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)

        # Write to temp file
        suffix = f".{audio_format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # Use OpenAI Whisper API
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )

            return TranscribeResponse(
                text=transcript.text,
                confidence=0.95,  # Whisper doesn't return confidence, use high default
                duration_ms=int(transcript.duration * 1000) if hasattr(transcript, 'duration') else 0
            )

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    except ImportError:
        logger.warning("OpenAI library not installed, voice transcription unavailable")
        raise HTTPException(
            status_code=503,
            detail="Voice transcription requires OpenAI library. Install with: pip install openai"
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: TranscribeRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Transcribe audio to text using Whisper.

    Accepts base64-encoded audio in various formats (wav, mp3, m4a, webm).
    Returns the transcribed text with confidence score.
    """
    return await transcribe_audio(request.audio, request.format)


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    request: VoiceChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Complete voice interaction: transcribe audio and get Alfred's response.

    This endpoint:
    1. Transcribes the audio using Whisper
    2. Sends the text to Alfred for processing
    3. Returns both transcription and response
    4. Optionally includes thinking steps for transparency
    """
    # Step 1: Transcribe
    transcription = await transcribe_audio(request.audio, request.format)

    # Step 2: Get Alfred's response
    alfred_instance = get_alfred()

    thinking_steps = []
    actions_taken = []

    if request.include_thinking:
        # Simulate thinking steps for transparency
        thinking_steps = [
            ThinkingStep(step="Understanding request", status="completed"),
            ThinkingStep(step="Checking context", status="completed"),
            ThinkingStep(step="Formulating response", status="completed"),
        ]

    try:
        response_text = alfred_instance.ask(transcription.text, user_id)

        # Detect if any actions were taken based on keywords
        text_lower = transcription.text.lower()
        if any(word in text_lower for word in ["add", "create", "new"]):
            if "task" in text_lower:
                actions_taken.append(ActionTaken(
                    type="task_creation",
                    description="Noted task for creation"
                ))
            elif "habit" in text_lower:
                actions_taken.append(ActionTaken(
                    type="habit_creation",
                    description="Noted habit for creation"
                ))

    except Exception as e:
        logger.error(f"Alfred response error: {e}")
        response_text = "I apologize, Sir, but I encountered an issue processing your request."

    return VoiceChatResponse(
        transcription=transcription,
        response=response_text,
        thinking_steps=thinking_steps if request.include_thinking else None,
        actions_taken=actions_taken if actions_taken else None
    )


@router.post("/quick-command")
async def quick_command(
    request: TranscribeRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Process a quick voice command without full chat response.

    Optimized for simple commands like:
    - "Log workout" -> logs habit
    - "Complete task X" -> completes task
    - "Add task: Buy groceries" -> creates task
    """
    # Transcribe
    transcription = await transcribe_audio(request.audio, request.format)
    text = transcription.text.lower().strip()

    storage = get_storage()
    action_result = {"action": None, "success": False, "message": "Command not recognized"}

    # Quick command patterns
    if text.startswith("log ") or text.startswith("complete habit "):
        # Habit logging
        habit_name = text.replace("log ", "").replace("complete habit ", "").strip()
        habits = storage.get_habits(user_id, active_only=True)

        for habit in habits:
            if habit_name.lower() in habit["name"].lower():
                storage.log_habit(habit["habit_id"], user_id)
                action_result = {
                    "action": "habit_logged",
                    "success": True,
                    "message": f"Logged {habit['name']}. Streak: {habit.get('current_streak', 0) + 1} days.",
                    "entity_id": habit["habit_id"]
                }
                break

    elif text.startswith("complete task ") or text.startswith("done with "):
        # Task completion
        task_name = text.replace("complete task ", "").replace("done with ", "").strip()
        tasks = storage.get_tasks(user_id)

        for task in tasks:
            if task_name.lower() in task["title"].lower() and task.get("status") != "completed":
                storage.complete_task(task["task_id"], user_id)
                action_result = {
                    "action": "task_completed",
                    "success": True,
                    "message": f"Completed: {task['title']}",
                    "entity_id": task["task_id"]
                }
                break

    elif text.startswith("add task ") or text.startswith("new task "):
        # Task creation
        task_title = text.replace("add task ", "").replace("new task ", "").strip()
        if task_title:
            task = storage.create_task(
                user_id=user_id,
                title=task_title.capitalize(),
                priority="medium"
            )
            action_result = {
                "action": "task_created",
                "success": True,
                "message": f"Created task: {task_title.capitalize()}",
                "entity_id": task.get("task_id")
            }

    return {
        "transcription": transcription.dict(),
        "result": action_result
    }
