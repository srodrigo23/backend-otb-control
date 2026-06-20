from fastapi import Cookie, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.models.user import User
from app.db.database import get_db

from app.services.jwt import decode_token
from app.services.auth import get_user_by_id

def get_current_user(
  access_token:str | None = Cookie(default=None),
  db: Session = Depends(get_db)
)-> User:
  
  if not access_token:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="not authorized"
    )
  
  payload = decode_token(token=access_token)
  if not payload:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid token or expired token"
    )
  
  user = get_user_by_id(db, user_id=payload["sub"])
  if not user:
    # or not user.is_active
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail="User not found"
    )
  return user