from fastapi import Request, HTTPException, status
from app.utils.auth import validate_session_token
from app.clients.firebase import db
from app.models.user import User

async def get_current_user(request: Request) -> User:
  session_token = request.cookies.get("session_token")
  if not session_token:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session token missing")
  
  try:
    decoded_payload = validate_session_token(session_token)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session token invalid")
  
  try:
    user_ref = db.collection("users").document(decoded_payload["sub"])
    user_doc = await user_ref.get()
    if user_doc.exists:
      return user_doc.to_dict()
    else:
      raise Exception()
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User id invalid")