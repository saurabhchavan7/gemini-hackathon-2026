# backend/migrate_embeddings.py
# Run this ONCE to add embeddings to existing memories

from google.cloud import firestore
from services.embedding_service import EmbeddingService
from core.config import settings

def migrate_embeddings():
    """Add embeddings to existing memory documents"""
    
    print("[MIGRATION] Starting embedding migration...")
    
    db = firestore.Client(project=settings.PROJECT_ID)
    embedding_service = EmbeddingService()
    
    user_id = "104141873915987258012"  # Your user ID
    
    # Get all memories without embeddings
    memories_ref = db.collection('users').document(user_id).collection('memories')
    memories = memories_ref.stream()
    
    updated_count = 0
    skipped_count = 0
    
    for doc in memories:
        memory_data = doc.to_dict()
        memory_id = doc.id
        
        # Skip if already has embedding
        if 'embedding' in memory_data:
            print(f"[MIGRATION] Skipping {memory_id} - already has embedding")
            skipped_count += 1
            continue
        
        try:
            print(f"[MIGRATION] Processing {memory_id}...")
            
            # Build text for embedding (same format as capture)
            combined_text = f"""
            Title: {memory_data.get('title', '')}
            Domain: {memory_data.get('domain', '')}
            Content: {memory_data.get('full_transcript', '')}
            Context: {memory_data.get('task_context', '')}
            Tags: {', '.join(memory_data.get('tags', []))}
            """
            
            # Generate embedding
            embedding_vector = embedding_service.get_embeddings([combined_text])[0]
            
            # Update document
            memories_ref.document(memory_id).update({
                'embedding': embedding_vector
            })
            
            print(f"[MIGRATION] ✅ Added embedding to {memory_id}")
            updated_count += 1
            
        except Exception as e:
            print(f"[MIGRATION] ❌ Failed for {memory_id}: {e}")
    
    print(f"\n[MIGRATION] Complete!")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")

if __name__ == "__main__":
    migrate_embeddings()
