
# ============================================
# FILE 2: graph_agent.py  
# ============================================
"""
LifeOS - Agent 6: Knowledge Graph Agent
Role: Discovers relationships between memories
"""
from agents.base import AgentBase
from typing import List, Dict, Optional
from datetime import datetime

class GraphAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Knowledge Graph Agent. Your role is to analyze memories "
            "and identify meaningful connections between them.\n\n"
            "Connection Types:\n"
            "- same_project: Related to same work/personal project\n"
            "- prerequisite: One builds upon the other\n"
            "- contradicts: Contains conflicting information\n"
            "- supports: Provides evidence for same conclusion\n"
            "- related_topic: Shares similar themes or subjects\n"
            "- part_of_sequence: Steps in a larger process\n\n"
            "For each connection provide:\n"
            "1. Relationship type\n"
            "2. Confidence score (0.0-1.0)\n"
            "3. Brief reasoning\n\n"
            "Only suggest connections with confidence > 0.6"
        )
        super().__init__(
            model_id="gemini-2.5-flash",
            system_instruction=system_instruction
        )

    async def analyze_connection(self, memory_a: Dict, memory_b: Dict) -> Optional[Dict]:
        """Analyzes if two memories are connected"""
        
        print(f"[Agent 6] Analyzing connection: '{memory_a.get('title')}' <-> '{memory_b.get('title')}'")
        
        prompt = (
            f"Analyze these two memories and determine if they're connected:\n\n"
            f"Memory A:\n"
            f"Title: {memory_a.get('title', 'Untitled')}\n"
            f"Summary: {memory_a.get('one_line_summary', '')}\n"
            f"Category: {memory_a.get('category', 'Unknown')}\n"
            f"Tags: {', '.join(memory_a.get('tags', []))}\n\n"
            f"Memory B:\n"
            f"Title: {memory_b.get('title', 'Untitled')}\n"
            f"Summary: {memory_b.get('one_line_summary', '')}\n"
            f"Category: {memory_b.get('category', 'Unknown')}\n"
            f"Tags: {', '.join(memory_b.get('tags', []))}\n\n"
            f"Are these connected? Respond in JSON: "
            f"{{\"connected\": true/false, \"relationship\": \"type\", \"confidence\": 0.0-1.0, \"reasoning\": \"explanation\"}}"
        )
        
        try:
            response = await self._call_gemini(prompt=prompt)
            
            result_text = ""
            if hasattr(response, 'text'):
                result_text = response.text
            elif hasattr(response, 'candidates'):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        result_text += part.text
            
            # Parse JSON
            import json
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                connection_data = json.loads(result_text)
            except:
                connected = "true" in result_text.lower()
                if not connected:
                    return None
                connection_data = {
                    "connected": True,
                    "relationship": "related_topic",
                    "confidence": 0.7,
                    "reasoning": "Topics appear related"
                }
            
            if connection_data.get("connected") and connection_data.get("confidence", 0) > 0.6:
                print(f"[Agent 6] Connection found: {connection_data.get('relationship')} (confidence: {connection_data.get('confidence')})")
                return {
                    "source_id": memory_a.get("id"),
                    "target_id": memory_b.get("id"),
                    "relationship": connection_data.get("relationship"),
                    "confidence": connection_data.get("confidence"),
                    "reasoning": connection_data.get("reasoning"),
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                print(f"[Agent 6] No strong connection (confidence: {connection_data.get('confidence', 0)})")
                return None
                
        except Exception as e:
            print(f"[ERROR] Agent 6 analysis failed: {e}")
            return None

    async def process_batch(self, memories: List[Dict]) -> List[Dict]:
        """Analyzes a batch of memories to find all connections"""
        
        if len(memories) < 2:
            print("[Agent 6] Need at least 2 memories to analyze")
            return []
        
        print(f"[Agent 6] Analyzing {len(memories)} memories for connections")
        
        connections = []
        total_comparisons = (len(memories) * (len(memories) - 1)) // 2
        print(f"[Agent 6] Will perform {total_comparisons} comparisons")
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                connection = await self.analyze_connection(memories[i], memories[j])
                if connection:
                    connections.append(connection)
        
        print(f"[Agent 6] Found {len(connections)} connections out of {total_comparisons} comparisons")
        return connections

    async def process(self, data: dict):
        """Event bus handler - usually runs as background batch job"""
        print(f"[Agent 6] Noting new memory: {data.get('summary', '')}")
        pass