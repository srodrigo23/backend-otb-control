from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
  db_url_supabase:str
  db_url_sqlite:str
  prod:bool
  client_url_prod:str
  client_url_dev:str
  
  model_config = SettingsConfigDict(env_file='.env')

settings = Settings()