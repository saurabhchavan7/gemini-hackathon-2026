"""
Gemini 3 Model Configuration for Hackathon Compliance
All agents use Gemini 3 API models
"""
from . import models_config

class GeminiModels:
    """Centralized Gemini 3 model configuration (from models_config.py)"""

    # PRIMARY MODEL - Gemini 3 Flash Preview (required for hackathon)
    PRIMARY_MODEL = models_config.GEMINI_PRIMARY_MODEL

    # ALTERNATIVE - Gemini 3 Pro Preview (higher quality, slower)
    PRO_MODEL = models_config.GEMINI_PRO_MODEL

    # For vision/OCR tasks
    VISION_MODEL = models_config.GEMINI_VISION_MODEL

    # For audio transcription (Gemini 3 supports audio)
    AUDIO_MODEL = models_config.GEMINI_AUDIO_MODEL

    # For embeddings (latest)
    EMBEDDING_MODEL = models_config.GEMINI_EMBEDDING_MODEL

    @classmethod
    def get_model(cls, task_type: str = "default") -> str:
        """
        Get appropriate Gemini 3 model for task

        Args:
            task_type: "default", "vision", "audio", "pro", "embedding"
        """
        task_map = {
            "default": cls.PRIMARY_MODEL,
            "vision": cls.VISION_MODEL,
            "audio": cls.AUDIO_MODEL,
            "pro": cls.PRO_MODEL,
            "embedding": cls.EMBEDDING_MODEL
        }
        return task_map.get(task_type, cls.PRIMARY_MODEL)

    @classmethod
    def get_display_name(cls) -> str:
        """Return model name for display/logging"""
        return "Gemini 3 Flash Preview"