
import bcrypt
from sqlalchemy import Column, Integer, String, Enum
from app.db.database import Base

from ..enums import UserType

class User(Base):
  
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(64))
  password_hash = Column(String(128))
  role = Column(Enum(UserType), nullable=False)
  
  def verify_password(self, password):
    pwhash = bcrypt.hashpw(password, self.password_hash)
    return pwhash == self.password_hash
  
  