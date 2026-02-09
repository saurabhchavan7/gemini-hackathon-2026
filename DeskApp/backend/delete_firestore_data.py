# delete_firestore_data.py
from google.cloud import firestore

def delete_all_user_data(user_id: str):
    """Delete ALL data for a specific user"""
    
    # Use your project ID
    db = firestore.Client(project="gemini-hackathon-2026-484903")
    
    # List of all collections to delete
    collections = [
        "comprehensive_captures",
        "research_results",
        "task_resources", 
        "google_tasks",
        "google_calendar_events",
        "shopping_lists",
        "notes",
        "financial_items",
        "health_items",
        "travel_items",
        "media_items",
        "family_items",
        "document_items",
        "learning_items",
        "email_drafts"
    ]
    
    user_ref = db.collection("users").document(user_id)
    
    for collection_name in collections:
        print(f"🗑️  Deleting {collection_name}...")
        
        # Get all documents in collection
        docs = user_ref.collection(collection_name).stream()
        
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        print(f"   ✅ Deleted {count} documents from {collection_name}")
    
    print("🎉 All data deleted!")

if __name__ == "__main__":
    USER_ID = "104141873915987258012"
    
    confirm = input(f"⚠️  DELETE ALL DATA for user {USER_ID}? (yes/no): ")
    
    if confirm.lower() == "yes":
        delete_all_user_data(USER_ID)
    else:
        print("❌ Cancelled")