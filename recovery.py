from core.db import get_session
from core.enums import TransferState
from core.models import Transfer
from core.state_machine import transition


async def recover_stuck_transfers():
    """Marks any transfer left mid-flight by a previous crash as FAILED."""
    with get_session() as session:
        stuck = session.query(Transfer).filter(
            Transfer.state.in_([
                TransferState.DOWNLOADING.value,
                TransferState.UPLOADING.value,
                TransferState.RETRYING.value,
            ])
        ).all()
        for t in stuck:
            t.failure_reason = "Interrupted by process restart"
            transition(session, t, TransferState.FAILED, note="stuck on startup, marked failed")
