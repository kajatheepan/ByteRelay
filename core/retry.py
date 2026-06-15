import asyncio

from core.config import settings
from core.enums import TransferState
from core.pipeline import run_transfer
from core.state_machine import transition

RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError)


class NonRetryableError(Exception):
    def __init__(self, reason: str):
        self.reason = reason


class InsufficientStorageError(NonRetryableError):
    pass


class AuthenticationError(NonRetryableError):
    pass


# Gets a fresh Destination instance each attempt.
async def run_with_retry(session, transfer, source_factory, destination_factory, on_progress=None):
    for attempt in range(1, settings.max_retry_attempts + 1):
        destination = destination_factory()
        try:
            await run_transfer(session, transfer, source_factory(), destination, on_progress=on_progress)
            return
        except NonRetryableError as e:
            transfer.failure_reason = e.reason
            await destination.abort()
            transition(session, transfer, TransferState.FAILED, note=e.reason)
            return
        except RETRYABLE_EXCEPTIONS as e:
            await destination.abort()
            transfer.retry_count = attempt
            if attempt == settings.max_retry_attempts:
                transfer.failure_reason = f"Failed after {attempt} attempts: {e}"
                transition(session, transfer, TransferState.FAILED, note=str(e))
                return
            transition(session, transfer, TransferState.RETRYING, note=f"attempt {attempt} failed: {e}")
            await asyncio.sleep(2 ** attempt)
