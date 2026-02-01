"""
LifeOS Intent Agent - Phase 2B
Infers WHY the user saved this content.
"""

import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ALLOWED_INTENTS = ["apply", "learn", "buy", "track", "reference", "unknown"]
ALLOWED_URGENCY = ["high", "medium", "low"]


def _clean_json(text: str) -> str:
    """Remove markdown fences if present."""
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```json"):
        t = t[7:]
    if t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def infer_intent(
    *,
    content_type: str,
    title: str,
    extracted_text: str,
    deadline: str | None,
    app_name: str = "",
    window_title: str = ""
) -> dict:
    """
    Returns:
    {
      "intent": "apply|learn|buy|track|reference|unknown",
      "urgency": "high|medium|low",
      "tags": [string]
    }
    """

    prompt = f"""
You are the Intent Agent for LifeOS.

Infer WHY the user saved this content.

Choose exactly ONE intent from:
apply | learn | buy | track | reference | unknown

Rules:
- Be conservative.
- If unsure, return "unknown".
- Do not invent intent names.

Return JSON ONLY in this exact format:
{{
  "intent": "apply|learn|buy|track|reference|unknown",
  "urgency": "high|medium|low",
  "tags": ["max 5 short tags"]
}}

Context:
- app_name: {app_name}
- window_title: {window_title}
- content_type: {content_type}
- title: {title}
- deadline: {deadline}

Extracted text (truncated):
\"\"\"{(extracted_text or "")[:3500]}\"\"\"
""".strip()

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[prompt]
        )

        raw = response.text
        cleaned = _clean_json(raw)
        data = json.loads(cleaned)

        intent = data.get("intent", "unknown")
        urgency = data.get("urgency", "low")
        tags = data.get("tags", [])

        if intent not in ALLOWED_INTENTS:
            intent = "unknown"
        if urgency not in ALLOWED_URGENCY:
            urgency = "low"
        if not isinstance(tags, list):
            tags = []

        tags = [str(t).strip() for t in tags if str(t).strip()][:5]

        return {
            "intent": intent,
            "urgency": urgency,
            "tags": tags
        }

    except Exception as e:
        # Never break capture flow
        return {
            "intent": "unknown",
            "urgency": "low",
            "tags": [],
            "error": str(e)
        }
