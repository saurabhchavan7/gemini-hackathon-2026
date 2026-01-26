import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os

# Path to the service account key you just downloaded
SERVICE_ACCOUNT_KEY = os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")

# Initialize Firebase with the Service Account
if not firebase_admin._apps:
    try:
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            print(f"🔑 Loading Service Account: {SERVICE_ACCOUNT_KEY}")
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
        else:
            print("⚠️ serviceAccountKey.json not found! Falling back to ADC...")
            firebase_admin.initialize_app()
            
    except Exception as e:
        print(f"❌ Firebase init error: {e}")

db = firestore.client()

class FirestoreClient:
    def __init__(self):
        self.collection = "captures"

    def save_capture(self, user_id: str, item_data: dict):
        try:
            item_id = item_data.get("item_id")
            
            # Sanitize data for Firestore
            if isinstance(item_data.get("entities"), str):
                try:
                    item_data["entities"] = json.loads(item_data["entities"])
                except:
                    item_data["entities"] = {}

            if isinstance(item_data.get("confidence"), str):
                try:
                    item_data["confidence"] = json.loads(item_data["confidence"])
                except:
                    item_data["confidence"] = {}

            # Add timestamps
            item_data["updated_at"] = datetime.now().isoformat()
            if "created_at" not in item_data:
                item_data["created_at"] = datetime.now().isoformat()
            
            # Save to: users/{user_id}/captures/{item_id}
            doc_ref = db.collection("users").document(user_id).collection(self.collection).document(item_id)
            doc_ref.set(item_data, merge=True)
            
            print(f"✅ Saved to Firestore: users/{user_id}/captures/{item_id}")
            return True
        except Exception as e:
            print(f"❌ Firestore save error: {e}")
            return False

    def get_user_captures(self, user_id: str, limit: int = 50):
        try:
            docs = (
                db.collection("users")
                .document(user_id)
                .collection(self.collection)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"❌ Firestore fetch error: {e}")
            return []

firestore_client = FirestoreClient()