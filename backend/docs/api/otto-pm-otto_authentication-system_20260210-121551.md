This document provides comprehensive API documentation for the Authentication System of the Otto Project Management solution. It details the various components involved in user authentication, session management, and integration with GitHub OAuth.

---

# Authentication System API Documentation

## 1. Overview and Purpose

The Otto Project Management solution's Authentication System provides secure user authentication primarily through GitHub OAuth. It manages the entire authentication lifecycle, from initiating the OAuth flow and exchanging authorization codes for user tokens to establishing and validating user sessions using JSON Web Tokens (JWTs). This system also includes mechanisms for user logout and a dependency injection for retrieving the current authenticated user in protected API routes.

The core functionalities include:
*   **GitHub OAuth Integration**: Facilitates user login via GitHub, obtaining necessary access tokens for interacting with GitHub's API on behalf of the user.
*   **Session Management**: Generates and validates secure JWTs for maintaining user sessions, storing them as HTTP-only cookies.
*   **User Data Handling**: Stores and retrieves comprehensive user profiles, including sensitive GitHub access tokens, for internal application use.
*   **Authentication Dependency**: Provides a FastAPI dependency to easily secure API endpoints by extracting and validating the current user from the session.

## 2. Functions/Classes

This section details the core functions and classes that comprise the authentication system.

### 2.1. GitHub OAuth Flow Functions

These functions are responsible for initiating and completing the GitHub OAuth process.

#### `build_oauth_url`

Builds the GitHub OAuth authorization URL to which users are redirected to initiate the login process.

*   **Signature**:
    ```python
    def build_oauth_url(state: OAuthState) -> OAuthUrl
    ```
*   **Description**:
    Constructs the full URL for GitHub's OAuth authorization endpoint. This URL includes the client ID, a predefined redirect URI, and a CSRF protection state token. The user's browser will be redirected to this URL to grant permissions to the Otto application.

#### `login` (API Endpoint)

Initiates the GitHub OAuth authentication flow by redirecting the user to GitHub.

*   **Signature**:
    ```python
    @router.get("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
    async def login() -> RedirectResponse
    ```
*   **Description**:
    This API endpoint serves as the entry point for GitHub OAuth login. When accessed, it generates a cryptographically secure CSRF state token, stores it in an HTTP-only cookie (`oauth_state`), and then redirects the user's browser to the GitHub OAuth authorization URL constructed by `build_oauth_url`.

#### `get_user_access_token`

Exchanges a GitHub authorization code for user access tokens.

*   **Signature**:
    ```python
    async def get_user_access_token(code: OAuthCode) -> UserTokens
    ```
*   **Description**:
    This asynchronous function is called after a user successfully authorizes the Otto application on GitHub. It takes the authorization `code` provided by GitHub's callback and sends a POST request to GitHub's token exchange endpoint. Upon success, it retrieves the user's `access_token` and `refresh_token`.

### 2.2. Session Management Functions

These functions handle the creation, validation, and invalidation of user session tokens.

#### `generate_session_token`

Generates a JWT token for user sessions.

*   **Signature**:
    ```python
    def generate_session_token(user_id: UserId) -> JWT
    ```
*   **Description**:
    Creates a signed JSON Web Token (JWT) that represents an authenticated user session. The token includes the user's ID (`sub`), issuance time (`iat`), and expiration time (`exp`). The token is signed using a secret key and is valid for 7 days.

#### `validate_session_token`

Validates and decodes a JWT session token.

*   **Signature**:
    ```python
    def validate_session_token(token: JWT) -> SessionPayload
    ```
*   **Description**:
    Decodes and verifies the signature and expiration of a given JWT session token. If the token is valid, it returns the decoded payload containing the user ID and token metadata. This function is crucial for ensuring the integrity and validity of active user sessions.

#### `logout` (API Endpoint)

Logs out the current user by clearing their session cookie.

*   **Signature**:
    ```python
    @router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
    async def logout() -> JSONResponse
    ```
*   **Description**:
    This API endpoint handles user logout. It creates a `JSONResponse` indicating successful logout and instructs the client's browser to delete the `session_token` cookie, effectively ending the user's session.

### 2.3. Authentication Dependency

This dependency is used to secure FastAPI routes, ensuring only authenticated users can access them.

#### `get_current_user`

Extracts and validates the current user from the session cookie.

*   **Signature**:
    ```python
    async def get_current_user(request: Request) -> User
    ```
*   **Description**:
    This asynchronous dependency function is designed to be injected into FastAPI routes that require authentication. It performs the following steps:
    1.  Retrieves the `session_token` from the incoming HTTP request's cookies.
    2.  Validates the session token using `validate_session_token`.
    3.  Extracts the user ID from the decoded token payload.
    4.  Fetches the complete `User` record from the database (Firestore, as per context) using the user ID.
    5.  Returns the `User` object if all steps are successful, making it available to the route handler.

### 2.4. User Data Model

This class defines the structure for internal user data, including sensitive information.

#### `User` (Pydantic Model)

Full user data for internal use, extending `UserRead` with sensitive fields.

*   **Signature**:
    ```python
    class User(UserRead):
        github_access_token: UserAccessToken
        github_refresh_token: UserAccessToken | None
        installation_id: InstallationId | None
    ```
*   **Description**:
    This Pydantic model represents the complete user profile stored internally within the application. It extends a base `UserRead` model (not provided in chunks but implied) with sensitive information crucial for backend operations, such as GitHub OAuth access and refresh tokens, and the GitHub App installation ID. These fields are typically not exposed directly to client applications.

## 3. Parameters

This section provides a detailed description of parameters for each function.

### `build_oauth_url`

*   `state`
    *   **Type**: `OAuthState` (string)
    *   **Description**: A cryptographically secure random string used for CSRF protection. This token is generated by the server, stored in a cookie, and later verified upon GitHub's callback to ensure the request originated from the legitimate client.
    *   **Required**: Yes

### `login` (API Endpoint)

*   No explicit parameters in the function signature.
*   **Implicit Parameters**:
    *   `request`: The incoming `Request` object from FastAPI, used to set cookies.

### `get_user_access_token`

*   `code`
    *   **Type**: `OAuthCode` (string)
    *   **Description**: The authorization code received from GitHub after the user successfully grants permissions to the application. This code is short-lived and used to exchange for access tokens.
    *   **Required**: Yes

### `generate_session_token`

*   `user_id`
    *   **Type**: `UserId` (string or integer, representing a unique user identifier)
    *   **Description**: The unique identifier for the user for whom the session token is being generated. This ID will be encoded as the `sub` (subject) claim in the JWT payload.
    *   **Required**: Yes

### `validate_session_token`

*   `token`
    *   **Type**: `JWT` (string)
    *   **Description**: The JWT string to be validated and decoded. This is typically extracted from a session cookie.
    *   **Required**: Yes

### `logout` (API Endpoint)

*   No explicit parameters in the function signature.
*   **Implicit Parameters**:
    *   `response`: The `JSONResponse` object from FastAPI, used to delete cookies.

### `get_current_user`

*   `request`
    *   **Type**: `Request` (from `fastapi`)
    *   **Description**: The incoming HTTP request object, which contains the `session_token` in its cookies.
    *   **Required**: Yes

### `User` (Pydantic Model Attributes)

*   `github_access_token`
    *   **Type**: `UserAccessToken` (string)
    *   **Description**: The OAuth access token obtained from GitHub, used to make authenticated API requests to GitHub on behalf of the user.
    *   **Required**: Yes
*   `github_refresh_token`
    *   **Type**: `UserAccessToken` (string)
    *   **Description**: The OAuth refresh token obtained from GitHub, used to acquire new access tokens when the current one expires, without requiring the user to re-authenticate.
    *   **Required**: No (Optional, `None` if not provided by GitHub or not supported)
*   `installation_id`
    *   **Type**: `InstallationId` (integer or string)
    *   **Description**: The ID of the GitHub App installation, if the user has installed the app on any repositories. This is crucial for interacting with repositories via the GitHub App's permissions.
    *   **Required**: No (Optional, `None` if no installation exists or is not relevant)

## 4. Return Values

This section details the return values for each function and class.

### `build_oauth_url`

*   **Type**: `OAuthUrl` (string)
*   **Description**: The complete, encoded URL string for GitHub's OAuth authorization endpoint.

### `login` (API Endpoint)

*   **Type**: `RedirectResponse` (from `fastapi.responses`)
*   **Description**: An HTTP 307 Temporary Redirect response that points the user's browser to the GitHub OAuth authorization URL. This response also sets the `oauth_state` cookie.

### `get_user_access_token`

*   **Type**: `UserTokens` (dictionary)
*   **Description**: A dictionary containing the GitHub user's access tokens.
    *   `access_token` (string): The primary token for API calls.
    *   `refresh_token` (string): The token used to renew the access token.

### `generate_session_token`

*   **Type**: `JWT` (string)
*   **Description**: A signed JWT string representing the user's session, valid for 7 days.

### `validate_session_token`

*   **Type**: `SessionPayload` (dictionary)
*   **Description**: The decoded payload of the JWT, typically a dictionary containing:
    *   `iat` (integer): Issued at timestamp.
    *   `exp` (integer): Expiration timestamp.
    *   `sub` (string/integer): The user ID.

### `logout` (API Endpoint)

*   **Type**: `JSONResponse` (from `fastapi.responses`)
*   **Description**: A JSON response with a message confirming successful logout. This response also includes instructions to delete the `session_token` cookie from the client.
    ```json
    {"message": "Logged out successfully"}
    ```

### `get_current_user`

*   **Type**: `User` (Pydantic model)
*   **Description**: The complete `User` object retrieved from the database, corresponding to the authenticated user.

### `User` (Pydantic Model)

*   **Type**: An instance of the `User` Pydantic model.
*   **Description**: An object containing the user's full profile data, including GitHub access tokens and installation ID, for internal application use.

## 5. Usage Examples

### 5.1. Initiating GitHub OAuth Login

To start the GitHub login process, a user simply navigates to the `/login` endpoint.

```python
# Example: Client-side (e.g., browser redirect)
# User navigates to:
# GET /login

# Example: Server-side (FastAPI route definition)
from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from app.clients.github import build_oauth_url
import secrets

router = APIRouter()

@router.get("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT, tags=["Authentication"])
async def login() -> RedirectResponse:
  """Initiate GitHub OAuth authentication flow."""
  state: str = secrets.token_urlsafe(16) # OAuthState type
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

# Example: How build_oauth_url might be used internally
# from app.clients.github import build_oauth_url
# state_token = "some_random_state_string"
# github_auth_url = build_oauth_url(state_token)
# print(f"Redirect user to: {github_auth_url}")
# # Expected output: https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_CALLBACK_URL&state=some_random_state_string
```

### 5.2. Exchanging GitHub Authorization Code for Tokens

This typically happens in a GitHub OAuth callback endpoint (e.g., `/auth/github/callback`, not explicitly provided but implied by `get_user_access_token`).

```python
# Example: Using get_user_access_token in a callback route
from app.clients.github import get_user_access_token, GitHubAPIError
from app.utils.auth import generate_session_token
from app.services.user import create_or_update_user # Assuming such a service exists
from fastapi import HTTPException, status, Request
from fastapi.responses import RedirectResponse

# Assume this is part of a /auth/github/callback route
async def github_callback_handler(code: str, state: str, request: Request):
    # 1. Validate CSRF state (compare with cookie)
    oauth_state_cookie = request.cookies.get("oauth_state")
    if not oauth_state_cookie or oauth_state_cookie != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    # 2. Exchange code for tokens
    try:
        user_tokens = await get_user_access_token(code)
        access_token = user_tokens["access_token"]
        refresh_token = user_tokens.get("refresh_token") # Optional
    except GitHubAPIError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"GitHub token exchange failed: {e}")

    # 3. Get user profile from GitHub (not shown, but would use access_token)
    # github_user_profile = await get_user_profile(access_token)

    # 4. Create or update user in database
    # user_id = await create_or_update_user(github_user_profile, access_token, refresh_token)
    user_id = "some_user_id_from_db" # Placeholder

    # 5. Generate session token
    session_token = generate_session_token(user_id)

    # 6. Set session cookie and redirect
    response = RedirectResponse(url="/dashboard") # Redirect to a protected route
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=60 * 60 * 24 * 7, # 7 days
        httponly=True,
        secure=False, # Set to true in prod
        samesite="lax"
    )
    response.delete_cookie("oauth_state") # Clean up state cookie
    return response
```

### 5.3. Securing API Routes with `get_current_user`

```python
# Example: Using get_current_user as a FastAPI dependency
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.user import User # Assuming User model is defined

router = APIRouter()

@router.get("/protected", tags=["Protected"])
async def protected_route(current_user: User = Depends(get_current_user)):
  """
  An example protected route that requires an authenticated user.
  """
  return {"message": f"Welcome, {current_user.name}! Your ID is {current_user.id}"}

# If a request to /protected comes without a valid session_token cookie,
# get_current_user will raise an HTTPException, and the route handler won't be called.
```

### 5.4. Generating and Validating Session Tokens (Internal Use)

```python
# Example: Generating a session token
from app.utils.auth import generate_session_token
from app.types import UserId, JWT # Assuming these types are defined

user_id: UserId = "user123"
session_jwt: JWT = generate_session_token(user_id)
print(f"Generated JWT: {session_jwt}")
# Expected output: Generated JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Example: Validating a session token
from app.utils.auth import validate_session_token
from app.types import SessionPayload
import jwt # PyJWT library exceptions

try:
    decoded_payload: SessionPayload = validate_session_token(session_jwt)
    print(f"Decoded payload: {decoded_payload}")
    # Expected output: Decoded payload: {'iat': 1678886400, 'exp': 1679491200, 'sub': 'user123'}
except jwt.ExpiredSignatureError:
    print("Token has expired.")
except jwt.InvalidTokenError:
    print("Invalid token (e.g., malformed or invalid signature).")
```

### 5.5. Logging Out

```python
# Example: Client-side (e.g., JavaScript fetch request)
/*
fetch('/logout', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    console.log(data.message); // "Logged out successfully"
    // Redirect user to login page or update UI
})
.catch(error => console.error('Logout failed:', error));
*/

# Example: Server-side (FastAPI route definition)
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/logout", status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout() -> JSONResponse:
  """Log out the current user by clearing their session cookie."""
  response = JSONResponse(content={"message": "Logged out successfully"})
  response.delete_cookie("session_token")
  return response
```

## 6. Error Handling

This section outlines the exceptions that can be raised by the authentication system components.

### `get_current_user`

*   **`HTTPException` (status_code=401 Unauthorized)**
    *   **Description**: Raised if the authentication process fails at any stage.
    *   **Reasons**:
        *   `session_token` cookie is missing from the request.
        *   The `session_token` is invalid (e.g., malformed, incorrect signature).
        *   The `session_token` has expired.
        *   The user ID extracted from the token does not correspond to an existing user in the database.

### `get_user_access_token`

*   **`GitHubAPIError`**
    *   **Description**: A custom exception raised if the token exchange process with GitHub fails. This could be due to an invalid authorization code, network issues, or GitHub API errors.

### `validate_session_token`

*   **`jwt.ExpiredSignatureError` (from `PyJWT`)**
    *   **Description**: Raised if the `exp` (expiration) claim in the JWT indicates that the token is no longer valid.
*   **`jwt.InvalidTokenError` (from `PyJWT`)**
    *   **Description**: A general exception for various token validation failures, including:
        *   Token is malformed (e.g., not a valid JWT structure).
        *   Token signature is invalid (e.g., tampered with, signed with a different secret key).
        *   Other validation errors (e.g., invalid claims, incorrect algorithm).

### `login` (API Endpoint)

*   **Implicit Errors**: While the `login` endpoint itself primarily performs a redirect, errors could occur if `build_oauth_url` fails (e.g., misconfiguration), though this is less likely to raise an explicit exception from the endpoint itself and more likely to be a server-side configuration issue.

### `logout` (API Endpoint)

*   No explicit exceptions are raised by the `logout` endpoint itself, as it primarily clears a cookie and returns a success message.

## 7. Common Use Cases

### 7.1. User Login via GitHub

1.  **User initiates login**: A user clicks a "Login with GitHub" button on the frontend, which triggers a request to the `/login` API endpoint.
2.  **Redirect to GitHub**: The `/login` endpoint generates a CSRF `oauth_state` token, sets it as an HTTP-only cookie, and redirects the user's browser to GitHub's OAuth authorization page (`build_oauth_url`).
3.  **GitHub Authorization**: The user grants (or denies) permissions to the Otto application on GitHub.
4.  **GitHub Callback**: GitHub redirects the user's browser back to the configured `GITHUB_CALLBACK_URL` (e.g., `/auth/github/callback`), including an authorization `code` and the `state` token.
5.  **Token Exchange**: The callback endpoint validates the `state` token against the cookie, then uses `get_user_access_token` to exchange the `code` for GitHub `access_token` and `refresh_token`.
6.  **User Provisioning**: The application uses the GitHub `access_token` to fetch the user's profile from GitHub, creates or updates the user's record in the database (including storing the GitHub tokens and potentially an `installation_id` in the `User` model), and retrieves the internal `user_id`.
7.  **Session Creation**: A session JWT is generated using `generate_session_token` with the `user_id`.
8.  **Session Cookie & Redirect**: The session JWT is set as an HTTP-only `session_token` cookie, and the user is redirected to a protected area of the application (e.g., `/dashboard`).

### 7.2. Accessing Protected API Endpoints

1.  **Authenticated Request**: A logged-in user's frontend application makes an API request to a protected endpoint (e.g., `/api/projects`). The browser automatically includes the `session_token` cookie.
2.  **Dependency Injection**: The FastAPI route for `/api/projects` has `current_user: User = Depends(get_current_user)` injected.
3.  **Session Validation**: `get_current_user` extracts the `session_token` from the request cookie, calls `validate_session_token` to verify its authenticity and expiration.
4.  **User Retrieval**: If valid, `get_current_user` extracts the `user_id` from the token and fetches the complete `User` object from the database.
5.  **Route Execution**: The `User` object is passed to the route handler, allowing the application logic to access user-specific data (e.g., `current_user.id`, `current_user.github_access_token`) to fulfill the request.
6.  **Unauthorized Access**: If the `session_token` is missing, invalid, or expired, `get_current_user` raises an `HTTPException(401)`, and the request is rejected before reaching the route handler.

### 7.3. User Logout

1.  **User initiates logout**: A user clicks a "Logout" button on the frontend, which sends a POST request to the `/logout` API endpoint.
2.  **Session Invalidation**: The `/logout` endpoint receives the request, creates a success `JSONResponse`, and crucially, instructs the client's browser to delete the `session_token` cookie.
3.  **Frontend Update**: The frontend receives the success response, clears any local user data, and typically redirects the user to the public login page.
4.  **Future Requests**: Any subsequent requests from the user will no longer include a valid `session_token`, leading to `401 Unauthorized` if they attempt to access protected resources.