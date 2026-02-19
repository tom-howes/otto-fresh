# backend/app/clients/firebase.py
"""
Firebase client with better error handling
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2 import service_account
from app.config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID
import os

db = None

print(f"🔥 Initializing Firebase...")
print(f"   Credentials: {FIREBASE_CREDENTIALS_PATH}")
print(f"   Project ID: {FIREBASE_PROJECT_ID}")

try:
    if not FIREBASE_CREDENTIALS_PATH or not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        raise Exception(f"Firebase credentials not found at: {FIREBASE_CREDENTIALS_PATH}")
    
    # Initialize Firebase Admin
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    print("✓ Firebase Admin initialized")
    
    # Create Firestore client (async)
    firestore_credentials = service_account.Credentials.from_service_account_file(
        FIREBASE_CREDENTIALS_PATH
    )
    
    db = firestore.AsyncClient(
        project=FIREBASE_PROJECT_ID, 
        credentials=firestore_credentials
    )
    print("✓ Firestore AsyncClient created")
    
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    db = None
    raise

print("✅ Firebase ready\n")


# Helper function for cleanup
async def cleanup_expired_documents(collection_name: str, expiry_field: str = 'expires_at'):
    """
    Clean up expired documents from a collection.
    
    Args:
        collection_name: Firestore collection name
        expiry_field: Field name containing expiry timestamp
    """
    from datetime import datetime
    
    try:
        docs = db.collection(collection_name).stream()
        deleted = 0
        
        async for doc in docs:
            data = doc.to_dict()
            if expiry_field in data:
                expires_at = datetime.fromisoformat(data[expiry_field])
                if datetime.now() > expires_at:
                    await db.collection(collection_name).document(doc.id).delete()
                    deleted += 1
        
        if deleted > 0:
            print(f"🧹 Cleaned up {deleted} expired documents from {collection_name}")
        
        return deleted
    except Exception as e:
        print(f"⚠️  Cleanup failed for {collection_name}: {e}")
        return 0