from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    database_url:str
    class Config:
        env_file = ".env"


settings = AppSettings()
