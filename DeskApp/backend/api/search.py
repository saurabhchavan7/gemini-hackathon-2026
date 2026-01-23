from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.vector_service import vector_service
from services.gemini_service import gemini_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, List[str]]] = None
    limit: int = 10

@router.post("/api/search")
async def search_items(request: SearchRequest):
    """Natural language search using Gemini + Vector Search"""
    
    try:
        # 1. Generate embedding for query using Gemini
        query_embedding = await gemini_service.generate_embedding(request.query)
        
        # 2. Search Vector Search
        results = await vector_service.search(
            query_embedding=query_embedding,
            num_neighbors=request.limit,
            filters=request.filters
        )
        
        # 3. Fetch full item details from database
        from models.database import get_items_by_ids
        item_ids = [r["item_id"] for r in results]
        items = await get_items_by_ids(item_ids)
        
        # 4. Merge with similarity scores
        for item in items:
            score = next((r["similarity_score"] for r in results if r["item_id"] == item["id"]), 0)
            item["similarity_score"] = score
        
        # 5. Sort by similarity
        items.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "success": True,
            "query": request.query,
            "results": items,
            "count": len(items)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))