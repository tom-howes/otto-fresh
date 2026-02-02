# Task Management Backend API Checklist

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
- [x] Plan subcollection structure for Tasks (under Workspaces)
- [x] Plan subcollection structure for Comments (under Tasks)
- [x] Create Pydantic models for each entity:
  - [x] User (create, read, update schemas)
  - [x] Workspace (create, read, update schemas)
  - [x] Section (create, read, update schemas)
  - [x] Task (create, read, update schemas)
  - [x] Comment (create, read, update schemas)

---

## Phase 3: Authentication

### GitHub OAuth Setup
- [ ] Register OAuth App on GitHub (get client ID and secret)
- [ ] Add GitHub credentials to environment variables
- [ ] Create GitHub OAuth client wrapper

### Auth Endpoints
- [ ] `GET /auth/github` - Redirect to GitHub authorization
- [ ] `GET /auth/github/callback` - Handle OAuth callback
  - [ ] Exchange code for access token
  - [ ] Fetch GitHub user profile
  - [ ] Create or update user in Firestore
  - [ ] Generate and return session token/JWT
- [ ] `POST /auth/logout` - Invalidate session (if using server-side sessions)

### Auth Dependencies
- [ ] Create `get_current_user` dependency (validates token, returns user)
- [ ] Create token generation utility
- [ ] Create token validation utility

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
- [ ] `create_workspace(user_id, repo_info)` - Create workspace with repo
- [ ] `get_workspace(workspace_id)` - Fetch workspace details
- [ ] `get_workspace_by_join_code(code)` - Find workspace by join code
- [ ] `generate_join_code()` - Generate unique join code
- [ ] `add_member(workspace_id, user_id)` - Add user to workspace
- [ ] `remove_member(workspace_id, user_id)` - Remove user from workspace
- [ ] `get_members(workspace_id)` - List workspace members
- [ ] `is_member(workspace_id, user_id)` - Check membership
- [ ] `initialize_default_sections(workspace_id)` - Create TO DO, IN PROGRESS, IN REVIEW, DONE

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

### GitHub Client
- [ ] Create GitHub API client wrapper
- [ ] `get_user_repos(access_token)` - List user's repositories
- [ ] `get_repo(access_token, owner, repo)` - Get repository details
- [ ] `check_repo_permissions(access_token, owner, repo)` - Verify user has push access
- [ ] `get_default_branch_sha(access_token, owner, repo)` - Get HEAD SHA
- [ ] `create_branch(access_token, owner, repo, branch_name, sha)` - Create new branch

### GitHub Endpoints
- [ ] `GET /github/repos` - List user's repositories for selection
- [ ] `GET /github/repos/{owner}/{repo}` - Get repository details

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

## Phase 8: Task Service & Endpoints

### Task Service
- [ ] `create_task(workspace_id, data)` - Create task
- [ ] `get_tasks(workspace_id, filters)` - List tasks with optional filters
- [ ] `get_task(workspace_id, task_id)` - Get single task
- [ ] `update_task(workspace_id, task_id, data)` - Update task
- [ ] `move_task(workspace_id, task_id, section_id, position)` - Move to section
- [ ] `delete_task(workspace_id, task_id)` - Delete task
- [ ] `create_task_branch(workspace_id, task_id)` - Create GitHub branch
- [ ] `validate_assignee(workspace_id, user_id)` - Check user is member
- [ ] `generate_branch_name(task)` - Create branch name from task

### Task Endpoints
- [ ] `GET /workspaces/{workspace_id}/tasks` - List tasks
- [ ] `POST /workspaces/{workspace_id}/tasks` - Create task
- [ ] `GET /workspaces/{workspace_id}/tasks/{task_id}` - Get task
- [ ] `PATCH /workspaces/{workspace_id}/tasks/{task_id}` - Update task
- [ ] `PATCH /workspaces/{workspace_id}/tasks/{task_id}/move` - Move task
- [ ] `DELETE /workspaces/{workspace_id}/tasks/{task_id}` - Delete task
- [ ] `POST /workspaces/{workspace_id}/tasks/{task_id}/branch` - Create branch

---

## Phase 9: Comment Service & Endpoints

### Comment Service
- [ ] `create_comment(workspace_id, task_id, user_id, content)` - Add comment
- [ ] `get_comments(workspace_id, task_id)` - List comments on task
- [ ] `update_comment(workspace_id, task_id, comment_id, content)` - Edit comment
- [ ] `delete_comment(workspace_id, task_id, comment_id)` - Delete comment
- [ ] `is_comment_author(comment_id, user_id)` - Verify ownership

### Comment Endpoints
- [ ] `GET /workspaces/{workspace_id}/tasks/{task_id}/comments` - List comments
- [ ] `POST /workspaces/{workspace_id}/tasks/{task_id}/comments` - Add comment
- [ ] `PATCH /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}` - Edit
- [ ] `DELETE /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}` - Delete

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
  - [ ] Task service tests
  - [ ] Comment service tests
- [ ] Write integration tests for endpoints
  - [ ] Auth flow tests
  - [ ] Workspace CRUD tests
  - [ ] Section CRUD tests
  - [ ] Task CRUD tests
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

## Optional Enhancements

- [ ] Add rate limiting
- [ ] Add request logging middleware
- [ ] Implement workspace admin roles
- [ ] Add join code expiration/regeneration
- [ ] Add task activity history
- [ ] Add webhook support for GitHub events
- [ ] Implement soft delete for tasks
- [ ] Add pagination to list endpoints