from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_api_id: int
    telegram_api_hash: str
    telegram_bot_token: str

    database_path: str = "./data/transfers.db"

    chunk_size_bytes: int = 8_388_608        # 8MB
    max_retry_attempts: int = 3
    concurrent_worker_limit: int = 3
    max_file_size_bytes: int = 4_294_967_296  # 2GB

    encryption_key: str

    log_level: str = "INFO"
    app_env: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
