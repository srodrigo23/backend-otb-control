from sqlalchemy.orm import sessionmaker
import sqlalchemy
from src.models import User
from faker import Faker

engine=sqlalchemy.create_engine(f'sqlite:///database1.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()


fake = Faker(['en_US'])
for _ in range(1000):
  name = fake.name().split(' ')
  
  db_user = User(
    first_name = name[0],
    # second_name = "rodrigo",
    last_name = name[1],
    email = f"{name[0].lower()}{name[1].lower()}@gmail.com",
    username = f"{name[0].lower()}.{name[1].lower()}",
    hashed_password = "password"  
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)