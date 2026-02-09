#firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2 import service_account
from app.config import (
  FIREBASE_CREDENTIALS_PATH,
  FIREBASE_PROJECT_ID
)

# Initialize Firebase Admin SDK Connection
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Create Firestore client
firestore_credentials = service_account.Credentials.from_service_account_file(FIREBASE_CREDENTIALS_PATH)
db = firestore.AsyncClient(project=FIREBASE_PROJECT_ID, credentials=firestore_credentials)

