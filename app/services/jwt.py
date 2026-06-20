from datetime import datetime, timedelta, timezone
from typing import Any
import jwt

from app.core.settings import settings


def create_access_token(payload: dict[str, Any]) -> str:
  data = payload.copy()
  expire = datetime.now(timezone.utc) + timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
  )
  data["exp"] = expire
  return jwt.encode(
    data, 
    settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
  )


def decode_token(token:str) -> dict[str, Any] | None:
  """
  Decode and validate token. Returns payload or None if it's invalid
  PyJWT fires exception if this expires or corrupt sign
  """
  try:
    payload = jwt.decode(
      token,
      settings.SECRET_KEY,
      algorithms=[settings.ALGORITHM],
      options={"require":["exp", "sub"]}
    )
    return payload
  except jwt.ExpiredSignatureError:
    return None
  except jwt.InvalidTokenError:
    return None