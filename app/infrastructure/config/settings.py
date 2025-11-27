from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "PukPuk Backend"
    debug: bool = False
    database_url: str = "mongodb://localhost:27017"
    database_name: str = "pukpuk_db"

    class Config:
        env_file = ".env"

settings = Settings()