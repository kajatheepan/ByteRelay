import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from adapters.fake_adapters import FakeSource, FakeDestination
from core.db import utc_now_iso
from core.enums import TransferState as S
from core.models import Base, Transfer, ChunkRecord
from core.retry import run_with_retry, NonRetryableError


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


def make_transfer(session):
    t = Transfer(
        user_id=1,
        telegram_file_id="file123",
        telegram_chat_id=1,
        original_filename="test.txt",
        file_size_bytes=5000,
        state=S.QUEUED.value,
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
    )
    session.add(t)
    session.commit()
    return t


def chunk_records(session, transfer_id):
    return session.query(ChunkRecord).filter_by(transfer_id=transfer_id).all()


@pytest.mark.asyncio
async def test_success_completes_with_all_chunks_uploaded(session):
    transfer = make_transfer(session)
    destination = FakeDestination()

    await run_with_retry(
        session, transfer,
        source_factory=lambda: FakeSource(b"x" * 5000),
        destination_factory=lambda: destination,
    )

    assert transfer.state == S.COMPLETED.value
    records = chunk_records(session, transfer.id)
    assert len(records) > 0
    assert all(r.status == "uploaded" for r in records)


@pytest.mark.asyncio
async def test_fails_once_then_succeeds_on_retry(session):
    transfer = make_transfer(session)

    # First destination fails on chunk 3, second succeeds — matches run_with_retry
    # calling destination_factory() fresh on each attempt.
    destinations = [FakeDestination(fail_on_chunk=3), FakeDestination()]

    def destination_factory():
        return destinations.pop(0)

    await run_with_retry(
        session, transfer,
        source_factory=lambda: FakeSource(b"x" * 5000),
        destination_factory=destination_factory,
    )

    assert transfer.state == S.COMPLETED.value
    assert transfer.retry_count == 1

    session_ids = {r.upload_session_id for r in chunk_records(session, transfer.id)}
    assert len(session_ids) == 2


@pytest.mark.asyncio
async def test_non_retryable_error_fails_immediately(session):
    transfer = make_transfer(session)

    class FailingDestination(FakeDestination):
        async def start(self, file_name, total_size):
            raise NonRetryableError("bad credentials")

    destination = FailingDestination()

    await run_with_retry(
        session, transfer,
        source_factory=lambda: FakeSource(b"x" * 5000),
        destination_factory=lambda: destination,
    )

    assert transfer.state == S.FAILED.value
    assert transfer.retry_count == 0
    assert destination.aborted is True


@pytest.mark.asyncio
async def test_exhausts_all_retries_then_fails(session):
    transfer = make_transfer(session)
    destinations_created = []

    def destination_factory():
        d = FakeDestination(fail_on_chunk=1)
        destinations_created.append(d)
        return d

    await run_with_retry(
        session, transfer,
        source_factory=lambda: FakeSource(b"x" * 5000),
        destination_factory=destination_factory,
    )

    assert transfer.state == S.FAILED.value
    assert transfer.retry_count == 3
    assert len(destinations_created) == 3
    assert all(d.aborted for d in destinations_created)
