from google.cloud import aiplatform
from typing import List, Dict, Any
import json

class VectorSearchService:
 def __init__(self):
 # Load config
 with open("vertex_ai_config.json", "r") as f:
 config = json.load(f)
 
 self.project_id = config["project_id"]
 self.region = config["region"]
 self.endpoint_id = config["endpoint_id"]
 self.deployed_index_id = "lifeos_deployed_index"
 
 aiplatform.init(project=self.project_id, location=self.region)
 
 # Get endpoint
 self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
 index_endpoint_name=config["endpoint_resource_name"]
 )
 
 async def add_item(self, item_id: str, embedding: List[float], metadata: Dict[str, Any]):
 """
 Add an item to the vector database.
 
 Args:
 item_id: Unique identifier for the item
 embedding: 768-dimensional vector from Gemini
 metadata: Item metadata (title, tags, etc.)
 """
 # Format for Vector Search
 embedding_data = {
 "id": item_id,
 "embedding": embedding,
 "restricts": [
 {"namespace": "type", "allow": [metadata.get("type", "unknown")]},
 {"namespace": "urgency", "allow": [metadata.get("urgency", "low")]},
 {"namespace": "platform", "allow": [metadata.get("platform", "unknown")]}
 ]
 }
 
 # Upload to GCS
 from google.cloud import storage
 client = storage.Client()
 bucket = client.bucket(f"{self.project_id}-lifeos-vectors")
 blob = bucket.blob(f"embeddings/items/{item_id}.json")
 blob.upload_from_string(json.dumps(embedding_data))
 
 # Index will auto-update due to STREAM_UPDATE mode
 print(f"item_id} to vector database")
 
 async def search(
 self, 
 query_embedding: List[float], 
 num_neighbors: int = 10,
 filters: Dict[str, List[str]] = None
 ) -> List[Dict[str, Any]]:
 """
 Search for similar items.
 
 Args:
 query_embedding: Query vector (768-dim)
 num_neighbors: How many results to return
 filters: Optional filters (type, urgency, platform)
 
 Returns:
 List of matching items with scores
 """
 # Build restrictions for filtering
 restricts = []
 if filters:
 for namespace, allow_list in filters.items():
 restricts.append({
 "namespace": namespace,
 "allow": allow_list
 })
 
 # Query Vector Search
 response = self.endpoint.find_neighbors(
 deployed_index_id=self.deployed_index_id,
 queries=[query_embedding],
 num_neighbors=num_neighbors,
 filter=restricts if restricts else None
 )
 
 # Format results
 results = []
 for neighbor in response[0]:
 results.append({
 "item_id": neighbor.id,
 "distance": neighbor.distance,
 "similarity_score": 1 - neighbor.distance # Convert distance to similarity
 })
 
 return results

# Singleton instance
vector_service = VectorSearchService()