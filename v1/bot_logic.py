from telethon import events

from bot import client
from core.config import settings


@client.on(events.NewMessage(func=lambda e: e.file is not None))
async def on_file(event):
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
