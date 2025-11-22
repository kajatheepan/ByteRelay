import asyncio

from telegram_client import client
from core.config import settings
from core.db import get_session
from core.models import Transfer
from core.retry import run_with_retry
from onboarding import get_credential

transfer_semaphore = asyncio.Semaphore(settings.concurrent_worker_limit)


async def dispatch_transfer(transfer_id: int):
    """Runs one transfer under the concurrency limit, using the real Telegram/Nextcloud adapters."""
    async with transfer_semaphore:
        with get_session() as session:
            transfer = session.get(Transfer, transfer_id)
            credential = get_credential(session, transfer.user_id)

            from adapters.telegram_source import TelegramSource
            from adapters.nextcloud_destination import NextcloudDestination

            message = await client.get_messages(transfer.telegram_chat_id, ids=transfer.telegram_message_id)
            source_factory = lambda: TelegramSource(client, message, settings.chunk_size_bytes)
            destination_factory = lambda: NextcloudDestination(credential, transfer.original_filename)

            async def on_progress(percent):
                await client.edit_message(transfer.telegram_chat_id, transfer.telegram_message_id,
                                           f"Uploading... {percent}%")

            await run_with_retry(session, transfer, source_factory, destination_factory, on_progress=on_progress)
