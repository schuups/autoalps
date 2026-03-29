from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cache_path: str = "./_cache"
    epochs: int = 50
    batch_size: int = 16

    class Config:
        env_file = ".env"


settings = Settings()
