import os
from typing import List, Tuple, Optional
from google.cloud import aiplatform
from google.cloud import aiplatform_v1
from vertexai.language_models import TextEmbeddingModel
from datetime import datetime
from core.config import settings


class EmbeddingService:
    
    def __init__(self):
        self.project_id = settings.PROJECT_ID
        self.region = settings.LOCATION
        self.index_name = settings.VERTEX_INDEX_NAME

        if not self.project_id:
            raise ValueError("[EMBEDDING_SERVICE] Missing GCP_PROJECT_ID; set it in the environment.")
        if not self.index_name:
            raise ValueError("[EMBEDDING_SERVICE] Missing VERTEX_INDEX_NAME; set it in the environment.")
        
        self.index_client = aiplatform_v1.IndexServiceClient(
            client_options={"api_endpoint": f"{self.region}-aiplatform.googleapis.com"}
        )
        
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        print(f"[EMBEDDING_SERVICE] Initialized - Using v1 client")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), 5):
            batch = texts[i:i + 5]
            response = self.embedding_model.get_embeddings(batch)
            embeddings.extend([e.values for e in response])
        print(f"[EMBEDDING_SERVICE] Generated {len(embeddings)} embeddings")
        return embeddings

    def embed_and_upload_document(
        self,
        chunks: List[str],
        file_doc_id: str,
        user_id: str,
        metadata: dict
    ) -> Tuple[Optional[str], Optional[str]]:
        
        try:
            print(f"[EMBEDDING_SERVICE] Processing {len(chunks)} chunks...")
            embeddings = self.get_embeddings(chunks)
            
            print(f"[EMBEDDING_SERVICE] Creating datapoints...")
            datapoints = []
            for i, embedding in enumerate(embeddings):
                datapoint = aiplatform_v1.IndexDatapoint(
                    datapoint_id=f"{file_doc_id}_chunk_{i}",
                    feature_vector=embedding,
                    restricts=[
                        aiplatform_v1.IndexDatapoint.Restriction(
                            namespace="user_id",
                            allow_list=[user_id]
                        ),
                        aiplatform_v1.IndexDatapoint.Restriction(
                            namespace="type",
                            allow_list=["document"]
                        ),
                        aiplatform_v1.IndexDatapoint.Restriction(
                            namespace="source_id",
                            allow_list=[file_doc_id]
                        ),
                        aiplatform_v1.IndexDatapoint.Restriction(
                            namespace="domain",
                            allow_list=[metadata.get("domain", "unknown")]
                        )
                    ]
                )
                datapoints.append(datapoint)
            
            print(f"[EMBEDDING_SERVICE] Uploading {len(datapoints)} datapoints...")
            
            request = aiplatform_v1.UpsertDatapointsRequest(
                index=self.index_name,
                datapoints=datapoints
            )
            
            response = self.index_client.upsert_datapoints(request=request)
            print(f"[EMBEDDING_SERVICE] SUCCESS - Uploaded {len(datapoints)} vectors")
            
            return None, None
            
        except Exception as e:
            print(f"[EMBEDDING_SERVICE] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return str(e), None

    def embed_and_upload_capture(
        self,
        capture_id: str,
        user_id: str,
        combined_text: str,
        metadata: dict
    ) -> Tuple[Optional[str], Optional[str]]:
        
        try:
            print(f"[EMBEDDING_SERVICE] Processing capture {capture_id}...")
            embeddings = self.get_embeddings([combined_text])
            
            datapoint = aiplatform_v1.IndexDatapoint(
                datapoint_id=f"capture_{capture_id}",
                feature_vector=embeddings[0],
                restricts=[
                    aiplatform_v1.IndexDatapoint.Restriction(
                        namespace="user_id",
                        allow_list=[user_id]
                    ),
                    aiplatform_v1.IndexDatapoint.Restriction(
                        namespace="type",
                        allow_list=["capture"]
                    ),
                    aiplatform_v1.IndexDatapoint.Restriction(
                        namespace="source_id",
                        allow_list=[capture_id]
                    ),
                    aiplatform_v1.IndexDatapoint.Restriction(
                        namespace="domain",
                        allow_list=[metadata.get("domain", "unknown")]
                    )
                ]
            )
            
            print(f"[EMBEDDING_SERVICE] Uploading capture datapoint...")
            
            request = aiplatform_v1.UpsertDatapointsRequest(
                index=self.index_name,
                datapoints=[datapoint]
            )
            
            response = self.index_client.upsert_datapoints(request=request)
            print(f"[EMBEDDING_SERVICE] SUCCESS - Uploaded capture")
            
            return None, None
            
        except Exception as e:
            print(f"[EMBEDDING_SERVICE] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return str(e), None