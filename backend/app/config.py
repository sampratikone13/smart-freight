import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Freight Analytics & Shipping Time Prediction System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # PostgreSQL Configuration
    DB_USER: str = os.getenv("DB_USER", "samprati")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "supply_chain_dw")
    
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_PASSWORD:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
