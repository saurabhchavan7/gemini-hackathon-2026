import asyncio
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Any, List, Callable
from google import genai
from google.genai import types
from pydantic import BaseModel
from core.config import settings

T = TypeVar("T", bound=BaseModel)

class AgentBase(ABC):
    """
    Abstract Base Class for all LifeOS Agents.
    Every agent inherits from this.
    """

    def __init__(self, model_id: str, system_instruction: str, tools: Optional[List[Callable]] = None):
        """
        Initializes the agent with a specific model and behavior guide.

        Args:
            model_id: The ID of the Gemini model (e.g., 'gemini-2.5-flash')
            system_instruction: The personality and rules for this agent
            tools: Optional list of Python functions that Gemini can call
        """
        self.model_id = model_id
        self.system_instruction = system_instruction
        self.tools = tools
        
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def _call_gemini(
        self, 
        prompt: str, 
        response_model: Optional[Type[T]] = None,
        attachments: Optional[list] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Core engine that sends data to Gemini and returns validated results.
        Includes exponential backoff for rate limiting.
        
        Args:
            prompt: The user input or specific command for the agent
            response_model: A Pydantic class to force structured output
            attachments: Optional files (images/audio) to analyze
            max_retries: Number of retry attempts for rate limit errors
        """
        for attempt in range(max_retries):
            try:
                # Prepare configuration
                config = {
                    "system_instruction": self.system_instruction,
                    "temperature": 1.0,
                }

                if response_model:
                    config["response_mime_type"] = "application/json"
                    config["response_schema"] = response_model

                if self.tools:
                    config["tools"] = self.tools

                # Build the content parts
                content_parts = [prompt]
                if attachments:
                    content_parts.extend(attachments)

                # Execute the call
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=content_parts,
                    config=types.GenerateContentConfig(**config)
                )

                # Return parsed Pydantic object if model provided, else raw response
                if response_model and response.parsed:
                    return response.parsed
                return response

            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s
                        print(f"[RATE_LIMIT] Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"[ERROR] Rate limit exhausted after {max_retries} attempts")
                        raise e
                else:
                    # For other errors, fail immediately
                    print(f"[ERROR] {self.__class__.__name__}: {error_str}")
                    raise e

    @abstractmethod
    async def process(self, *args, **kwargs):
        """
        Every agent must implement its own 'process' logic.
        """
        pass