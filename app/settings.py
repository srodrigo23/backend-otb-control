from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings (BaseSettings):
  db_url_supabase:str
  db_url_sqlite:str
  # frontend_url:str
  prod:bool
  model_config = SettingsConfigDict(env_file='.env')


settings = Settings()