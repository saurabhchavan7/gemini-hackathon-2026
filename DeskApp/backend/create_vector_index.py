import json
import os
from google.cloud import aiplatform
from google.cloud import storage


# ===== CONFIG =====
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
REGION = os.getenv("GCP_LOCATION", "us-central1")
BUCKET_NAME = os.getenv("VERTEX_BUCKET_NAME", "")
INDEX_DISPLAY_NAME = os.getenv("VERTEX_INDEX_DISPLAY_NAME", "lifeos-items-index")
DIMENSIONS = int(os.getenv("VERTEX_EMBEDDING_DIMENSIONS", "768"))  # Gemini embeddings dimension

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is required to create a Vertex AI index.")
if not BUCKET_NAME:
    BUCKET_NAME = f"{PROJECT_ID}-lifeos-vectors"
# ==================

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)

# Create a dummy embedding (Vertex requires at least one vector)
initial_embedding = {
 "id": "init_vector",
 "embedding": [0.0] * DIMENSIONS
}

# Upload embedding to Google Cloud Storage
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)
blob = bucket.blob("embeddings/initial.json")
blob.upload_from_string(json.dumps(initial_embedding))

print(" Initial embedding uploaded to GCS")

print(f"Creating Vector Search index (this takes ~10 minutes)...")

index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
 display_name=INDEX_DISPLAY_NAME,
 contents_delta_uri=f"gs://{BUCKET_NAME}/embeddings/",
 dimensions=DIMENSIONS,
 approximate_neighbors_count=150,
 leaf_node_embedding_count=500,
 leaf_nodes_to_search_percent=7,
 distance_measure_type="DOT_PRODUCT_DISTANCE",
 index_update_method="STREAM_UPDATE",
 description="LifeOS captured items vector index"
)

print(" Vector Search index created!")
print("Index resource name:", index.resource_name)

# Save config for later steps
config = {
 "project_id": PROJECT_ID,
 "region": REGION,
 "bucket": BUCKET_NAME,
 "index_id": index.name.split("/")[-1],
 "index_resource_name": index.resource_name
}

with open("vertex_ai_config.json", "w") as f:
 json.dump(config, f, indent=2)

print(f"json")