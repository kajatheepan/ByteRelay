import logging

from core.enums import TransferState as S
from core.models import TransferHistory
from core.db import utc_now_iso

logger = logging.getLogger(__name__)


# Map of current state -> set of states it's legally allowed to move to.
# COMPLETED / FAILED / CANCELLED map to an empty set because they're terminal
# (a finished transfer can never change state again).
LEGAL_TRANSITIONS = {
    S.QUEUED:      {S.DOWNLOADING, S.CANCELLED},
    S.DOWNLOADING: {S.UPLOADING, S.RETRYING, S.FAILED},
    S.UPLOADING:   {S.COMPLETED, S.RETRYING, S.FAILED},
    S.RETRYING:    {S.DOWNLOADING, S.UPLOADING, S.FAILED},
    S.COMPLETED:   set(),
    S.FAILED:      set(),
    S.CANCELLED:   set(),
}


# Raised when code tries to move a transfer to a state it isn't allowed to
# reach from its current state.
class IllegalTransitionError(Exception):
    pass


# The only function allowed to change a transfer's state. Validates the
# move is legal, updates the Transfer row, and writes a permanent
# TransferHistory record of the change.
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
