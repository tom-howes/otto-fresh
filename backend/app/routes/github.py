from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from app.dependencies.auth import get_current_user
from app.clients.github import get_installation_token, list_installation_repositories, GitHubAPIError
from app.models import User
from app.types import GitHubRepo

router = APIRouter(prefix="/github", tags=["GitHub"])
  
@router.get("/install", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def install_github_app(current_user: User = Depends(get_current_user)) -> RedirectResponse:
  """Redirect user to install the GitHub App on their repositories.

  Returns:
      Redirect to GitHub App installation page.
  """
  install_url = "https://github.com/apps/otto-pm/installations/new"
  return RedirectResponse(url=install_url)

@router.get("/repos", status_code=status.HTTP_200_OK)
async def get_installed_repos(current_user: User = Depends(get_current_user)) -> list[GitHubRepo]:
  """List repositories where the GitHub App is installed.
    
  Args:
      current_user: The authenticated user.
        
  Returns:
      List of repositories accessible via the installation.
        
  Raises:
      HTTPException: 400 if app not installed.
      HTTPException: 502 if GitHub API fails.
  """
  installation_id = current_user.get("installation_id")
    
  if not installation_id:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="GitHub App not installed. Visit /github/install first."
    )
    
  try:
    # Get installation token
    installation_token = await get_installation_token(str(installation_id))
    
    # List repos accessible to this installation
    repos = await list_installation_repositories(installation_token)
    return repos
  except GitHubAPIError as e:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to fetch repositories"
    )