from sqlalchemy.orm import sessionmaker
import sqlalchemy
from app.models import User
from app.settings import settings

from app.enums import UserType
import bcrypt

# here url database
engine=sqlalchemy.create_engine(settings.db_url_sqlite)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def hash_password(text):
  return bcrypt.hashpw(text, bcrypt.gensalt())

password = hash_password(b'qwerty')

db.add(
  User(
    username="sergio.cardenas",
    password_hash=password,
    role=UserType.ADMIN
  )
)

db.add(
  User(
    username="miriam.lucana",
    password_hash=password,
    role=UserType.ADMIN
  )
)

db.add(
  User(
    username="reynaldo.perez",
    password_hash=password,
    role=UserType.ADMIN
  )
)
db.commit()