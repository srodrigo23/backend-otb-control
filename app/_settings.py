from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
  db_url_supabase:str
  db_url_sqlite:str
  prod:bool
  client_url_prod:str
  client_url_dev:str
  
  SECRET_KEY: str
  ALGORITHM: str
  ACCESS_TOKEN_EXPIRE_MINUTES: int
  
  model_config = SettingsConfigDict(env_file='.env')

settings = Settings()