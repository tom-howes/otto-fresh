from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.clients.github import list_user_repositories, GitHubAPIError
from app.models.user import User
from app.types import GitHubRepo

router = APIRouter(prefix="/github", tags=["GitHub"])

@router.get("/repos", status_code=status.HTTP_200_OK)
async def get_user_repos(current_user: User = Depends(get_current_user)) -> list[GitHubRepo]:
  """List repositories accessible to the current user.
    
  Args:
      current_user: The authenticated user from the session.
      
  Returns:
      List of repositories the user can access.
      
  Raises:
      HTTPException: 502 if GitHub API request fails.
  """
  try:
    repos = await list_user_repositories(current_user["github_access_token"])
    return repos
  except GitHubAPIError as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAYA, detail="Failed to fetch repositories")

  