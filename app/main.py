from fastapi import Depends, FastAPI, HTTPException, Response, status, Cookie
from sqlalchemy.orm import Session

from .services import crud
# from . import models
from .schemas import schema as schemas
from .db.database import SessionLocal, engine, Base
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .schemas.schema import LoginRequest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from .routers import neighbors, meets, measures, collect_debts, debts
from .dependencies import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()
# config for CORS
origins = [
  settings.client_url_dev,
  settings.client_url_prod,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(neighbors.router)
app.include_router(meets.router)
app.include_router(measures.router)
app.include_router(collect_debts.router)
app.include_router(debts.router)

@app.get("/")
async def root():
  return {"message": "Hello World"}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.ALGORITHM, algorithm=settings.ALGORITHM)

  
@app.post("/login")
def login(data:LoginRequest, response: Response, db: Session= Depends(get_db)):
  user = crud.get_user_by_username(db=db, username=data.username)
  if user is not None:
    if user.verify_password(data.password):
      response.status_code = status.HTTP_202_ACCEPTED
      
      token = create_access_token({"sub": data.username})
      
      response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.prod,  # True in production (HTTPS)
        samesite="lax",
      )
      return {"message": "Login successful"}
  return {
    'success':'False'
  }
  
@app.get("/me")
def get_me(access_token: str = Cookie(None)):
  if not access_token:
    raise HTTPException(status_code=401, detail="Not authenticated")
  try:
    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    username = payload.get("sub")
    return {"username": username}
  except JWTError:
    raise HTTPException(status_code=401, detail="Invalid token")
  
