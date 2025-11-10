
from core.enums import TransferState as S
from v1.core.models import TransferHistory
from datetime import datetime, timezone



LEGAL_TRANSITIONS = {
    S.QUEUED:      {S.DOWNLOADING, S.CANCELLED},
    S.DOWNLOADING: {S.UPLOADING, S.RETRYING, S.FAILED},
    S.UPLOADING:   {S.COMPLETED, S.RETRYING, S.FAILED},
    S.RETRYING:    {S.DOWNLOADING, S.UPLOADING, S.FAILED},
    S.COMPLETED:   set(),
    S.FAILED:      set(),
    S.CANCELLED:   set(),
}

class IllegalTransitionError(Exception):
    pass

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def transition(session, transfer, new_state: S, note: str | None = None):
    current = S(transfer.state)
    if new_state not in LEGAL_TRANSITIONS[current]:
        raise IllegalTransitionError(f"Cannot go from {current} to {new_state}")
    old_state = transfer.state
    transfer.state = new_state.value
    transfer.updated_at = utc_now_iso()

    session.add(TransferHistory(
        transfer_id=transfer.id,
        from_state=old_state,
        to_state=new_state.value,
        timestamp=utc_now_iso(),
        note=note,
    ))

    session.commit()

    logger.info("state_transition", extra={
        "transfer_id": transfer.id,
        "from_state": old_state,
        "to_state": new_state.value,
        "note": note,
    })
    