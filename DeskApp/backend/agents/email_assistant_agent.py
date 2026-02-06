"""
LifeOS - Agent 9: Email Intelligence Assistant
Role: Analyzes yesterday's emails and drafts replies for forgotten messages
"""
from agents.base import AgentBase
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from services.gmail_service import GmailService
from services.firestore_service import FirestoreService

class EmailAnalysis(BaseModel):
    """AI's analysis of whether email needs reply"""
    needs_reply: bool = Field(..., description="Does this email require a response?")
    urgency: int = Field(..., ge=1, le=5, description="How urgent is the reply? 1=low, 5=critical")
    reasoning: str = Field(..., description="Why does/doesn't this need a reply?")
    reply_context: str = Field(..., description="What should the reply address?")
    suggested_tone: str = Field(..., description="professional, friendly, or brief")

class DraftEmail(BaseModel):
    """Generated email draft"""
    subject: str
    body: str
    tone: str

class EmailAssistantAgent(AgentBase):
    def __init__(self, user_id: str):
        self.user_id = user_id
        system_instruction = (
            "You are an intelligent email assistant. Your role is to help users manage their inbox "
            "by identifying emails that need replies and drafting appropriate responses.\n\n"
            
            "EMAIL ANALYSIS RULES:\n"
            "- NEED replies: Direct questions, requests for info/action, important business comms\n"
            "- DON'T need replies: FYI messages, automated notifications, newsletters, social pleasantries\n\n"
            
            "URGENCY SCORING: 1=Low (can wait), 3=Medium (1-2 days), 5=Critical (immediate)\n\n"
            
            "TONE SELECTION:\n"
            "- professional: Boss, clients, formal business\n"
            "- friendly: Colleagues, teammates, casual business\n"
            "- brief: Quick confirmations, simple questions\n\n"
            
            "DRAFT RULES:\n"
            "- Match original email's tone and formality\n"
            "- Be brief but complete\n"
            "- Include appropriate signature\n"
        )
        super().__init__(
            model_id="gemini-2.5-flash",
            system_instruction=system_instruction
        )
    
    async def analyze_email(self, email: Dict) -> Optional[EmailAnalysis]:
        """Analyze if email needs reply using AI"""
        
        try:
            if self._should_auto_skip(email):
                print(f"[Agent 9] Auto-skip: {email['subject'][:50]}")
                return None
            
            prompt = (
                f"Analyze this email and determine if it needs a reply:\n\n"
                f"From: {email['from_name']} <{email['from_email']}>\n"
                f"Subject: {email['subject']}\n"
                f"Date: {email['date']}\n\n"
                f"Email Body:\n{email['body']}\n\n"
                f"Questions:\n"
                f"1. Does this require a response?\n"
                f"2. How urgent? (1-5)\n"
                f"3. Why?\n"
                f"4. What should reply address?\n"
                f"5. What tone?\n"
            )
            
            from google import genai
            from google.genai import types
            from core.config import settings
            
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                    response_schema=EmailAnalysis
                )
            )
            
            if response.parsed:
                analysis = response.parsed
                
                if analysis.needs_reply:
                    print(f"[Agent 9] Needs reply: {email['subject'][:50]}")
                    print(f"[Agent 9] Urgency: {analysis.urgency}/5 - {analysis.reasoning}")
                else:
                    print(f"[Agent 9] No reply needed: {email['subject'][:50]}")
                
                return analysis
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Email analysis failed: {e}")
            return None
    
    def _should_auto_skip(self, email: Dict) -> bool:
        """Auto-skip newsletters, noreply, and automated emails"""
        
        from_email = email['from_email'].lower()
        body = email.get('body', '').lower()
        labels = email.get('labels', [])
        
        skip_patterns = [
            'noreply@', 'no-reply@', 'donotreply@',
            'notification@', 'notifications@',
            'newsletter@', 'updates@', 'marketing@'
        ]
        
        if any(pattern in from_email for pattern in skip_patterns):
            return True
        
        if 'unsubscribe' in body:
            return True
        
        if 'SPAM' in labels or 'TRASH' in labels:
            return True
        
        return False
    
    async def generate_draft(
        self, 
        email: Dict, 
        analysis: EmailAnalysis,
        user_signature: Optional[str] = None
    ) -> Optional[DraftEmail]:
        """Generate email draft based on analysis"""
        
        try:
            print(f"[Agent 9] Generating draft for: {email['subject'][:50]}")
            
            prompt = (
                f"Generate a reply to this email:\n\n"
                f"Original Email:\n"
                f"From: {email['from_name']}\n"
                f"Subject: {email['subject']}\n"
                f"Body: {email['body']}\n\n"
                f"Context:\n"
                f"- Urgency: {analysis.urgency}/5\n"
                f"- Address: {analysis.reply_context}\n"
                f"- Tone: {analysis.suggested_tone}\n\n"
                f"Generate a {analysis.suggested_tone} reply that:\n"
                f"1. Addresses key points\n"
                f"2. Uses suggested tone\n"
                f"3. Brief but complete\n"
                f"4. Appropriate closing\n"
            )
            
            from google import genai
            from google.genai import types
            from core.config import settings
            
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DraftEmail
                )
            )
            
            if response.parsed:
                draft = response.parsed
                
                if user_signature:
                    draft.body += f"\n\n{user_signature}"
                
                print(f"[Agent 9] Draft generated ({len(draft.body)} chars)")
                return draft
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Draft generation failed: {e}")
            return None
    
    async def process_yesterdays_emails(self, max_emails: int = 20) -> Dict:
        """
        Main processing function for email intelligence
        Returns summary of processing results
        """
        try:
            print("=" * 60)
            print("[Agent 9] EMAIL INTELLIGENCE STARTING")
            print("=" * 60)
            
            gmail_service = GmailService(self.user_id)
            
            # IMPORTANT: Initialize the service first
            await gmail_service.initialize()
            
            print("[Agent 9] Step 1: Fetching emails from last 48 hours")
            emails = gmail_service.get_yesterdays_emails(max_results=max_emails)
            
            if not emails:
                print("[Agent 9] No emails found")
                return {
                    "status": "success",
                    "message": "No emails to process",
                    "emails_checked": 0,
                    "drafts_created": 0
                }
            
            print(f"[Agent 9] Found {len(emails)} emails")
            
            print("[Agent 9] Step 2: Checking which need replies")
            unreplied = []
            
            for email in emails:
                already_replied = gmail_service.check_if_user_replied(email['thread_id'])
                if not already_replied:
                    unreplied.append(email)
            
            print(f"[Agent 9] {len(unreplied)} emails without replies")
            
            if not unreplied:
                return {
                    "status": "success",
                    "message": "All emails already have replies",
                    "emails_checked": len(emails),
                    "drafts_created": 0
                }
            
            print("[Agent 9] Step 3: AI analyzing emails")
            emails_needing_replies = []
            
            for email in unreplied:
                analysis = await self.analyze_email(email)
                
                if analysis and analysis.needs_reply:
                    emails_needing_replies.append({
                        "email": email,
                        "analysis": analysis
                    })
            
            print(f"[Agent 9] {len(emails_needing_replies)} emails need replies")
            
            if not emails_needing_replies:
                return {
                    "status": "success",
                    "message": "No emails require replies",
                    "emails_checked": len(emails),
                    "drafts_created": 0
                }
            
            print("[Agent 9] Step 4: Generating email drafts")
            drafts_created = []
            
            for item in emails_needing_replies:
                email = item['email']
                analysis = item['analysis']
                
                draft = await self.generate_draft(email, analysis)
                
                if draft:
                    gmail_draft_result = gmail_service.create_draft(
                        to_email=email['from_email'],
                        subject=draft.subject,
                        body=draft.body,
                        thread_id=email['thread_id']
                    )
                    
                    draft_doc = {
                        "email_id": email['id'],
                        "thread_id": email['thread_id'],
                        "from_name": email['from_name'],
                        "from_email": email['from_email'],
                        "subject": email['subject'],
                        "original_snippet": email['snippet'],
                        "ai_analysis": {
                            "needs_reply": analysis.needs_reply,
                            "urgency": analysis.urgency,
                            "reasoning": analysis.reasoning,
                            "reply_context": analysis.reply_context,
                            "suggested_tone": analysis.suggested_tone
                        },
                        "draft": {
                            "subject": draft.subject,
                            "body": draft.body,
                            "tone": draft.tone
                        },
                        "gmail_draft_id": gmail_draft_result.get('draft_id'),
                        "status": "pending",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    db = FirestoreService()
                    doc_ref = db._get_user_ref(self.user_id).collection("email_drafts").document()
                    doc_ref.set(draft_doc)
                    
                    drafts_created.append(draft_doc)
                    print(f"[Agent 9] Draft created for: {email['subject'][:50]}")
            
            print(f"[Agent 9] Saved {len(drafts_created)} drafts to Firestore and Gmail")
            
            print("=" * 60)
            print("[Agent 9] SUMMARY")
            print("=" * 60)
            print(f"Emails checked: {len(emails)}")
            print(f"Unreplied: {len(unreplied)}")
            print(f"Need replies: {len(emails_needing_replies)}")
            print(f"Drafts created: {len(drafts_created)}")
            
            if drafts_created:
                print("\n[Agent 9] Drafts created for:")
                for draft in drafts_created:
                    print(f"  - {draft['from_name']}: {draft['subject']}")
                    print(f"    Urgency: {draft['ai_analysis']['urgency']}/5")
                    print(f"    Tone: {draft['draft']['tone']}")
            
            print("=" * 60)
            
            return {
                "status": "success",
                "emails_checked": len(emails),
                "unreplied": len(unreplied),
                "needs_replies": len(emails_needing_replies),
                "drafts_created": len(drafts_created),
                "drafts": drafts_created
            }
            
        except Exception as e:
            print(f"[ERROR] Agent 9 processing failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def process(self, data: dict):
        """Event bus handler - not used for Agent 9"""
        pass