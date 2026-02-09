"""
LifeOS - Agent 8: Intelligent Resource Finder
Role: Autonomously decides if resources are needed and finds them
"""
from agents.base import AgentBase
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from core.config import settings
import re

class ResourceDecision(BaseModel):
    """AI's decision on whether resources are needed"""
    needs_resources: bool = Field(..., description="Does this task need learning resources?")
    reasoning: str = Field(..., description="Why resources are/aren't needed")
    resource_count: int = Field(default=3, ge=1, le=5, description="How many resources to find (1-5)")
    resource_types: List[str] = Field(
        default_factory=list,
        description="What types: documentation, video, article, tutorial, code_example"
    )
    complexity: str = Field(..., description="Task complexity: 'beginner', 'intermediate', 'advanced'")

class Resource(BaseModel):
    """Single resource recommendation"""
    url: str
    title: str
    description: str
    type: str
    source: str
    authority_score: int
    relevance_score: int
    verified: bool
    thumbnail_url: Optional[str] = None

class ResourceRecommendations(BaseModel):
    """Collection of recommended resources"""
    resources: List[Resource] = Field(default_factory=list)
    summary: str
    learning_path: str

class ResourceFinderAgent(AgentBase):
    def __init__(self):
        self.decision_instruction = (
            "You are an intelligent learning assistant. Analyze tasks and autonomously decide "
            "if the user would benefit from learning resources.\n\n"
            
            "DECISION CRITERIA:\n"
            "- Resources ARE needed: Learning new skills, technical tasks, complex problems, unfamiliar tools\n"
            "- Resources NOT needed: Simple routine tasks, scheduling, administrative work\n\n"
            
            "RESOURCE COUNT LOGIC:\n"
            "- Simple topic (1-2 resources): Single concept, quick learning\n"
            "- Moderate topic (3 resources): Standard learning need\n"
            "- Complex topic (4-5 resources): Deep, multi-faceted learning\n\n"
            
            "Use intelligence. Be selective. Not every task needs resources."
        )
        
        self.search_instruction = "You are a web search expert. Find high-quality learning resources."
        self.parse_instruction = "You are a resource curator. Extract and structure resources in JSON format."
        
        from google.genai import types
        self.search_tool = types.Tool(google_search=types.GoogleSearch())
        
        super().__init__(
            model_id=settings.PRIMARY_MODEL,
            system_instruction=self.decision_instruction,
            tools=None
        )

    async def decide_if_resources_needed(self, task_data: dict) -> Optional[ResourceDecision]:
        """AI autonomously decides if resources are needed"""
        
        task_title = task_data.get('summary', '')
        full_context = task_data.get('full_context', '')
        intent = task_data.get('intent', '')
        category = task_data.get('category', '')
        
        prompt = (
            f"Analyze this task and decide if learning resources would help:\n\n"
            f"Task: {task_title}\n"
            f"Intent: {intent}\n"
            f"Category: {category}\n"
            f"Context: {full_context[:500]}\n\n"
            f"Should I find learning resources for this task? Use your intelligence to decide."
        )
        
        try:
            from google import genai
            from google.genai import types
            from core.config import settings
            
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model=settings.PRIMARY_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.decision_instruction,
                    response_mime_type="application/json",
                    response_schema=ResourceDecision
                )
            )
            
            if response.parsed:
                decision = response.parsed
                print(f"[Agent 8] Decision: needs_resources={decision.needs_resources}")
                print(f"[Agent 8] Reasoning: {decision.reasoning}")
                
                if decision.needs_resources:
                    print(f"[Agent 8] Will find {decision.resource_count} resources")
                    print(f"[Agent 8] Types: {', '.join(decision.resource_types)}")
                
                return decision
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Agent 8 decision failed: {e}")
            return None

    async def find_resources(
        self, 
        task_title: str, 
        task_context: Optional[str] = None,
        resource_count: int = 3,
        resource_types: List[str] = None
    ) -> Dict:
        """Find resources based on AI's decision"""
        
        try:
            print(f"[Agent 8] Finding {resource_count} resources for '{task_title}'")
            
            context_info = f"\nContext: {task_context}" if task_context else ""
            type_preference = f"\nPrefer: {', '.join(resource_types)}" if resource_types else ""
            
            search_prompt = (
                f"Search the web for the {resource_count} BEST learning resources about:\n\n"
                f"Topic: {task_title}{context_info}{type_preference}\n\n"
                f"Find: Official documentation, video tutorials, comprehensive articles, code examples\n"
                f"For each: note URL, title, and why it's valuable"
            )
            
            from google import genai
            from google.genai import types
            from core.config import settings
            
            search_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            print("[Agent 8] Step 1: Searching web")
            
            search_response = search_client.models.generate_content(
                model=settings.PRIMARY_MODEL,
                contents=search_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.search_instruction,
                    tools=[self.search_tool]
                )
            )
            
            search_results = ""
            if hasattr(search_response, 'text'):
                search_results = search_response.text
            elif hasattr(search_response, 'candidates') and search_response.candidates:
                for part in search_response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        search_results += part.text
            
            if not search_results:
                return {"status": "error", "message": "No search results"}
            
            print(f"[Agent 8] Got search results ({len(search_results)} chars)")
            
            # STEP 2: Parse into structured format
            print("[Agent 8] Step 2: Parsing results")
            
            parse_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            parse_prompt = (
                f"Extract the {resource_count} BEST resources from these search results:\n\n"
                f"{search_results}\n\n"
                f"Return JSON with structure: resources, summary, learning_path\n"
                f"Each resource needs: url, title, description, type, source, "
                f"authority_score, relevance_score, verified, thumbnail_url"
            )
            
            parse_response = parse_client.models.generate_content(
                model=settings.PRIMARY_MODEL,
                contents=parse_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.parse_instruction,
                    response_mime_type="application/json",
                    response_schema=ResourceRecommendations
                )
            )
            
            if parse_response.parsed:
                result_data = parse_response.parsed
                
                validated_resources = []
                for res in result_data.resources:
                    if self._is_valid_url(res.url):
                        res.source = self._extract_domain(res.url)
                        res.verified = True
                        
                        if 'youtube' in res.url.lower():
                            res.thumbnail_url = self._get_youtube_thumbnail(res.url)
                        
                        validated_resources.append(res)
                
                print(f"[Agent 8] Parsed {len(validated_resources)} resources")
                
                return {
                    "status": "success",
                    "task_title": task_title,
                    "resources": [r.model_dump() for r in validated_resources],
                    "summary": result_data.summary,
                    "learning_path": result_data.learning_path,
                    "resource_count": len(validated_resources)
                }
            else:
                return {"status": "error", "message": "Could not parse results"}
                
        except Exception as e:
            print(f"[ERROR] Agent 8 find_resources failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def _get_youtube_thumbnail(self, url: str) -> Optional[str]:
        """Extract YouTube video thumbnail"""
        try:
            video_id = None
            if 'youtu.be/' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            elif 'youtube.com/watch?v=' in url:
                video_id = url.split('v=')[1].split('&')[0]
            
            if video_id:
                return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        except:
            pass
        return None
    
    async def process(self, data: dict):
        """Event bus handler - AI decides if resources are needed"""
        
        print("[Agent 8] Analyzing if task needs resources")
        
        decision = await self.decide_if_resources_needed(data)
        
        if not decision:
            print("[Agent 8] Decision failed, skipping")
            return
        
        if decision.needs_resources:
            print(f"[Agent 8] Resources needed: {decision.reasoning}")
            
            user_id = data.get('user_id')
            capture_id = data.get('capture_id')
            task_title = data.get('summary', '')
            full_context = data.get('full_context', '')
            
            result = await self.find_resources(
                task_title=task_title,
                task_context=full_context,
                resource_count=decision.resource_count,
                resource_types=decision.resource_types
            )
            
            if result['status'] == 'success':
                from services.firestore_service import FirestoreService
                db = FirestoreService()
                
                resource_doc = {
                    "task_title": task_title,
                    "resources": result['resources'],
                    "summary": result['summary'],
                    "learning_path": result['learning_path'],
                    "ai_decision": decision.model_dump(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "user_feedback": None,
                    "capture_id": capture_id,
                    "metadata": {
                        "agent_version": "1.0",
                        "resource_count": result['resource_count'],
                        "complexity": decision.complexity
                    }
                }
                
                # Use capture_id as document ID (unified linkage)
                if capture_id:
                    doc_ref = db._get_user_ref(user_id).collection("task_resources").document(capture_id)
                else:
                    doc_ref = db._get_user_ref(user_id).collection("task_resources").document()
                
                doc_ref.set(resource_doc)
                
                print(f"[Agent 8] Saved resources to: task_resources/{doc_ref.id}")
                
                # Update main capture with flag
                if capture_id:
                    try:
                        field_updates = {
                            "resources.has_data": True,
                            "resources.completed_at": datetime.utcnow().isoformat(),
                            "resources.resources_count": result['resource_count'],
                            "resources.summary": result['summary'][:500] if result.get('summary') else "",
                            "timeline.resources_completed": datetime.utcnow().isoformat()
                        }
                        
                        await db.update_capture_fields(user_id, capture_id, field_updates)
                        print(f"[Agent 8] ✓ Resources linked to capture {capture_id}")
                        
                    except Exception as e:
                        print(f"[Agent 8] WARNING: Failed to update capture: {e}")
                
                resource_titles = [r['title'][:50] for r in result['resources']]
                print(f"[Agent 8] Resources: {resource_titles}")
            else:
                print(f"[ERROR] Failed to find resources: {result.get('message')}")
        else:
            print(f"[Agent 8] No resources needed: {decision.reasoning}")