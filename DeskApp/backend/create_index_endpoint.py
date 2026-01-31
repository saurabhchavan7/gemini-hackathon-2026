from google.cloud import aiplatform
import json

# Load config created earlier
with open("vertex_ai_config.json", "r") as f:
 config = json.load(f)

PROJECT_ID = config["project_id"]
REGION = config["region"]
INDEX_ID = config["index_id"]
INDEX_RESOURCE_NAME = config["index_resource_name"]

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)

print(f"Creating Index Endpoint...")

# Create endpoint
endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
 display_name="lifeos-items-endpoint",
 public_endpoint_enabled=True, # OK for hackathon demo
 description="LifeOS Vector Search Endpoint"
)

print(" Endpoint created!")
print("Endpoint resource name:", endpoint.resource_name)

print(f"Deploying index to endpoint (takes ~5 minutes)...")

# Deploy index to endpoint
endpoint.deploy_index(
 index=aiplatform.MatchingEngineIndex(index_name=INDEX_RESOURCE_NAME),
 deployed_index_id="lifeos_deployed_index",
 display_name="LifeOS Items Index",
 min_replica_count=1,
 max_replica_count=2
)

print(" Index deployed successfully!")

# Save endpoint info back to config
config["endpoint_id"] = endpoint.name.split("/")[-1]
config["endpoint_resource_name"] = endpoint.resource_name

with open("vertex_ai_config.json", "w") as f:
 json.dump(config, f, indent=2)

print(f"json updated with endpoint info")
