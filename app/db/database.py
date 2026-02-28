from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..settings import settings

DATABASE_URL = settings.db_url_supabase if settings.prod else settings.db_url_sqlite 

engine = create_engine(
  DATABASE_URL,  
  # connect_args={"check_same_thread": True} # only for sqlite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
