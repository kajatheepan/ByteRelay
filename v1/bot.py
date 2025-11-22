import asyncio 

from telethon import TelegramClient

from core.config import settings
from core.logging_setup import setup_logging


client = TelegramClient("bot_session", settings.telegram_api_id, settings.telegram_api_hash)

import bot_logic  # noqa: E402 — registers event handlers on client, must import after client exists


async def main():
    setup_logging()
    await client.start(bot_token=settings.telegram_bot_token)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())