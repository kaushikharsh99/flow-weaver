from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./flow_weaver.db"
    SECRET_KEY: str = "super_secret_flow_weaver_key_change_me_in_production"
    
    class Config:
        env_file = ".env"

settings = Settings()
