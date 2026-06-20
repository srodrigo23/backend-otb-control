from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  SECRET_KEY:str
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
  ALGORITHM:str
  
  DB_URL_SUPABASE:str
  DB_URL_SQLITE:str
  ENVIRONMENT: str = "DEVELOPMENT"
  
  PORT:int
  CLIENT_URL_PROD:str
  CLIENT_URL_DEV:str
  
  @property
  def cookie_secure(self) -> bool:
    return self.ENVIRONMENT == "PRODUCTION"

  @property
  def cookie_samesite(self) -> str:
    # En producción el frontend usa Vercel proxy (/api/* → Render), 
    # así que la cookie es first-party y SameSite=Lax funciona.
    # SameSite=Lax evita que Safari iOS bloquee la cookie (ITP).
    return "lax"
  
  model_config = {"env_file": ".env"}
  
settings = Settings()