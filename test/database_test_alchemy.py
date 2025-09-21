from sqlalchemy.orm import sessionmaker
import sqlalchemy
from models import User, Item
from faker import Faker

engine=sqlalchemy.create_engine(
  # f'sqlite:///db_test.db'
  # f"postgresql://postgres:otbcentralizadoqwerty@db.vnuioejzhnwuokpzwnqn.supabase.co:5432/postgres"
  f"postgresql://postgres.vnuioejzhnwuokpzwnqn:otbcentralizadoqwerty@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()


fake = Faker(['en_US'])
for _ in range(1000):
  name = fake.name().split(' ')
  print(name)
  db_user = User(
    first_name = name[0],
    second_name = "rodrigo",
    last_name = name[1],
    
    ci="5540408-PT",
    phone_number="+5917741858",
    email = f"{name[0].lower()}{name[1].lower()}@gmail.com",


    # username = f"{name[0].lower()}.{name[1].lower()}",
    # hashed_password = "password"  
  )

  
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  
  db_item = Item(
    title="item1",
    description="this is a description",
    owner_id=db_user.id
  )

  db.add(db_item)
  db.commit()
  db.refresh(db_item)