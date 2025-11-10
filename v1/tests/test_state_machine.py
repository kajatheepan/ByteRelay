import time

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.models import Base, Transfer, TransferHistory
from core.enums import TransferState as S
from core.state_machine import transition, LEGAL_TRANSITIONS, IllegalTransitionError
from core.db import utc_now_iso


# Fresh in-memory DB per test, never touches the real transfers.db
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


# Helper to create a Transfer already sitting in a given state, so each
# test can start from whatever state it needs to check.
def make_transfer(session, state: S):
    t = Transfer(
        user_id=1,
        telegram_file_id="file123",
        telegram_chat_id=1,
        original_filename="test.txt",
        file_size_bytes=100,
        state=state.value,
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
    )
    session.add(t)
    session.commit()
    return t


# Auto-generates one test case per entry in LEGAL_TRANSITIONS, so adding a
# new legal transition later gets covered here automatically.
@pytest.mark.parametrize(
    "from_state, to_state",
    [
        (from_state, to_state)
        for from_state, targets in LEGAL_TRANSITIONS.items()
        for to_state in targets
    ],
)
def test_legal_transition_succeeds_and_logs_history(session, from_state, to_state):
    transfer = make_transfer(session, from_state)

    transition(session, transfer, to_state)

    assert transfer.state == to_state.value

    history_rows = (
        session.query(TransferHistory)
        .filter_by(transfer_id=transfer.id)
        .all()
    )
    assert len(history_rows) == 1
    assert history_rows[0].from_state == from_state.value
    assert history_rows[0].to_state == to_state.value


# Terminal states (COMPLETED/FAILED/CANCELLED) must never allow a transition out
@pytest.mark.parametrize(
    "from_state, to_state",
    [
        (S.COMPLETED, S.DOWNLOADING),
        (S.FAILED, S.UPLOADING),
        (S.CANCELLED, S.QUEUED),
    ],
)
def test_illegal_transition_raises(session, from_state, to_state):
    transfer = make_transfer(session, from_state)

    with pytest.raises(IllegalTransitionError):
        transition(session, transfer, to_state)


def test_updated_at_changes_after_transition(session):
    transfer = make_transfer(session, S.QUEUED)
    original_updated_at = transfer.updated_at

    time.sleep(1)  # utc_now_iso() has 1-second resolution
    transition(session, transfer, S.DOWNLOADING)

    assert transfer.updated_at != original_updated_at
