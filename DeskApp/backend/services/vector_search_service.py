import os
from typing import List, Dict, Optional
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
from vertexai.language_models import TextEmbeddingModel

class VectorSearchService:
    
    def __init__(self):
        self.project_id = "gemini-hackathon-2026-484903"
        self.region = "us-central1"
        self.index_endpoint_id = "8185021842885443584"
        self.deployed_index_id = "lifeos_deployed_index"
        
        aiplatform.init(project=self.project_id, location=self.region)
        self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=self.index_endpoint_id
        )
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        print(f"[VECTOR_SEARCH] Initialized - Endpoint: {self.index_endpoint_id}")

    def search(
        self,
        query: str,
        user_id: str,
        num_results: int = 10,
        filter_type: Optional[str] = None,
        filter_domain: Optional[str] = None
    ) -> List[Dict]:
        
        try:
            print(f"[VECTOR_SEARCH] Query: '{query}'")
            query_embedding = self.embedding_model.get_embeddings([query])[0].values
            
            restricts = [
                Namespace(name="user_id", allow_tokens=[user_id], deny_tokens=[])
            ]
            
            if filter_type:
                restricts.append(
                    Namespace(name="type", allow_tokens=[filter_type], deny_tokens=[])
                )
            
            if filter_domain:
                restricts.append(
                    Namespace(name="domain", allow_tokens=[filter_domain], deny_tokens=[])
                )
            
            print(f"[VECTOR_SEARCH] Searching with {len(restricts)} filters...")
            
            response = self.index_endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[query_embedding],
                num_neighbors=num_results,
                filter=restricts
            )
            
            results = []
            if response and len(response) > 0:
                for neighbor_list in response:
                    for neighbor in neighbor_list:
                        results.append({
                            "id": neighbor.id,
                            "distance": neighbor.distance,
                            "source_id": self._extract_source_id(neighbor.id),
                            "type": self._extract_type(neighbor.id),
                        })
            
            print(f"[VECTOR_SEARCH] Found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"[VECTOR_SEARCH] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_source_id(self, datapoint_id: str) -> str:
        if datapoint_id.startswith("capture_"):
            return datapoint_id.replace("capture_", "")
        elif "_chunk_" in datapoint_id:
            return datapoint_id.split("_chunk_")[0]
        return datapoint_id

    def _extract_type(self, datapoint_id: str) -> str:
        return "capture" if datapoint_id.startswith("capture_") else "document"