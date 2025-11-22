import logging
import uuid

from telethon import Button

from telegram_client import client
from core.credentials import encrypt_password
from core.db import get_session, utc_now_iso
from core.models import NextcloudCredential

logger = logging.getLogger(__name__)

# Files awaiting setup, keyed by user_id. Not persisted to the database.
PENDING_FILES = {}

# Files awaiting a Confirm/Cancel tap, keyed by a unique interaction_key.
PENDING_CONFIRMATIONS = {}


def get_credential(session, user_id: int) -> NextcloudCredential | None:
    """Look up a user's saved Nextcloud credential, if any."""
    return session.query(NextcloudCredential).filter_by(user_id=user_id).first()


async def handle_incoming_file(user_id, chat_id, message_id, file_id, filename, size, event):
    """Route an incoming file to setup (if no saved credential) or straight to the confirm button."""
    with get_session() as session:
        credential = get_credential(session, user_id)

    if credential is None:
        PENDING_FILES[user_id] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "file_id": file_id,
            "filename": filename,
            "size": size,
            "event": event,
        }
        await run_setup(event, user_id)
        return

    await send_confirm_button(event, filename, size)


async def run_setup(event, user_id):
    """Ask the user for Nextcloud server URL, username, and password, then save the credential."""
    async with client.conversation(event.chat_id, timeout=300) as conv:
        await conv.send_message(
            "Let's connect your Nextcloud account.\n"
            "I'll store your server URL, username, and password (encrypted) so I can upload files for you.\n\n"
            "Step 1/3 — Send your Nextcloud server URL (e.g. https://dms.uom.lk):"
        )
        server_url = (await conv.get_response()).raw_text.strip()
        if not server_url.startswith("https://"):
            await conv.send_message("URL must start with https://. Please send it again.")
            server_url = (await conv.get_response()).raw_text.strip()

        await conv.send_message("Step 2/3 — Send your Nextcloud username:")
        username = (await conv.get_response()).raw_text.strip()

        await conv.send_message("Step 3/3 — Send your Nextcloud password:")
        password_msg = await conv.get_response()
        password = password_msg.raw_text.strip()

        try:
            await client.delete_messages(event.chat_id, [password_msg.id])
        except Exception as e:
            logger.warning("password_message_delete_failed", extra={"note": str(e)})

    with get_session() as session:
        cred = NextcloudCredential(
            user_id=user_id, server_url=server_url, username=username,
            encrypted_password=encrypt_password(password),
            created_at=utc_now_iso(), updated_at=utc_now_iso(),
        )
        session.add(cred)
        session.commit()

    await client.send_message(
        event.chat_id,
        "✅ Nextcloud account connected. Your password message has been deleted from this chat.",
    )

    pending = PENDING_FILES.pop(user_id, None)
    if pending:
        await send_confirm_button(pending["event"], pending["filename"], pending["size"])


async def send_confirm_button(event, filename, size):
    """Show the file's Confirm/Cancel buttons and register it in PENDING_CONFIRMATIONS."""
    interaction_key = f"{event.sender_id}:{uuid.uuid4().hex}"
    msg = await event.respond(
        f"📄 {filename} ({size / 1_048_576:.1f} MB)\nUpload to Nextcloud?",
        buttons=[[Button.inline("✅ Confirm", data=f"confirm:{interaction_key}"),
                  Button.inline("❌ Cancel", data=f"cancel:{interaction_key}")]],
    )
    PENDING_CONFIRMATIONS[interaction_key] = {
        "user_id": event.sender_id,
        "chat_id": event.chat_id,
        "telegram_file_id": event.file.id,
        "filename": filename,
        "size": size,
        "confirm_message_id": msg.id,
    }
