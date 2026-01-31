"""
LifeOS - Perception Agent
Role: Multimodal Ingestion (OCR + Transcription)
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from agents.base import AgentBase
from core.config import settings
from google.genai import types
from services.cache_service import CacheService

class PerceptionResult(BaseModel):
    """The structured output for the Perception stage"""
    ocr_text: str = Field(..., description="Complete text extracted from the screenshot")
    audio_transcript: Optional[str] = Field(None, description="Verbatim transcript of the audio file")
    visual_description: str = Field(..., description="A technical description of what is visible in the UI")

class PerceptionAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the Perception Engine for LifeOS. Your task is to extract all visible text "
            "from screenshots (OCR) and transcribe any provided audio. "
            "Be extremely precise. If you see code, transcribe it exactly. "
            "If you see a UI, describe the active elements. "
            "Return the data in the requested JSON structure."
        )
        super().__init__(model_id=settings.PERCEPTION_MODEL, system_instruction=system_instruction)
        self.cache = CacheService()

    async def process(self, screenshot_bytes: Optional[bytes] = None, audio_bytes: Optional[bytes] = None) -> PerceptionResult:
        """
        Processes raw bytes into a PerceptionResult.
        Uses cache to avoid redundant API calls during testing.
        """
        # Check cache for screenshot
        if screenshot_bytes:
            cached_result = self.cache.get(screenshot_bytes, max_age_minutes=60)
            if cached_result:
                print("[Agent 1] Using cached OCR result")
                return PerceptionResult(**cached_result)
        
        print("[Agent 1] No cache - calling Gemini API")
        
        # No cache hit - call Gemini API
        attachments = []
        prompt = "Analyze these inputs and extract all text and descriptions."

        if screenshot_bytes:
            attachments.append(types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png"))
        
        if audio_bytes:
            attachments.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"))

        # Call the base class engine
        result = await self._call_gemini(
            prompt=prompt,
            response_model=PerceptionResult,
            attachments=attachments
        )
        
        # Cache the result for future use
        if screenshot_bytes and result:
            self.cache.set(screenshot_bytes, result.model_dump())
        
        return result