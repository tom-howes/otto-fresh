from app.config import JWT_SECRET_KEY
import jwt
import time
from app.models import SessionPayload, JWT, UserId

SESSION_EXPIRY = 60 * 60 * 6       # 6 hours
REFRESH_EXPIRY = 60 * 60 * 24 * 7  # 7 days


def generate_session_token(user_id: UserId) -> JWT:
    """Generate a short-lived JWT session token (6 hours)."""
    payload: SessionPayload = {
        "iat": int(time.time()),
        "exp": int(time.time() + SESSION_EXPIRY),
        "sub": user_id
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user_id: UserId) -> JWT:
    """Generate a long-lived JWT refresh token (7 days)."""
    payload: SessionPayload = {
        "iat": int(time.time()),
        "exp": int(time.time() + REFRESH_EXPIRY),
        "sub": user_id
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def validate_session_token(token: JWT) -> SessionPayload:
    """Validate and decode a JWT token (works for both session and refresh tokens)."""
    decoded_payload: SessionPayload = jwt.decode(
        token, key=JWT_SECRET_KEY, algorithms=["HS256"])
    return decoded_payload
