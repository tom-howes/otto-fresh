"""
In-memory user store - bypasses Firestore for testing
"""
from app.models import User, UserCreate, UserUpdate
from app.types import UserId
from datetime import datetime

_users = {}

async def get_user_by_id(user_id: UserId) -> User:
    user = _users.get(str(user_id))
    print(f"  ✓ get_user: {'Found' if user else 'Not found'}")
    return user


async def create_user(user_data: UserCreate) -> User:
    user_dict = user_data.model_dump()
    user_dict["workspace_ids"] = []
    user_dict["created_at"] = datetime.now()
    user_dict["updated_at"] = datetime.now()
    
    _users[str(user_data.id)] = user_dict
    print(f"  ✓ Created user (memory): {user_data.github_username}")
    return user_dict


async def update_user(user_id: UserId, update_data: UserUpdate) -> None:
    if str(user_id) in _users:
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.now()
        _users[str(user_id)].update(update_dict)
        print(f"  ✓ Updated user (memory)")


async def get_user_installation_id(user_id: UserId):
    user = _users.get(str(user_id))
    return user.get("installation_id") if user else None


async def get_user_workspaces(user_id: UserId):
    user = _users.get(str(user_id))
    return user.get("workspace_ids", []) if user else []


async def add_workspace_to_user(user_id: UserId, workspace_id):
    if str(user_id) in _users:
        _users[str(user_id)].setdefault("workspace_ids", []).append(workspace_id)


async def remove_workspace_from_user(user_id: UserId, workspace_id):
    if str(user_id) in _users:
        workspace_ids = _users[str(user_id)].get("workspace_ids", [])
        if workspace_id in workspace_ids:
            workspace_ids.remove(workspace_id)