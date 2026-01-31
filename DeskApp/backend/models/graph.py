from pydantic import BaseModel, Field

class GraphEdge(BaseModel):
 """The Neural Link. Describes how two memories relate to each other."""
 source_id: str = Field(..., description="The ID of the first Memory")
 target_id: str = Field(..., description="The ID of the second Memory")
 
 # Connection Logic
 relationship_type: str = Field(..., description="e.g., 'same_project', 'contradicts', 'supports', 'next_step'")
 similarity_score: float = Field(..., description="0.0 to 1.0 score based on Vector similarity")
 reasoning: str = Field(..., description="The AI's explanation for WHY these are linked")