"""
Gemini 3 Model Configuration for Hackathon Compliance
All agents use Gemini 3 API models
"""

class GeminiModels:
    """Centralized Gemini 3 model configuration"""
    
    # PRIMARY MODEL - Gemini 3 Flash Preview (required for hackathon)
    PRIMARY_MODEL = "gemini-3-flash-preview"
    
    # ALTERNATIVE - Gemini 3 Pro Preview (higher quality, slower)
    PRO_MODEL = "gemini-3-pro-preview"
    
    # For vision/OCR tasks
    VISION_MODEL = "gemini-3-flash-preview"
    
    # For audio transcription (use Gemini 3 if available, fallback to 2.5)
    AUDIO_MODEL = "gemini-3-flash-preview"
    
    # For embeddings (latest)
    EMBEDDING_MODEL = "text-embedding-004"
    
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