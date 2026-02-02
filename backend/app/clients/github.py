import httpx
import jwt
import time
from app.config import (
  GITHUB_APP_ID,
  GITHUB_CLIENT_ID,
  GITHUB_CLIENT_SECRET,
  GITHUB_PRIVATE_KEY,
  GITHUB_CALLBACK_URL
)

def generate_jwt():
  payload = {
    "iat": int(time.time()) - 60,
    "exp": int(time.time()) + 600,
    "iss": GITHUB_APP_ID
  }
  jwt = jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")
  return jwt

async def get_installation_token(installation_id):
  jwt = generate_jwt()
  url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
  headers = {
    "Authorization" : f"Bearer {jwt}",
    "Accept" : "application/vnd.github+json"
  }
  async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers)
    data = response.json()
    token = data["token"]
    return token 

def build_oauth_url(state):
  url = "https://github.com/login/oauth/authorize"
  url += f"?client_id={GITHUB_CLIENT_ID}"
  url += f"&redirect_uri={GITHUB_CALLBACK_URL}"
  url += f"&state={state}"
  return url

