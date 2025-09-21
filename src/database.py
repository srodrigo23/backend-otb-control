from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./db_test.db"
# SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:otbcentralizadoqwerty@db.vnuioejzhnwuokpzwnqn.supabase.co:5432/postgres"
# SQLALCHEMY_DATABASE_URL = f"postgresql://postgres.vnuioejzhnwuokpzwnqn:otbcentralizadoqwerty@aws-0-us-east-2.pooler.supabase.com:5432/postgres"


engine = create_engine(
  SQLALCHEMY_DATABASE_URL, 
  # connect_args={"check_same_thread": True} # only for sqlite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
