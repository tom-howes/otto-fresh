# Issue Management Backend API Checklist

## Phase 1: Project Setup

- [x] Create FastAPI project with virtual environment
- [x] Install dependencies (fastapi, uvicorn, firebase-admin, httpx, pydantic, python-dotenv)
- [x] Set up project structure:
  - [x] `/app` main package
  - [x] `/app/routes` for API endpoints
  - [x] `/app/services` for business logic
  - [x] `/app/models` for Pydantic schemas
  - [x] `/app/dependencies` for auth and other dependencies
  - [x] `/app/clients` for external API wrappers (GitHub)
  - [x] `/app/config.py` for configuration
- [x] Create Firebase project and download service account credentials
- [x] Set up environment variables (.env file, add to .gitignore)
- [x] Initialize Firebase Admin SDK connection

---

## Phase 2: Firestore Data Model Setup

- [x] Plan document structure for Users collection
- [x] Plan document structure for Workspaces collection
- [x] Plan subcollection structure for Sections (under Workspaces)
- [x] Plan subcollection structure for Issues (under Workspaces)
- [x] Plan subcollection structure for Comments (under Issues)
- [x] Create Pydantic models for each entity:
  - [x] User (create, read, update schemas)
  - [x] Workspace (create, read, update schemas)
  - [x] Section (create, read, update schemas)
  - [x] Issue (create, read, update schemas)
  - [x] Comment (create, read, update schemas)

---

## Phase 3: Authentication

### GitHub App Setup
- [x] Create a GitHub App (not OAuth App) in GitHub Developer Settings
  - [x] Set app name and description
  - [x] Set homepage URL
  - [x] Set callback URL for user authentication (`/auth/github/callback`)
  - [x] Set webhook URL for receiving events (`/webhooks/github`)
  - [x] Generate and download private key (.pem file)
  - [x] Set required permissions:
    - [x] Repository contents: Read and write
    - [x] Metadata: Read
  - [x] Subscribe to webhook events:
    - [x] Push
- [x] Add GitHub App credentials to environment variables:
  - [x] App ID
  - [x] Client ID
  - [x] Client secret
  - [x] Private key path
  - [x] Webhook secret
- [x] Create GitHub App client wrapper

### Auth Endpoints
- [x] `GET /auth/github` - Redirect to GitHub authorization
- [x] `GET /auth/github/callback` - Handle OAuth callback
  - [x] Exchange code for user access token
  - [x] Fetch GitHub user profile
  - [x] Create or update user in Firestore
  - [x] Generate and return session token/JWT
- [x] `POST /auth/logout` - Invalidate session (if using server-side sessions)

### Auth Dependencies
- [x] Create `get_current_user` dependency (validates token, returns user)
- [x] Create token generation utility
- [x] Create token validation utility

---

## Phase 4: User Service & Endpoints

### User Service
- [ ] `get_user_by_id(user_id)` - Fetch user from Firestore
- [ ] `update_user(user_id, data)` - Update user profile
- [ ] `get_user_workspaces(user_id)` - List workspaces user belongs to
- [ ] `add_workspace_to_user(user_id, workspace_id)` - Add workspace to user's list
- [ ] `remove_workspace_from_user(user_id, workspace_id)` - Remove workspace from list

### User Endpoints
- [ ] `GET /users/me` - Get current user profile
- [ ] `PATCH /users/me` - Update current user profile
- [ ] `GET /users/me/workspaces` - List user's workspaces

---

## Phase 5: Workspace Service & Endpoints

### Workspace Service
- [ ] `create_workspace(user_id, repo_info, installation_id)` - Create workspace with repo
- [ ] `get_workspace(workspace_id)` - Fetch workspace details
- [ ] `get_workspace_by_join_code(code)` - Find workspace by join code
- [ ] `get_workspace_by_repo(owner, repo)` - Find workspace by repository (for webhooks)
- [ ] `generate_join_code()` - Generate unique join code
- [ ] `add_member(workspace_id, user_id)` - Add user to workspace
- [ ] `remove_member(workspace_id, user_id)` - Remove user from workspace
- [ ] `get_members(workspace_id)` - List workspace members
- [ ] `is_member(workspace_id, user_id)` - Check membership
- [ ] `initialize_default_sections(workspace_id)` - Create TO DO, IN PROGRESS, IN REVIEW, DONE
- [ ] `update_installation_id(workspace_id, installation_id)` - Update GitHub App installation

### Workspace Membership Dependency
- [ ] Create `verify_workspace_membership` dependency
  - [ ] Takes workspace_id from path
  - [ ] Verifies current user is a member
  - [ ] Returns workspace data or raises 403

### Workspace Endpoints
- [ ] `POST /workspaces` - Create workspace (connect repository)
- [ ] `POST /workspaces/join` - Join workspace by code
- [ ] `GET /workspaces/{workspace_id}` - Get workspace details
- [ ] `GET /workspaces/{workspace_id}/members` - List members
- [ ] `DELETE /workspaces/{workspace_id}/members/me` - Leave workspace

---

## Phase 6: GitHub Integration

### GitHub App Client
- [ ] Create GitHub App authentication utilities
  - [ ] Generate JWT from private key for app authentication
  - [ ] Get installation access token for a specific installation
- [ ] Create GitHub API client wrapper
- [ ] `get_user_repos(user_access_token)` - List user's repositories
- [ ] `get_repo(installation_token, owner, repo)` - Get repository details
- [ ] `check_repo_permissions(user_access_token, owner, repo)` - Verify user has access
- [ ] `get_default_branch_sha(installation_token, owner, repo)` - Get HEAD SHA
- [ ] `create_branch(installation_token, owner, repo, branch_name, sha)` - Create new branch
- [ ] `get_repo_contents(installation_token, owner, repo, path)` - Read file contents for RAG

### GitHub App Installation Flow
- [ ] `GET /github/install` - Redirect user to GitHub App installation page
- [ ] `GET /github/install/callback` - Handle post-installation redirect
  - [ ] Store installation ID with workspace
  - [ ] Verify installation has required permissions

### GitHub Endpoints
- [ ] `GET /github/repos` - List user's repositories for selection
- [ ] `GET /github/repos/{owner}/{repo}` - Get repository details

### Webhook Handler
- [ ] `POST /webhooks/github` - Receive GitHub webhook events
  - [ ] Verify webhook signature using webhook secret
  - [ ] Parse event type from headers
  - [ ] Handle `push` events:
    - [ ] Check if push is to default/main branch
    - [ ] Identify which workspace the repository belongs to
    - [ ] Trigger RAG pipeline for the repository
  - [ ] Handle `installation` events (app installed/uninstalled)
  - [ ] Return 200 OK promptly (process async if needed)

---

## Phase 7: Section Service & Endpoints

### Section Service
- [ ] `create_section(workspace_id, title, position)` - Create section
- [ ] `get_sections(workspace_id)` - List sections ordered by position
- [ ] `get_section(workspace_id, section_id)` - Get single section
- [ ] `update_section(workspace_id, section_id, data)` - Update section
- [ ] `reorder_section(workspace_id, section_id, new_position)` - Change position
- [ ] `delete_section(workspace_id, section_id)` - Delete section
- [ ] `get_next_position(workspace_id)` - Calculate next position value

### Section Endpoints
- [ ] `GET /workspaces/{workspace_id}/sections` - List sections
- [ ] `POST /workspaces/{workspace_id}/sections` - Create section
- [ ] `PATCH /workspaces/{workspace_id}/sections/{section_id}` - Update section
- [ ] `DELETE /workspaces/{workspace_id}/sections/{section_id}` - Delete section

---

## Phase 8: Issue Service & Endpoints

### Issue Service
- [ ] `create_issue(workspace_id, data)` - Create issue
- [ ] `get_issues(workspace_id, filters)` - List issues with optional filters
- [ ] `get_issue(workspace_id, issue_id)` - Get single issue
- [ ] `update_issue(workspace_id, issue_id, data)` - Update issue
- [ ] `move_issue(workspace_id, issue_id, section_id, position)` - Move to section
- [ ] `delete_issue(workspace_id, issue_id)` - Delete issue
- [ ] `create_issue_branch(workspace_id, issue_id)` - Create GitHub branch
- [ ] `validate_assignee(workspace_id, user_id)` - Check user is member
- [ ] `generate_branch_name(issue)` - Create branch name from issue

### Issue Endpoints
- [ ] `GET /workspaces/{workspace_id}/issues` - List issues
- [ ] `POST /workspaces/{workspace_id}/issues` - Create issue
- [ ] `GET /workspaces/{workspace_id}/issues/{issue_id}` - Get issue
- [ ] `PATCH /workspaces/{workspace_id}/issues/{issue_id}` - Update issue
- [ ] `PATCH /workspaces/{workspace_id}/issues/{issue_id}/move` - Move issue
- [ ] `DELETE /workspaces/{workspace_id}/issues/{issue_id}` - Delete issue
- [ ] `POST /workspaces/{workspace_id}/issues/{issue_id}/branch` - Create branch

---

## Phase 9: Comment Service & Endpoints

### Comment Service
- [ ] `create_comment(workspace_id, issue_id, user_id, content)` - Add comment
- [ ] `get_comments(workspace_id, issue_id)` - List comments on issue
- [ ] `update_comment(workspace_id, issue_id, comment_id, content)` - Edit comment
- [ ] `delete_comment(workspace_id, issue_id, comment_id)` - Delete comment
- [ ] `is_comment_author(comment_id, user_id)` - Verify ownership

### Comment Endpoints
- [ ] `GET /workspaces/{workspace_id}/issues/{issue_id}/comments` - List comments
- [ ] `POST /workspaces/{workspace_id}/issues/{issue_id}/comments` - Add comment
- [ ] `PATCH /workspaces/{workspace_id}/issues/{issue_id}/comments/{comment_id}` - Edit
- [ ] `DELETE /workspaces/{workspace_id}/issues/{issue_id}/comments/{comment_id}` - Delete

---

## Phase 10: Error Handling & Validation

- [ ] Create custom exception classes
  - [ ] `NotFoundError`
  - [ ] `UnauthorizedError`
  - [ ] `ForbiddenError`
  - [ ] `ValidationError`
  - [ ] `GitHubAPIError`
- [ ] Create exception handlers for FastAPI
- [ ] Create standard error response model
- [ ] Add input validation to all Pydantic models
- [ ] Add workspace membership validation to all workspace-scoped endpoints
- [ ] Add comment ownership validation to edit/delete endpoints

---

## Phase 11: Testing

- [ ] Set up pytest with async support
- [ ] Create test fixtures (mock Firestore, mock GitHub API)
- [ ] Write unit tests for services
  - [ ] User service tests
  - [ ] Workspace service tests
  - [ ] Section service tests
  - [ ] Issue service tests
  - [ ] Comment service tests
- [ ] Write integration tests for endpoints
  - [ ] Auth flow tests
  - [ ] Workspace CRUD tests
  - [ ] Section CRUD tests
  - [ ] Issue CRUD tests
  - [ ] Comment CRUD tests
- [ ] Test error cases and edge cases

---

## Phase 12: Documentation & Deployment Prep

- [ ] Review and customize OpenAPI documentation
- [ ] Add descriptions to all endpoints
- [ ] Add example requests/responses to schemas
- [ ] Create README with setup instructions
- [ ] Set up environment variable documentation
- [ ] Configure CORS for frontend origin
- [ ] Set up logging
- [ ] Create Dockerfile (optional)
- [ ] Set up CI/CD pipeline (optional)

---

## Phase 13: RAG Pipeline Integration

### RAG Service
- [ ] Create RAG pipeline service module
- [ ] `trigger_rag_pipeline(workspace_id, repo_owner, repo_name)` - Main entry point
- [ ] `fetch_repository_contents(installation_token, owner, repo)` - Clone or fetch repo files
- [ ] `chunk_repository_data(files)` - Split code/docs into chunks
- [ ] `generate_embeddings(chunks)` - Create vector embeddings
- [ ] `store_embeddings(workspace_id, embeddings)` - Save to vector database

### Vector Database Setup
- [ ] Choose vector database (Pinecone, Weaviate, Chroma, etc.)
- [ ] Set up vector database connection
- [ ] Create index/collection for workspace embeddings
- [ ] Add vector database credentials to environment variables

### Background Processing
- [ ] Set up async task processing (Celery, FastAPI BackgroundTasks, or similar)
- [ ] Handle long-running RAG pipeline without blocking webhook response
- [ ] Add status tracking for RAG pipeline jobs
- [ ] Handle errors and retries gracefully

### RAG Query Endpoint (optional)
- [ ] `POST /workspaces/{workspace_id}/query` - Query the RAG system
  - [ ] Accept natural language question
  - [ ] Search vector database for relevant chunks
  - [ ] Return context for LLM or LLM-generated response

---

## Optional Enhancements

- [ ] Add rate limiting
- [ ] Add request logging middleware
- [ ] Implement workspace admin roles
- [ ] Add join code expiration/regeneration
- [ ] Add issue activity history
- [ ] Add webhook support for GitHub events
- [ ] Implement soft delete for issues
- [ ] Add pagination to list endpoints