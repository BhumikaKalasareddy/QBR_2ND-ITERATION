import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "QBR Telemetry API"
    GCP_PROJECT_ID: str = "svc-edp-reporting-prod"

    class Config:
        env_file = ".env"
        extra = "ignore"

# Instantiate settings instance so other modules can import it
settings = Settings()