"""
LifeOS - Agent 4: Deep Research Agent
Role: Automatically researches code errors and complex topics
"""
from agents.base import AgentBase
from google.genai import types
from services.firestore_service import FirestoreService


class ResearchAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Deep Research Agent. Your role is to analyze technical problems and provide solutions.\n\n"
            "When you see:\n"
            "- Code errors: Search Stack Overflow, GitHub issues, official documentation\n"
            "- Technical questions: Find authoritative sources and best practices\n"
            "- Product research: Compare options and provide recommendations\n\n"
            "Always cite sources with links. Be concise but thorough."
        )
        
        # Enable Google Search tool
        self.search_tool = types.Tool(google_search=types.GoogleSearch())
        
        super().__init__(
            model_id="gemini-2.5-flash",
            system_instruction=system_instruction,
            tools=[self.search_tool]
        )

    async def process(self, data: dict):
        """Triggered for 'Research' intent or when code errors detected"""
        
        intent = data.get("intent")
        summary = data.get("summary", "")
        user_id = data.get("user_id")
        
        # Check if this looks like a technical problem
        error_keywords = ["error", "exception", "traceback", "failed", "bug", 
                         "not working", "crash", "issue", "problem"]
        is_technical = any(keyword in summary.lower() for keyword in error_keywords)
        
        # Only activate for Research intent or technical issues
        if intent != "Research" and not is_technical:
            return
        
        print(f"[Agent 4] Research analyzing: {summary[:80]}")
        
        # Craft research-focused prompt
        if is_technical:
            prompt = (
                f"A user encountered this technical issue: {summary}\n\n"
                f"Search for solutions on Stack Overflow, GitHub, and official documentation. "
                f"Provide:\n"
                f"1. The likely cause\n"
                f"2. Step-by-step solution\n"
                f"3. Links to relevant sources"
            )
        else:
            prompt = f"Research this topic thoroughly: {summary}\n\nProvide comprehensive analysis with credible sources."
        
        try:
            # Call Gemini with search grounding enabled
            response = await self._call_gemini(prompt=prompt)
            
            # Extract grounding metadata (sources)
            sources_found = 0
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding = candidate.grounding_metadata
                    if hasattr(grounding, 'grounding_chunks'):
                        sources_found = len(grounding.grounding_chunks)
            
            print(f"[Agent 4] Research complete: Found {sources_found} sources")
            
            # Extract text response
            research_text = ""
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        research_text += part.text
            
            print(f"[Agent 4] Research summary: {research_text[:150]}")
            
            return {
                "status": "success",
                "research_text": research_text,
                "sources_count": sources_found
            }
            
        except Exception as e:
            print(f"[ERROR] Agent 4 research failed: {e}")
            return {"status": "error", "message": str(e)}