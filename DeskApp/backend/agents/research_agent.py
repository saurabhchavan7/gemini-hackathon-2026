"""
LifeOS - Agent 4: Intelligent Research Agent
Role: Smart research activation for technical problems, learning, and decisions
"""
from agents.base import AgentBase
from google.genai import types
from services.firestore_service import FirestoreService
from typing import List, Dict, Any, Optional
from datetime import datetime


class ResearchAgent(AgentBase):
    """
    Intelligent Research Agent
    Automatically researches when content warrants investigation
    """
    
    def __init__(self):
        system_instruction = """You are the LifeOS Deep Research Agent.

Your job is to research topics and provide actionable insights with sources.

RESEARCH APPROACH:
1. For CODE ERRORS: Find solutions on Stack Overflow, GitHub, official docs
2. For LEARNING: Find tutorials, courses, documentation
3. For DECISIONS: Find comparisons, reviews, expert opinions
4. For COMPLEX TOPICS: Provide structured breakdown with sources

ALWAYS:
- Cite sources with links
- Be concise but thorough
- Focus on actionable solutions
- Prioritize authoritative sources"""

        # Enable Google Search tool
        self.search_tool = types.Tool(google_search=types.GoogleSearch())
        
        super().__init__(
            model_id="gemini-2.5-flash",
            system_instruction=system_instruction,
            tools=[self.search_tool]
        )
    
    # Keywords that trigger research
    TECHNICAL_KEYWORDS = [
        "error", "exception", "traceback", "failed", "bug", "crash",
        "not working", "issue", "problem", "undefined", "null",
        "cannot", "unable", "invalid", "timeout", "refused"
    ]
    
    LEARNING_KEYWORDS = [
        "learn", "tutorial", "how to", "guide", "course", "understand",
        "explain", "what is", "introduction", "beginner", "advanced"
    ]
    
    DECISION_KEYWORDS = [
        "compare", "vs", "versus", "better", "best", "which one",
        "should i", "recommend", "alternative", "options", "pros cons"
    ]
    
    # Domains that often benefit from research
    RESEARCH_FRIENDLY_DOMAINS = [
        "work_career",
        "education_learning", 
        "health_wellbeing",
        "money_finance",
        "travel_movement"
    ]

    async def process(self, data: dict):
        """
        Intelligent research activation
        
        Triggers for:
        1. Explicit 'research' intent
        2. Technical errors/problems detected
        3. Learning tasks that need resources
        4. Complex decisions requiring comparison
        5. Any action marked as needing research
        """
        
        domain = data.get("domain", "")
        summary = data.get("summary") or data.get("overall_summary", "")
        actions = data.get("actions", [])
        primary_intent = data.get("primary_intent") or data.get("intent", "")
        full_context = data.get("full_context", "")
        user_id = data.get("user_id")
        
        # Combine all text for analysis
        all_text = f"{summary} {full_context}".lower()
        
        # Determine if research is needed
        should_research, research_type, research_query = self._should_research(
            domain=domain,
            actions=actions,
            primary_intent=primary_intent,
            all_text=all_text,
            summary=summary
        )
        
        if not should_research:
            return {"status": "skipped", "reason": "research not needed"}
        
        print(f"[Agent 4] Research triggered: type={research_type}")
        print(f"[Agent 4] Query: {research_query[:100]}...")
        
        try:
            # Craft research prompt based on type
            prompt = self._build_research_prompt(
                research_type=research_type,
                query=research_query,
                domain=domain,
                full_context=full_context[:2000]
            )
            
            # Call Gemini with search grounding
            response = await self._call_gemini(prompt=prompt)
            
            # Extract results
            research_text, sources_count = self._extract_research_results(response)
            
            print(f"[Agent 4] Research complete: {sources_count} sources found")
            print(f"[Agent 4] Summary: {research_text[:200]}...")
            
            # Save research results to Firestore if user_id provided
            if user_id and research_text:
                await self._save_research(
                    user_id=user_id,
                    capture_id=data.get("capture_id"),
                    query=research_query,
                    research_type=research_type,
                    results=research_text,
                    sources_count=sources_count
                )
            
            return {
                "status": "success",
                "research_type": research_type,
                "query": research_query,
                "results": research_text,
                "sources_count": sources_count
            }
            
        except Exception as e:
            print(f"[ERROR] Agent 4 research failed: {e}")
            return {"status": "error", "message": str(e)}

    def _should_research(
        self,
        domain: str,
        actions: list,
        primary_intent: str,
        all_text: str,
        summary: str
    ) -> tuple:
        """
        Determine if research should be triggered
        Returns: (should_research: bool, research_type: str, query: str)
        """
        
        # 1. Check for explicit research intent
        if primary_intent == "research":
            return True, "explicit", summary
        
        # Check actions for research intent
        for action in actions:
            intent = action.get('intent') if isinstance(action, dict) else action.intent
            if intent == "research":
                action_summary = action.get('summary') if isinstance(action, dict) else action.summary
                return True, "explicit", action_summary
        
        # 2. Check for technical errors/problems
        if any(keyword in all_text for keyword in self.TECHNICAL_KEYWORDS):
            # Find the most relevant error context
            for keyword in self.TECHNICAL_KEYWORDS:
                if keyword in all_text:
                    return True, "technical", summary
        
        # 3. Check for learning intent that might need resources
        if primary_intent == "learn" or any(
            keyword in all_text for keyword in self.LEARNING_KEYWORDS
        ):
            return True, "learning", summary
        
        # Check actions for learn intent
        for action in actions:
            intent = action.get('intent') if isinstance(action, dict) else action.intent
            if intent == "learn":
                action_summary = action.get('summary') if isinstance(action, dict) else action.summary
                return True, "learning", action_summary
        
        # 4. Check for comparison/decision needs
        if primary_intent == "compare" or any(
            keyword in all_text for keyword in self.DECISION_KEYWORDS
        ):
            return True, "comparison", summary
        
        # 5. Check if domain typically benefits from research
        # Only trigger if content seems complex enough
        if domain in self.RESEARCH_FRIENDLY_DOMAINS:
            # Check for complexity indicators
            complexity_indicators = [
                "interview", "exam", "investment", "medical", "legal",
                "tax", "visa", "contract", "negotiate", "diagnos"
            ]
            if any(ind in all_text for ind in complexity_indicators):
                return True, "domain_specific", summary
        
        return False, None, None

    def _build_research_prompt(
        self,
        research_type: str,
        query: str,
        domain: str,
        full_context: str
    ) -> str:
        """Build research prompt based on type"""
        
        if research_type == "technical":
            return f"""A user encountered this technical issue:

{query}

Full context:
{full_context}

Search for solutions and provide:
1. The likely cause of this issue
2. Step-by-step solution
3. Common mistakes to avoid
4. Links to relevant Stack Overflow/GitHub/documentation

Be specific and actionable."""

        elif research_type == "learning":
            return f"""A user wants to learn about:

{query}

Context:
{full_context}

Search and provide:
1. Best learning path for this topic
2. Top 3-5 resources (tutorials, courses, documentation)
3. Key concepts to focus on
4. Estimated time to learn
5. Practical projects to try

Prioritize beginner-friendly but authoritative sources."""

        elif research_type == "comparison":
            return f"""A user needs help deciding:

{query}

Context:
{full_context}

Search and provide:
1. Key factors to consider
2. Comparison of top options
3. Pros and cons of each
4. Expert recommendations
5. What most people choose and why

Be balanced and cite sources."""

        elif research_type == "domain_specific":
            domain_prompts = {
                "work_career": "career advice, interview tips, job market insights",
                "health_wellbeing": "medical information, health recommendations, treatment options",
                "money_finance": "financial advice, investment options, tax implications",
                "travel_movement": "travel tips, visa requirements, destination information",
                "education_learning": "educational resources, study strategies, certification paths"
            }
            
            focus = domain_prompts.get(domain, "relevant information")
            
            return f"""Research request in {domain} domain:

{query}

Context:
{full_context}

Focus on: {focus}

Provide:
1. Key information the user needs
2. Important considerations
3. Recommended next steps
4. Authoritative sources

Be thorough but concise."""

        else:
            return f"""Research this topic thoroughly:

{query}

Context:
{full_context}

Provide comprehensive analysis with:
1. Key findings
2. Important details
3. Actionable recommendations
4. Credible sources

Be helpful and specific."""

    def _extract_research_results(self, response) -> tuple:
        """Extract research text and source count from response"""
        
        research_text = ""
        sources_count = 0
        
        # Extract text
        if hasattr(response, 'text'):
            research_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    research_text += part.text
        
        # Extract grounding metadata (sources)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata'):
                grounding = candidate.grounding_metadata
                if hasattr(grounding, 'grounding_chunks'):
                    sources_count = len(grounding.grounding_chunks)
                elif hasattr(grounding, 'web_search_queries'):
                    # Fallback: count search queries as proxy
                    sources_count = len(grounding.web_search_queries)
        
        return research_text.strip(), sources_count

    async def _save_research(
        self,
        user_id: str,
        capture_id: Optional[str],
        query: str,
        research_type: str,
        results: str,
        sources_count: int
    ):
        """Save research results to Firestore"""
        try:
            db = FirestoreService()
            
            research_doc = {
                "query": query,
                "research_type": research_type,
                "results": results[:5000],
                "sources_count": sources_count,
                "created_at": datetime.utcnow().isoformat(),
                "status": "completed",
                "capture_id": capture_id
            }
            
            # Use capture_id as document ID (unified linkage)
            if capture_id:
                doc_ref = db._get_user_ref(user_id).collection("research_results").document(capture_id)
            else:
                doc_ref = db._get_user_ref(user_id).collection("research_results").document()
            
            doc_ref.set(research_doc)
            
            print(f"[Agent 4] Saved research to: research_results/{doc_ref.id}")
            
            # Update main capture with flag
            if capture_id:
                try:
                    field_updates = {
                        "research.has_data": True,
                        "research.completed_at": datetime.utcnow().isoformat(),
                        "research.sources_count": sources_count,
                        "research.query": query,
                        "research.research_type": research_type,
                        "timeline.research_completed": datetime.utcnow().isoformat()
                    }
                    
                    await db.update_capture_fields(user_id, capture_id, field_updates)
                    print(f"[Agent 4] ✓ Research linked to capture {capture_id}")
                    
                except Exception as e:
                    print(f"[Agent 4] WARNING: Failed to update capture: {e}")
                    
        except Exception as e:
            print(f"[ERROR] Failed to save research: {e}")