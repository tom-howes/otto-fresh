from app.config import JWT_SECRET_KEY
import jwt
import time

def generate_session_token(user_id):
  payload = {
    "iat": int(time.time()),
    "exp": int(time.time() + 60 * 60 * 24 * 7),  # 7 days from current time
    "sub": user_id
  }
  token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
  return token

def validate_session_token(token):
  decoded_payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=["HS256"])
  return decoded_payload