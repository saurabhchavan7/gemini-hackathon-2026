"""
LifeOS - Agent 7: Proactive Agent
Role: Context-aware assistance without being asked
"""
from agents.base import AgentBase
from core.config import settings

class ProactiveAgent(AgentBase):
    def __init__(self):
        system_instruction = (
            "You are the LifeOS Proactive Assistant. "
            "Analyze events and provide helpful context without being asked:\n"
            "- For events: Check for scheduling conflicts, weather, travel time\n"
            "- For purchases: Suggest price comparisons, reviews, alternatives\n"
            "- For tasks: Estimate time required, suggest optimal timing\n\n"
            "Be brief and actionable."
        )
        super().__init__(
            model_id=settings.PRIMARY_MODEL,
            system_instruction=system_instruction
        )

    async def process(self, data: dict):
        """Runs proactive checks based on intent"""
        
        intent = data.get("intent")
        summary = data.get("summary")
        
        # Only activate for Events and Purchases
        if intent not in ["Event", "Purchase"]:
            return
        
        print(f"[Agent 7] Proactive checking context for: {intent}")
        
        if intent == "Event":
            prompt = (
                f"The user has this event: {summary}\n\n"
                f"Provide 2-3 proactive suggestions such as:\n"
                f"- Checking for scheduling conflicts\n"
                f"- Weather considerations\n"
                f"- Travel time/traffic alerts\n"
                f"- Preparation reminders"
            )
        elif intent == "Purchase":
            prompt = (
                f"The user is considering: {summary}\n\n"
                f"Provide 2-3 helpful tips such as:\n"
                f"- Price comparison advice\n"
                f"- Review highlights\n"
                f"- Alternative options\n"
                f"- Timing recommendations (sales, etc.)"
            )
        
        try:
            response = await self._call_gemini(prompt=prompt)
            
            tips = ""
            if hasattr(response, 'text'):
                tips = response.text
            elif hasattr(response, 'candidates'):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        tips += part.text
            
            print(f"[Agent 7] Proactive tips: {tips[:200]}")
            
            return {"status": "success", "tips": tips}
            
        except Exception as e:
            print(f"[ERROR] Agent 7 failed: {e}")