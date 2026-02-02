import os
from typing import List, Tuple
from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndex
from vertexai.language_models import TextEmbeddingModel

class EmbeddingService:
    def __init__(self):
        self.project_id = os.getenv("VERTEX_PROJECT_ID", "gemini-hackathon-2026-484903")
        self.region = os.getenv("VERTEX_REGION", "us-central1")
        self.index_id = os.getenv("VERTEX_INDEX_ID", "2331855255303618560")
        aiplatform.init(project=self.project_id, location=self.region)
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = self.embedding_model.get_embeddings(texts)
        return [e.values for e in response]

    def embed_and_upload(
        self,
        chunks: List[str],
        file_doc_id: str,
        parsed: dict,
        upload_result: dict,
        enhanced_meta: dict,
    ) -> Tuple[str | None, str | None]:
        embedding_error = None
        vector_error = None
        try:
            embeddings = self.get_embeddings(chunks)
            datapoints = []
            for i, embedding in enumerate(embeddings):
                datapoints.append({
                    "datapoint_id": f"{file_doc_id}_chunk_{i}",
                    "feature_vector": embedding,
                    "crowding_tag": file_doc_id
                })
            try:
                index = MatchingEngineIndex(index_name=self.index_id)
                index.upsert_datapoints(datapoints)
                print(f"[VECTOR] Uploaded {len(datapoints)} vectors to index {self.index_id}")
            except Exception as ve:
                vector_error = str(ve)
                print(f"[VECTOR] Upload error: {vector_error}")
        except Exception as ee:
            embedding_error = str(ee)
            print(f"[EMBEDDING] Error: {embedding_error}")
        return embedding_error, vector_error

if __name__ == "__main__":
    service = EmbeddingService()
    test_chunks = [
        "This is the first test chunk.",
        "Here is another chunk of text for embedding.",
        "Final chunk for demo purposes."
    ]
    file_doc_id = "testfile123"
    parsed = {"domain": "test_domain", "title": "Test Title", "summary": "Test Summary"}
    upload_result = {"public_url": "https://example.com/testfile.pdf"}
    enhanced_meta = {"uploaded_at": "2026-02-01T12:00:00Z"}

    embedding_error, vector_error = service.embed_and_upload(
        test_chunks, file_doc_id, parsed, upload_result, enhanced_meta
    )
    print("Embedding error:", embedding_error)
    print("Vector upload error:", vector_error)
