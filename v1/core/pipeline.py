import time

from adapters.base import Source, Destination
from core.config import settings
from core.db import utc_now_iso
from core.enums import TransferState
from core.models import ChunkRecord
from core.state_machine import transition


# Moves one transfer from Source to Destination, chunk by chunk, updating
# state and chunk records as it goes. Exceptions from the destination are
# not caught here — core/retry.py wraps this and decides retry vs fail.
async def run_transfer(session, transfer, source: Source, destination: Destination,
                        on_progress=None):
    transition(session, transfer, TransferState.DOWNLOADING)
    metadata = await source.get_metadata()

    session_id = await destination.start(metadata["filename"], metadata["size_bytes"])
    transfer.upload_session_id = session_id
    session.commit()

    transition(session, transfer, TransferState.UPLOADING)

    chunk_number = 1
    bytes_uploaded = 0
    last_reported_at = 0.0  # local var, not a model attribute — only matters within this run

    async for chunk_bytes in source.stream():
        record = ChunkRecord(
            transfer_id=transfer.id,
            upload_session_id=session_id,
            chunk_number=chunk_number,
            chunk_size_bytes=len(chunk_bytes),
            status="pending",
        )
        session.add(record)
        session.commit()

        await destination.upload_chunk(chunk_bytes, chunk_number)

        record.status = "uploaded"
        record.uploaded_at = utc_now_iso()
        session.commit()

        bytes_uploaded += len(chunk_bytes)

        # only fire on_progress once per min_progress_interval_seconds
        now = time.monotonic()
        if on_progress and (now - last_reported_at) >= settings.min_progress_interval_seconds:
            percent = int((bytes_uploaded / metadata["size_bytes"]) * 100)
            await on_progress(percent)
            last_reported_at = now

        chunk_number += 1

    final_name = await destination.finish()
    transfer.final_filename = final_name

    if on_progress:
        await on_progress(100)  # guarantee a final 100% update even if throttled out

    transition(session, transfer, TransferState.COMPLETED)
