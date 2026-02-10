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