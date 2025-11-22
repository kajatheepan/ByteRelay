import asyncio

from core.config import settings
from core.logging_setup import setup_logging
from telegram_client import client

import bot_logic  # noqa: E402 — registers event handlers on client


async def main():
    setup_logging()
    await client.start(bot_token=settings.telegram_bot_token)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())