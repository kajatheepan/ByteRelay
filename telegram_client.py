from telethon import TelegramClient

from core.config import settings

client = TelegramClient("bot_session", settings.telegram_api_id, settings.telegram_api_hash)
