import asyncio

from telethon import events

from telegram_client import client
from core.config import settings
from core.db import get_session, utc_now_iso
from core.enums import TransferState
from core.models import Transfer
from dispatcher import dispatch_transfer
from onboarding import PENDING_CONFIRMATIONS, handle_incoming_file


@client.on(events.NewMessage(pattern="/start"))
async def on_start(event):
    """Replies with a short intro, mainly used to confirm the bot is running."""
    await event.respond(
        "👋 Send me a file and I'll upload it to your Nextcloud.\n"
        "First time? I'll ask for your Nextcloud server URL, username, and password."
    )


@client.on(events.NewMessage(func=lambda e: e.file is not None))
async def on_file(event):
    """Entry point for any message containing a file; rejects oversized files, then hands off."""
    user_id = event.sender_id
    file_id = event.file.id
    filename = event.file.name or "unnamed_file"
    size = event.file.size
    chat_id = event.chat_id

    if size > settings.max_file_size_bytes:
        limit_gb = settings.max_file_size_bytes / 1_073_741_824
        await event.respond(f"⚠️ This file is too large. Current limit is {limit_gb:.1f}GB.")
        return

    await handle_incoming_file(user_id, chat_id, event.message.id, file_id, filename, size, event)


@client.on(events.CallbackQuery())
async def on_callback(event):
    """Handles a Confirm/Cancel tap: creates the Transfer row on confirm, discards on cancel."""
    action, interaction_key = event.data.decode().split(":", 1)
    pending = PENDING_CONFIRMATIONS.get(interaction_key)
    if pending is None:
        await event.answer("Session expired, please resend the file.", alert=True)
        return

    if pending["user_id"] != event.sender_id:
        await event.answer("This isn't your transfer.", alert=True)
        return

    if action == "cancel":
        await event.edit("Discarded.")
        del PENDING_CONFIRMATIONS[interaction_key]
        return

    with get_session() as session:
        transfer = Transfer(
            user_id=pending["user_id"], telegram_file_id=pending["telegram_file_id"],
            telegram_chat_id=pending["chat_id"], telegram_message_id=pending["confirm_message_id"],
            source_message_id=pending["source_message_id"],
            original_filename=pending["filename"], file_size_bytes=pending["size"],
            state=TransferState.QUEUED.value,
            created_at=utc_now_iso(), updated_at=utc_now_iso(),
        )
        session.add(transfer)
        session.commit()
        transfer_id = transfer.id

    del PENDING_CONFIRMATIONS[interaction_key]

    await event.edit("Queued...")
    asyncio.create_task(dispatch_transfer(transfer_id))
