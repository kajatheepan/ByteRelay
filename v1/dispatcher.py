import asyncio
import logging

from telethon.errors.rpcerrorlist import MessageNotModifiedError

from telegram_client import client
from core.config import settings
from core.db import get_session
from core.models import Transfer
from core.retry import run_with_retry
from onboarding import get_credential

logger = logging.getLogger(__name__)

transfer_semaphore = asyncio.Semaphore(settings.concurrent_worker_limit)


async def dispatch_transfer(transfer_id: int):
    """Runs one transfer under the concurrency limit, using the real Telegram/Nextcloud adapters."""
    # this runs via asyncio.create_task(), so without this try/except any error here
    # is silently swallowed by asyncio ("Task exception was never retrieved")
    try:
        async with transfer_semaphore:
            with get_session() as session:
                transfer = session.get(Transfer, transfer_id)
                credential = get_credential(session, transfer.user_id)
                logger.info("dispatch_transfer_start", extra={
                    "transfer_id": transfer_id, "note": transfer.original_filename,
                })

                from adapters.telegram_source import TelegramSource
                from adapters.nextcloud_destination import NextcloudDestination

                message = await client.get_messages(transfer.telegram_chat_id, ids=transfer.source_message_id)
                source_factory = lambda: TelegramSource(client, message, settings.chunk_size_bytes)
                destination_factory = lambda: NextcloudDestination(credential, transfer.original_filename)

                async def on_progress(percent):
                    logger.info("dispatch_transfer_progress", extra={
                        "transfer_id": transfer_id, "note": f"{percent}%",
                    })
                    try:
                        await client.edit_message(transfer.telegram_chat_id, transfer.telegram_message_id,
                                                   f"Uploading... {percent}%")
                    except MessageNotModifiedError:
                        pass  # Telegram errors if the edit text equals the current text — harmless here

                await run_with_retry(session, transfer, source_factory, destination_factory, on_progress=on_progress)
                logger.info("dispatch_transfer_done", extra={"transfer_id": transfer_id, "note": transfer.state})
    except Exception as e:
        logger.error("dispatch_transfer_failed", extra={"transfer_id": transfer_id, "error": str(e)})
