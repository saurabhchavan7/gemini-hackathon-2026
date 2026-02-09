import os
from typing import Dict, Optional, List
from services.vector_search_service import VectorSearchService
from services.firestore_service import FirestoreService
from core.config import settings


class RAGService:
    """
    RAG (Retrieval Augmented Generation) Service
    
    Combines vector search with LLM to answer questions based on user's documents
    """
    def __init__(self):
        self.vector_search = VectorSearchService()
        self.db = FirestoreService()
        print("[RAG_SERVICE] Initialized")
        
    def _rephrase_query_with_llm(self, query: str) -> str:
        """
        Use Gemini to rephrase or expand the user query for better retrieval.
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(settings.PRIMARY_MODEL)
            prompt =  f"""
                You're an AI assistant who can understand user intent. The user can ask questions
                about what they have captured in the LifeOS application, such as information related to:

                1. work_career - Jobs, meetings, code, office, career
                2. education_learning - Courses, tutorials, assignments, study
                3. money_finance - Bills, banking, payments, investments
                4. home_daily_life - Groceries, repairs, utilities, chores
                5. health_wellbeing - Doctor, medications, fitness, wellness
                6. family_relationships - Family events, kids, birthdays
                7. travel_movement - Flights, hotels, trips, visas
                8. shopping_consumption - Products, shopping, wishlists
                9. entertainment_leisure - Movies, shows, games, concerts
                10. social_community - Social media, news, forums
                11. admin_documents - IDs, passports, forms, legal
                12. ideas_thoughts - Personal notes, brainstorms, ideas
                13. Other (can be anaything else not covered above)

                Rephrase or expand the following user question to maximize the chance of retrieving
                relevant documents from a personal knowledge base. Use synonyms, related terms,
                and clarify ambiguous words.

                Do NOT answer the question — only rewrite it for retrieval.

                User question: {query}

                Rephrased query:
"""            
            response = model.generate_content(prompt)
            rephrased = response.text.strip()
            if rephrased:
                print(f"[RAG_SERVICE] Rephrased query: {rephrased}")
                return rephrased
        except Exception as e:
            print(f"[RAG_SERVICE] Query rephrasing failed: {e}")
        return query
    
    
    
    def answer_question(
        self,
        query: str,
        user_id: str,
        num_results: int = 5,
        filter_domain: Optional[str] = None,
        filter_type: Optional[str] = None
    ) -> Dict:
        """
        Answer user's question using RAG
        
        Args:
            query: User's question
            user_id: User ID for filtering
            num_results: Number of documents to retrieve
            filter_domain: Optional domain filter
            filter_type: Optional type filter (capture/document)
            
        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "confidence": str,
                "context_used": str
            }
        """
        
        print(f"[RAG_SERVICE] Question: '{query}'")

        # Step 1: Rephrase/expand query using LLM
        retrieval_query = self._rephrase_query_with_llm(query)

        # Step 2: Search vector index for relevant content
        search_results = self.vector_search.search(
            query=retrieval_query,
            user_id=user_id,
            num_results=num_results,
            filter_domain=filter_domain,
            filter_type=filter_type
        )

        print(f"[RAG_SERVICE] Used retrieval query: {retrieval_query}")
        print(f"[RAG_SERVICE] Found {len(search_results)} vector search results")
        
        if not search_results:
            return {
                "answer": "I could not find any relevant information to answer your question. Please try uploading documents or capturing screenshots first.",
                "sources": [],
                "confidence": "none",
                "context_used": ""
            }
        
        # Step 2: Fetch full data from Firestore and build context
        context_chunks = []
        sources = []
        
        for result in search_results[:3]:
            source_id = result['source_id']
            item_type = result['type']
            
            try:
                if item_type == "capture":
                    doc = self.db._get_user_ref(user_id).collection("memories").document(source_id).get()
                else:
                    doc = self.db._get_user_ref(user_id).collection("files").document(source_id).get()
                
                if doc.exists:
                    data = doc.to_dict()
                    
                    # Extract text content for context
                    if data.get('chunks'):
                        # For documents, use first 10 chunks
                        context_chunks.extend(data['chunks'][:10])
                    elif data.get('full_transcript'):
                        # For captures, use OCR text
                        context_chunks.append(data['full_transcript'])
                    elif data.get('text'):
                        # Fallback to full text (truncated)
                        context_chunks.append(data['text'][:1500])
                    
                    # Save source info for response
                    sources.append({
                        "id": source_id,
                        "title": data.get('title', 'Untitled'),
                        "type": item_type,
                        "domain": data.get('domain', 'unknown'),
                        "similarity": round(1 - result['distance'], 2)
                    })
                    
                    print(f"[RAG_SERVICE] Added source: {data.get('title', 'Untitled')[:50]}")
            except Exception as e:
                print(f"[RAG_SERVICE] Warning: Could not fetch source {source_id}: {e}")
                continue
        
        if not context_chunks:
            return {
                "answer": "I found relevant documents but could not extract the content. Please check if the documents are properly uploaded.",
                "sources": sources,
                "confidence": "low",
                "context_used": ""
            }
        
        # Step 3: Build context from chunks (limit to 5 chunks max)
        context = "\n\n---\n\n".join(context_chunks[:5])
        
        print(f"[RAG_SERVICE] Built context from {len(context_chunks[:5])} chunks")
        print(f"[RAG_SERVICE] Context length: {len(context)} characters")
        
        # Step 4: Build prompt
        prompt = f"""You are a helpful assistant answering questions based on the user's personal documents and captures.

Context from user's documents:
{context}

User's question: {query}

Instructions:
- Answer the question directly and concisely
- Use only information from the context above if relevant information is available then give descriptive answer based on user question and context
- Be specific with numbers, dates, amounts, and facts
- If the answer is not in the context, say "I don't have that information in your documents"
- Keep your answer under 10 sentences
- Do not make up information

Answer:"""
        
        # Step 5: Generate answer using Gemini with retry
        try:
            print(f"[RAG_SERVICE] Calling Gemini for answer generation...")
            
            import google.generativeai as genai
            import time

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(settings.PRIMARY_MODEL)
            
            # Retry logic for rate limits
            max_retries = 2
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    answer = response.text.strip()
                    print(f"[RAG_SERVICE] Generated answer: {answer[:100]}...")
                    confidence = "high" if len(sources) >= 2 else "medium"
                    break
                except Exception as retry_error:
                    if "429" in str(retry_error) and attempt < max_retries - 1:
                        print(f"[RAG_SERVICE] Rate limit hit, waiting {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
        except Exception as e:
            print(f"[RAG_SERVICE] LLM error: {e}")
            
            # Fallback: Extractive answer from context
            answer = self._extract_answer_from_context(query, context_chunks, sources)
            confidence = "medium"
        
        # Step 6: Return complete response
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "context_used": context[:500] + "..." if len(context) > 500 else context,
            "num_sources": len(sources)
        }
    
    def _extract_answer_from_context(self, query: str, chunks: List[str], sources: List[Dict]) -> str:
        """
        Fallback method: Extract answer from context without LLM
        Used when rate limits are hit
        """
        
        # Simple extractive approach
        query_lower = query.lower()
        
        # Look for specific keywords
        if "how much" in query_lower or "amount" in query_lower or "cost" in query_lower:
            # Extract dollar amounts
            import re
            for chunk in chunks:
                amounts = re.findall(r'\$[\d,]+\.?\d*', chunk)
                if amounts:
                    return f"I found these amounts in your documents: {', '.join(amounts[:3])}. Please check the sources below for details."
        
        if "when" in query_lower or "date" in query_lower:
            # Extract dates
            import re
            for chunk in chunks:
                dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', chunk)
                if dates:
                    return f"I found these dates: {', '.join(dates[:3])}. Please check the sources for context."
        
        # Default: Just point to sources
        titles = [s['title'] for s in sources[:3]]
        return f"I found {len(sources)} relevant documents: {', '.join(titles)}. The answer may be in these sources."


if __name__ == "__main__":
    """Test the RAG service"""
    
    print("Testing RAG Service")
    print("="*60)
    
    service = RAGService()
    
    # Test question
    result = service.answer_question(
        query="can you find out the resources related to RAG service?",
        user_id="113314724333098866443",
        num_results=5
    )
    
    # print("\nQuestion:", result['query'])
    print("\nAnswer:", result['answer'])
    print("\nSources:", len(result['sources']))
    for i, source in enumerate(result['sources'], 1):
        print(f"  {i}. {source['title']} (similarity: {source['similarity']*100:.1f}%)")
    
    print("\nConfidence:", result['confidence'])
    print("\n" + "="*60)