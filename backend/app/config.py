from dotenv import load_dotenv
import os

load_dotenv()

# GitHub Environment Variables
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL")

with open(GITHUB_PRIVATE_KEY_PATH, "r") as f:
  GITHUB_PRIVATE_KEY = f.read()

# Firebase Environment Variables
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

# JWT Environment Variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")