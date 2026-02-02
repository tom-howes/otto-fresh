import firebase_admin
from firebase_admin import credentials, firestore
from app.config import (
  FIREBASE_CREDENTIALS_PATH,
  FIREBASE_PROJECT_ID
)

cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

db = firestore.AsyncClient(project=FIREBASE_PROJECT_ID)

