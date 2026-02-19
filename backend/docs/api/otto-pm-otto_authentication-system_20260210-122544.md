# API Documentation: Authentication System

## 1. Overview and Purpose

The Authentication System for Otto-PM, an AI-powered project management solution, provides secure user authentication and session management. It leverages GitHub's OAuth 2.0 for user registration and login, ensuring a streamlined and secure onboarding process. Once authenticated, users are issued a JSON Web Token (JWT) for session management, allowing access to protected API resources. The system is designed with security in mind, incorporating CSRF protection during the OAuth flow and handling session tokens securely via HTTP-only cookies.

This documentation details the public API endpoints, internal authentication utilities, and data models that constitute the core of the authentication system.

## 2. Functions/Classes

This section outlines the primary API endpoints, FastAPI dependencies, internal utility functions, and data models involved in the authentication process.

### 2.1 API Endpoints

#### `GET /login`

*   **Description**: Initiates the GitHub OAuth authentication flow. Generates a CSRF state token, stores it in an HTTP-only cookie, and redirects the user to GitHub's authorization page.
*   **Tags**: `Authentication`

#### `POST /logout`

*   **Description**: Logs out the current user by clearing their session cookie.
*   **Tags**: `Authentication`

#### `GET /protected` (Example of a Protected Route)

*   **Description**: An example route demonstrating how to protect an API endpoint using the `get_current_user` dependency. This route requires a valid authenticated user session.
*   **Tags**: `Authentication` (or relevant resource tag)

### 2.2 FastAPI Dependencies

#### `async def get_current_user(request: Request) -> User`

*   **Description**: Extracts and validates the current user from the session cookie. This dependency can be injected into any route that requires authentication. It validates the JWT session token and fetches the full user record from Firestore.

### 2.3 Internal Utility Functions

These functions are primarily used internally by the authentication system and are not exposed directly as API endpoints.

#### `def generate_session_token(user_id: UserId) -> JWT`

*   **Description**: Generates a JWT token for user sessions. This token is signed and contains the user ID, issue time, and expiration time.

#### `def validate_session_token(token: JWT) -> SessionPayload`

*   **Description**: Validates and decodes a JWT session token. It verifies the token's signature and expiration.

#### `def build_oauth_url(state: OAuthState) -> OAuthUrl`

*   **Description**: Builds the GitHub OAuth authorization URL. Constructs the URL to redirect users to for GitHub login, including client ID, redirect URI, and a CSRF state token.

#### `async def get_user_access_token(code: OAuthCode) -> UserTokens`

*   **Description**: Exchanges an authorization code (received from GitHub after user authorization) for user access tokens. This is a critical step in the OAuth callback process.

### 2.4 Data Models

#### `class User(UserRead)`

*   **Description**: Full user data for internal use only. Extends `UserRead` with sensitive fields that should never be exposed directly to clients. This model represents the complete user profile stored in the database.

## 3. Parameters

This section details the parameters for each function and endpoint.

### 3.1 API Endpoints

#### `GET /login`

*   **Parameters**: None
*   **Return Values**:
    *   `RedirectResponse` - A redirect response to the GitHub OAuth authorization URL. Sets an `oauth_state` cookie for CSRF protection.

#### `POST /logout`

*   **Parameters**: None
*   **Return Values**:
    *   `JSONResponse` - A JSON response confirming successful logout. Clears the `session_token` cookie.

#### `GET /protected` (Example)

*   **Parameters**:
    *   `current_user`: `User` (required) - Injected by the `Depends(get_current_user)` dependency. Represents the authenticated user's data.
*   **Return Values**:
    *   (Varies by protected route, typically returns data relevant to the resource, e.g., `User` object, `Project` list, etc.)

### 3.2 FastAPI Dependencies

#### `async def get_current_user(request: Request) -> User`

*   **Parameters**:
    *   `request`: `Request` (required) - The incoming HTTP request object, used to access cookies.
*   **Return Values**:
    *   `User` - The authenticated user's complete data from Firestore.

### 3.3 Internal Utility Functions

#### `def generate_session_token(user_id: UserId) -> JWT`

*   **Parameters**:
    *   `user_id`: `UserId` (required) - The unique identifier for the user to encode in the token.
*   **Return Values**:
    *   `JWT` - A signed JWT token string valid for 7 days.

#### `def validate_session_token(token: JWT) -> SessionPayload`

*   **Parameters**:
    *   `token`: `JWT` (required) - The JWT token string to validate.
*   **Return Values**:
    *   `SessionPayload` - The decoded payload containing `iat` (issued at), `exp` (expiration), and `sub` (subject, which is the user ID).

#### `def build_oauth_url(state: OAuthState) -> OAuthUrl`

*   **Parameters**:
    *   `state`: `OAuthState` (required) - CSRF protection token to verify on callback.
*   **Return Values**:
    *   `OAuthUrl` - The full GitHub OAuth authorization URL.

#### `async def get_user_access_token(code: OAuthCode) -> UserTokens`

*   **Parameters**:
    *   `code`: `OAuthCode` (required) - The authorization code from the OAuth callback.
*   **Return Values**:
    *   `UserTokens` - A dictionary (or similar structure) containing `access_token` and `refresh_token` from GitHub.

### 3.4 Data Models

#### `class User(UserRead)`

*   **Attributes**:
    *   `github_access_token`: `UserAccessToken` (required) - OAuth token for GitHub API access.
    *   `github_refresh_token`: `UserAccessToken | None` (optional) - Token for refreshing the access token.
    *   `installation_id`: `InstallationId | None` (optional) - The GitHub App installation ID, if the app is installed on user's repositories.

## 4. Return Values

(This section is largely covered in the "Parameters" section above, but here's a summary of the main return types.)

*   **`RedirectResponse`**: Used for initiating GitHub OAuth and redirecting the user.
*   **`JSONResponse`**: Used for standard API responses, such as logout confirmation.
*   **`User`**: The Pydantic model representing a fully authenticated user's data, typically returned by `get_current_user` or other user-related endpoints.
*   **`JWT`**: A string representing a JSON Web Token.
*   **`SessionPayload`**: A dictionary-like object containing the decoded contents of a JWT.
*   **`OAuthUrl`**: A string representing a URL for GitHub OAuth.
*   **`UserTokens`**: A dictionary-like object containing GitHub OAuth access and refresh tokens.

## 5. Usage Examples

### 5.1 Initiating GitHub Login

A user's browser would navigate to the `/login` endpoint.

```python
# Example: Client-side (e.g., browser redirect)
# User clicks a "Login with GitHub" button, which triggers a redirect
# to the backend's /login endpoint.
# The backend then redirects to GitHub.

# Python client example (for testing/programmatic access, though typically browser-driven)
import httpx

async def initiate_github_login():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/login", follow_redirects=False)
        print(f"Status Code: {response.status_code}")
        print(f"Redirect URL (to GitHub): {response.headers.get('location')}")
        print(f"Set-Cookie header: {response.headers.get('set-cookie')}")
        # Expected: 307 Temporary Redirect to GitHub, with 'oauth_state' cookie set.

# Example of the FastAPI endpoint:
from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from app.utils.auth import build_oauth_url
from app.types import OAuthState
import secrets

router = APIRouter()

@router.get("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
async def login() -> RedirectResponse:
  """Initiate GitHub OAuth authentication flow.
  
  Generates a CSRF state token, stores it in a cookie, and redirects
  the user to GitHub's authorization page.
  
  Returns:
      Redirect response to GitHub OAuth authorization URL.
  """
  state: OAuthState = secrets.token_urlsafe(16)
  url = build_oauth_url(state)
  response = RedirectResponse(url)
  response.set_cookie(
    key="oauth_state",
    value=state,
    max_age=300, # 5 mins
    httponly=True,
    secure=False, # Set to true in prod
    samesite="lax"
  )
  return response
```

### 5.2 Logging Out

A client sends a POST request to the `/logout` endpoint.

```python
# Example: Client-side (e.g., JavaScript fetch or Python httpx)
import httpx

async def logout_user():
    async with httpx.AsyncClient() as client:
        # Assuming session_token cookie is present from previous login
        response = await client.post("http://localhost:8000/logout")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print(f"Set-Cookie header (to clear session_token): {response.headers.get('set-cookie')}")
        # Expected: 200 OK, {"message": "Logged out successfully"}, with 'session_token' cookie cleared.

# Example of the FastAPI endpoint:
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout() -> JSONResponse:
  """Log out the current user by clearing their session cookie.
  
  Returns:
      JSON response confirming successful logout.
  """
  response = JSONResponse(content={"message": "Logged out successfully"})
  response.delete_cookie("session_token")
  return response
```

### 5.3 Accessing a Protected Route

A client makes a request to an endpoint that uses the `get_current_user` dependency. The `session_token` cookie must be present and valid.

```python
# Example: Client-side (e.g., JavaScript fetch or Python httpx)
import httpx

async def access_protected_route(session_token: str):
    async with httpx.AsyncClient() as client:
        # Client must send the session_token cookie
        cookies = {"session_token": session_token}
        response = await client.get("http://localhost:8000/protected", cookies=cookies)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        # Expected: 200 OK with user data, or 401 Unauthorized if token is invalid/missing.

# Example of a FastAPI protected route:
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.user import User # Assuming User model is defined

router = APIRouter()

@router.get("/protected", tags=["Example"])
async def protected_route(current_user: User = Depends(get_current_user)):
    """An example protected route that returns the authenticated user's ID."""
    return {"message": f"Welcome, authenticated user!", "user_id": current_user.id}

# Example of the get_current_user dependency:
from fastapi import Request, HTTPException, status, Depends
from app.utils.auth import validate_session_token
from app.services.user import get_user_by_id # Assumed service
from app.models.user import User # Assumed model
import jwt # For error types

async def get_current_user(request: Request) -> User:
  """Extract and validate the current user from the session cookie.
  
  This dependency can be injected into any route that requires
  authentication. It validates the JWT session token and fetches
  the full user record from Firestore.
  
  Args:
      request: The incoming HTTP request containing cookies.
      
  Returns:
      The authenticated user's complete data from Firestore.
      
  Raises:
      HTTPException: 401 Unauthorized if:
          - Session token cookie is missing
          - Session token is invalid or expired
          - User ID from token doesn't exist in database
  """
  session_token = request.cookies.get("session_token")
  if not session_token:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not authenticated: Session token missing",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  try:
    payload = validate_session_token(session_token)
    user_id = payload["sub"]
    user = await get_user_by_id(user_id) # Fetch user from DB
    if not user:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated: User not found",
        headers={"WWW-Authenticate": "Bearer"},
      )
    return user
  except jwt.ExpiredSignatureError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not authenticated: Session token expired",
      headers={"WWW-Authenticate": "Bearer"},
    )
  except jwt.InvalidTokenError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not authenticated: Invalid session token",
      headers={"WWW-Authenticate": "Bearer"},
    )
  except Exception as e:
    # Catch any other unexpected errors during token validation or user fetching
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=f"Authentication failed: {e}",
      headers={"WWW-Authenticate": "Bearer"},
    )
```

### 5.4 Generating and Validating Session Tokens (Internal)

```python
# Example: Internal usage within the backend
from app.utils.auth import generate_session_token, validate_session_token
from app.types import UserId, JWT, SessionPayload # Assumed types

# Generate a token for a new user
user_id: UserId = "user-123"
token: JWT = generate_session_token(user_id)
print(f"Generated Token: {token}")

# Later, validate the token
try:
    payload: SessionPayload = validate_session_token(token)
    print(f"Decoded Payload: {payload}")
    assert payload["sub"] == user_id
except Exception as e:
    print(f"Token validation failed: {e}")

# Example of the utility functions:
import jwt
import time
from app.types import SessionPayload, JWT, UserId # Assumed types
from app.config import JWT_SECRET_KEY # Assumed config

def generate_session_token(user_id: UserId) -> JWT:
  """Generate a JWT token for user sessions.
    
    Args:
        user_id: The unique identifier for the user to encode in the token.
        
    Returns:
        A signed JWT token string valid for 7 days.
    """
  payload: SessionPayload = {
    "iat": int(time.time()),
    "exp": int(time.time() + 60 * 60 * 24 * 7),  # 7 days from current time
    "sub": user_id
  }
  token: JWT = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
  return token

def validate_session_token(token: JWT) -> SessionPayload:
  """Validate and decode a JWT session token.
    
    Args:
        token: The JWT token string to validate.
        
    Returns:
        The decoded payload containing iat, exp, and sub (user ID).
        
    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is malformed or signature is invalid.
    """
  decoded_payload: SessionPayload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=["HS256"])
  return decoded_payload
```

### 5.5 Exchanging GitHub OAuth Code for Tokens (Internal)

This function is typically called by the `/github_callback` endpoint (not fully provided) after GitHub redirects the user back to the application.

```python
# Example: Internal usage within the backend (e.g., in /github_callback)
import httpx
from app.types import OAuthCode, UserTokens # Assumed types
from app.clients.github import get_user_access_token # Assumed client

async def handle_github_callback(oauth_code: OAuthCode):
    try:
        user_tokens: UserTokens = await get_user_access_token(oauth_code)
        print(f"GitHub Access Token: {user_tokens['access_token']}")
        print(f"GitHub Refresh Token: {user_tokens.get('refresh_token')}")
        # Further logic: fetch user profile, create/update user in DB, generate session token
    except Exception as e:
        print(f"Failed to get GitHub access token: {e}")

# Example of the client function:
import httpx
from fastapi import HTTPException, status
from app.types import OAuthCode, UserTokens # Assumed types
from app.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET # Assumed config

class GitHubAPIError(HTTPException):
    """Custom exception for GitHub API errors."""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)

async def get_user_access_token(code: OAuthCode) -> UserTokens:
  """Exchange an authorization code for user access tokens.
  
  Called after the user authorizes the app on GitHub's OAuth page.
  
  Args:
      code: The authorization code from the OAuth callback.
      
  Returns:
      Dictionary containing access_token and refresh_token.
      
  Raises:
      GitHubAPIError: If the token exchange fails.
  """
  url = "https://github.com/login/oauth/access_token"
  url += f"?client_id={GITHUB_CLIENT_ID}"
  url += f"&client_secret={GITHUB_CLIENT_SECRET}" # Assuming this is added in the actual code
  url += f"&code={code}"
  url += "&accept=json" # Request JSON response

  async with httpx.AsyncClient() as client:
    response = await client.post(url, headers={"Accept": "application/json"})
    if response.status_code != 200:
      raise GitHubAPIError(f"Failed to exchange code for token: {response.text}", status_code=response.status_code)
    
    data = response.json()
    if "error" in data:
      raise GitHubAPIError(f"GitHub token error: {data.get('error_description', data['error'])}")
    
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token")
    }
```

## 6. Error Handling

The authentication system is designed to provide clear error messages and appropriate HTTP status codes for various authentication failures.

*   **`HTTPException` (FastAPI)**:
    *   **`status.HTTP_401_UNAUTHORIZED`**:
        *   **`get_current_user`**: Raised if the `session_token` cookie is missing, the token is expired, the token is invalid/malformed, or the user ID extracted from the token does not correspond to an existing user in the database.
        *   **`get_user_access_token` (via `GitHubAPIError`)**: Raised if the exchange of the GitHub OAuth authorization code for access tokens fails (e.g., invalid code, GitHub API error).
    *   **`status.HTTP_307_TEMPORARY_REDIRECT`**: (Not an error, but a standard response for `/login` endpoint to initiate OAuth flow).
*   **`jwt.ExpiredSignatureError`**:
    *   **`validate_session_token`**: Raised if the provided JWT session token has passed its expiration time (`exp` claim).
*   **`jwt.InvalidTokenError`**:
    *   **`validate_session_token`**: Raised if the provided JWT session token is malformed, has an invalid signature, or other structural issues.
*   **`GitHubAPIError` (Custom Exception)**:
    *   **`get_user_access_token`**: A custom exception wrapping `HTTPException` specifically for errors encountered during interactions with the GitHub API, such as failing to retrieve user access tokens.

## 7. Common Use Cases

### 7.1 User Registration and First-Time Login via GitHub

1.  **User Action**: Clicks "Login with GitHub" on the frontend.
2.  **Frontend**: Redirects the user's browser to `GET /login`.
3.  **Backend (`GET /login`)**:
    *   Generates a unique CSRF `oauth_state` token.
    *   Sets the `oauth_state` as an HTTP-only cookie in the user's browser.
    *   Constructs the GitHub OAuth authorization URL using `build_oauth_url`.
    *   Redirects the user's browser to the GitHub authorization URL.
4.  **GitHub**: User grants permission to the application.
5.  **GitHub**: Redirects the user's browser back to the application's configured callback URL (e.g., `/github_callback`) with an `authorization_code` and the `state` parameter.
6.  **Backend (`/github_callback` - implied)**:
    *   Validates the `state` parameter from the URL against the `oauth_state` cookie to prevent CSRF attacks.
    *   Calls `get_user_access_token` with the `authorization_code` to exchange it for GitHub `access_token` and `refresh_token`.
    *   Fetches the user's GitHub profile using the `access_token`.
    *   Checks if the user already exists in the database.
        *   If new: Creates a new `User` record, storing GitHub tokens and profile information.
        *   If existing: Updates the `User` record with new GitHub tokens if necessary.
    *   Calls `generate_session_token` with the user's `id` to create a JWT session token.
    *   Sets the `session_token` as an HTTP-only cookie in the user's browser.
    *   Redirects the user to the application's dashboard or a success page.

### 7.2 Subsequent User Login (Session Token Re-use)

1.  **User Action**: Navigates to a protected part of the application.
2.  **Frontend**: Makes an API request to a protected endpoint (e.g., `GET /projects`).
3.  **Browser**: Automatically includes the `session_token` cookie with the request.
4.  **Backend (`GET /projects` with `get_current_user` dependency)**:
    *   The `get_current_user` dependency is invoked.
    *   It retrieves the `session_token` from the request cookies.
    *   It calls `validate_session_token` to verify the token's authenticity and expiration.
    *   It extracts the `user_id` from the token payload.
    *   It fetches the full `User` object from the database using the `user_id`.
    *   If all checks pass, the `User` object is injected into the route handler.
    *   **Route Handler**: Processes the request using the authenticated `current_user` data.
5.  **Backend**: Returns the requested data to the frontend.

### 7.3 Accessing Protected Resources

Any API endpoint that requires an authenticated user will inject the `get_current_user` dependency. If the user's session token is valid, the route handler will receive the `User` object and can proceed with business logic. If the token is invalid or missing, `get_current_user` will raise an `HTTPException(401)`, preventing unauthorized access.

### 7.4 User Logout

1.  **User Action**: Clicks "Logout" on the frontend.
2.  **Frontend**: Sends a `POST` request to `POST /logout`.
3.  **Backend (`POST /logout`)**:
    *   Creates a `JSONResponse` indicating successful logout.
    *   Deletes the `session_token` cookie from the user's browser by setting its expiration to a past date.
4.  **Backend**: Returns the `JSONResponse` to the frontend.
5.  **Frontend**: Redirects the user to the login page or home page.