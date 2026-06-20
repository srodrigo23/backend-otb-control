from fastapi import Response
from app.core.settings import settings

COOKIE_NAME = "access_token"

def set_auth_cookie(response: Response, token: str) -> None:
  response.set_cookie(
    key=COOKIE_NAME,
    value=token,
    httponly=True,
    secure=settings.cookie_secure,
    samesite=settings.cookie_samesite,
    max_age=60 * 60 * 24,
    path="/",             # defines scope
  )

def delete_auth_cookie(response: Response) -> None:
  response.delete_cookie(
    key=COOKIE_NAME,
    httponly=True,
    secure=settings.cookie_secure,     # same
    samesite=settings.cookie_samesite, # same
    path="/",                          # same
  )