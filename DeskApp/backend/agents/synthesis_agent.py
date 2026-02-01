# ============================================
# FILE 1: synthesis_agent.py
# ============================================
"""
LifeOS - Agent 5: Synthesis Agent
Role: Combines multiple captures into comprehensive briefs
"""
from agents.base import AgentBase
from typing import List, Dict

class SynthesisAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Synthesis Agent. Your role is to analyze multiple related captures "
            "and create comprehensive project briefs, summaries, or reports.\n\n"
            "When given multiple memories:\n"
            "1. Identify common themes and connections\n"
            "2. Organize information logically\n"
            "3. Create structured brief with clear sections\n"
            "4. Highlight key takeaways and action items\n"
            "5. Suggest next steps"
        )
        super().__init__(
            model_id="gemini-2.5-flash",
            system_instruction=system_instruction
        )

    async def synthesize_memories(self, memories: List[Dict]) -> Dict:
        """Takes multiple memory objects and creates a comprehensive brief"""
        
        if len(memories) < 2:
            return {"status": "skip", "message": "Need at least 2 memories to synthesize"}
        
        print(f"[Agent 5] Synthesis combining {len(memories)} memories")
        
        # Build context from all memories
        context_parts = []
        for i, mem in enumerate(memories, 1):
            context_parts.append(
                f"Memory {i}:\n"
                f"Title: {mem.get('title', 'Untitled')}\n"
                f"Summary: {mem.get('one_line_summary', '')}\n"
                f"Category: {mem.get('category', 'Unknown')}\n"
                f"Tags: {', '.join(mem.get('tags', []))}\n"
            )
        
        combined_context = "\n---\n".join(context_parts)
        
        prompt = (
            f"Analyze these {len(memories)} related captures and create a comprehensive brief:\n\n"
            f"{combined_context}\n\n"
            f"Generate a structured synthesis with: Executive Summary, Key Findings, Analysis, Recommendations, Next Steps"
        )
        
        try:
            response = await self._call_gemini(prompt=prompt)
            
            synthesis_text = ""
            if hasattr(response, 'text'):
                synthesis_text = response.text
            elif hasattr(response, 'candidates'):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        synthesis_text += part.text
            
            print(f"[Agent 5] Synthesis complete: {len(synthesis_text)} characters")
            
            return {
                "status": "success",
                "synthesis": synthesis_text,
                "source_count": len(memories)
            }
            
        except Exception as e:
            print(f"[ERROR] Agent 5 synthesis failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process(self, data: dict):
        """Event bus handler - not used for Agent 5 (manual trigger)"""
        pass
