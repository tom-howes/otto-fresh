import httpx
import jwt
import time
from enum import IntEnum
from app.config import (
  GITHUB_APP_ID,
  GITHUB_CLIENT_ID,
  GITHUB_CLIENT_SECRET,
  GITHUB_PRIVATE_KEY,
  GITHUB_CALLBACK_URL
)

class Status_Codes(IntEnum):
  GET_SUCCESS = 200
  POST_SUCCESS = 201

def handle_error(response, expected_status_code):
  if response.status_code != expected_status_code:
    error_data = response.json()
    raise Exception(f"GitHub API error: {error_data.get('message')}")

def generate_jwt():
  payload = {
    "iat": int(time.time()) - 60,
    "exp": int(time.time()) + 600,
    "iss": GITHUB_APP_ID
  }
  token = jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")
  return token

async def get_installation_token(installation_id):
  token = generate_jwt()
  url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
  headers = {
    "Authorization" : f"Bearer {token}",
    "Accept" : "application/vnd.github+json"
  }
  async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers)
    handle_error(response, Status_Codes.POST_SUCCESS)
    data = response.json()
    return data["token"]

def build_oauth_url(state):
  url = "https://github.com/login/oauth/authorize"
  url += f"?client_id={GITHUB_CLIENT_ID}"
  url += f"&redirect_uri={GITHUB_CALLBACK_URL}"
  url += f"&state={state}"
  return url

async def get_user_access_token(code):
  url = "https://github.com/login/oauth/access_token"
  url += f"?client_id={GITHUB_CLIENT_ID}"
  url += f"&client_secret={GITHUB_CLIENT_SECRET}"
  url += f"&code={code}"
  headers = {
    "Accept": "application/json"
  }
  async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    data = response.json()
    return {
      "access_token": data["access_token"],
      "refresh_token": data.get("refresh_token")
    }

async def get_user_profile(user_access_token):
  url = "https://api.github.com/user"
  headers = {
    "Authorization": f"Bearer {user_access_token}"
  }
  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    return response.json()
  
async def list_user_repositories(user_access_token):
  url = "https://api.github.com/user/repos"
  url += "?sort=updated"
  headers = {
    "Authorization": f"Bearer {user_access_token}"
  }
  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    return response.json()
  
async def get_repository_details(installation_token, owner, repository):
  url = f"https://api.github.com/repos/{owner}/{repository}"
  headers = {
    "Authorization": f"Bearer {installation_token}"
  }
  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    return response.json()

# File contents returned are base64 encoded
async def get_repository_contents(installation_token, owner, repository, path=""):
  url = f"https://api.github.com/repos/{owner}/{repository}/contents/{path}"
  headers = {
    "Authorization": f"Bearer {installation_token}"
  }
  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    return response.json()
  
async def get_default_branch_sha(installation_token, owner, repository, branch):
  url = f"https://api.github.com/repos/{owner}/{repository}/git/ref/heads/{branch}"
  headers = {
    "Authorization": f"Bearer {installation_token}"
  }
  async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
    handle_error(response, Status_Codes.GET_SUCCESS)
    data = response.json()
    return data["object"]["sha"]
  
async def create_branch(installation_token, owner, repository, branch_name, sha):
  url = f"https://api.github.com/repos/{owner}/{repository}/git/refs"
  headers = {
    "Authorization": f"Bearer {installation_token}"
  }
  body = {
    "ref": f"refs/heads/{branch_name}",
    "sha": sha
  }
  async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers, json=body)
    handle_error(response, Status_Codes.POST_SUCCESS)
    return response.json()
