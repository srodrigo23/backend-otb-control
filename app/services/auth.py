from sqlalchemy.orm import Session
from app.models.user import User
from uuid import UUID 
import bcrypt


# -------------------- Queries -----------------------
def get_user_by_username(db: Session, username:str):
  return db.query(User).filter(User.username == username).first()

def get_user_by_id(db:Session, user_id:int | UUID) -> User | None:
  return db.query(User).filter(User.id == user_id).first()

# ---------------- password methods -------------------

def hash_password(plain_text_password:str) -> str:
  password_bytes = plain_text_password.endode("utf-8")
  hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
  return hashed_bytes.decode('utf-8') 
  
def verify_password(plain_text_password:str, hashed_password:str)->bool:
  return bcrypt.checkpw(
    password=plain_text_password.encode('utf-8'),
    hashed_password=hashed_password.encode('utf-8')
  )

def verify_credentials(username:str, password:str, db:Session) -> User | None:
  
  user = get_user_by_username(db, username)
  if not user:
    #Simulation to avoid timing attacks
    bcrypt.checkpw(b"dummy", bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
    return None
  
  # If there is an error with incorrect password have to be an custom message
  if not verify_password(plain_text_password=password, hashed_password=user.password_hash):
    return None
  
  # TODO: for inactive users have to be an espcific error
  # if not user.is_active:
  #   return None
  
  return user