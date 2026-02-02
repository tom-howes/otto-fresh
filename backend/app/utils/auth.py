from app.config import JWT_SECRET_KEY
import jwt
import time
from app.types import SessionPayload, JWT

def generate_session_token(user_id: str) -> JWT:
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