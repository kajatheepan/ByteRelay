# All app config lives here. Every other file must import `settings` from
# this module instead of reading os.environ or .env directly.
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
    min_progress_interval_seconds: float = 3.0  # throttles progress updates, avoids Telegram rate limits

    encryption_key: str  # Fernet key used to encrypt saved Nextcloud passwords

    log_level: str = "INFO"
    app_env: str = "development"

    class Config:
        env_file = ".env"


# Created once at import time; raises if a required field is missing from .env.
settings = Settings()
