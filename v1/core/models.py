from sqlalchemy import (Column, Integer, Text, ForeignKey,
                         CheckConstraint, UniqueConstraint, Index)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

VALID_STATES = "('queued','downloading','uploading','retrying','completed','failed','cancelled')"


class Transfer(Base):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    telegram_file_id = Column(Text, nullable=False)
    telegram_chat_id = Column(Integer, nullable=False)
    telegram_message_id = Column(Integer)
    original_filename = Column(Text, nullable=False)
    final_filename = Column(Text)
    file_size_bytes = Column(Integer, nullable=False)
    total_chunks = Column(Integer)
    state = Column(Text, nullable=False)
    upload_session_id = Column(Text)
    retry_count = Column(Integer, nullable=False, default=0)
    failure_reason = Column(Text)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(f"state IN {VALID_STATES}"),
        Index("idx_transfer_state", "state"),
        Index("idx_transfer_user", "user_id"),
    )


class TransferHistory(Base):
    __tablename__ = "transfer_history"
    id = Column(Integer, primary_key=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id", ondelete="CASCADE"), nullable=False)
    from_state = Column(Text)
    to_state = Column(Text, nullable=False)
    timestamp = Column(Text, nullable=False)
    note = Column(Text)

    __table_args__ = (
        CheckConstraint(f"to_state IN {VALID_STATES}"),
        Index("idx_history_transfer", "transfer_id"),
    )


class ChunkRecord(Base):
    __tablename__ = "chunk_record"
    id = Column(Integer, primary_key=True)
    transfer_id = Column(Integer, ForeignKey("transfer.id", ondelete="CASCADE"), nullable=False)
    upload_session_id = Column(Text, nullable=False)
    chunk_number = Column(Integer, nullable=False)
    chunk_size_bytes = Column(Integer, nullable=False)
    status = Column(Text, nullable=False)
    uploaded_at = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('pending','uploaded','failed')"),
        UniqueConstraint("upload_session_id", "chunk_number"),
        Index("idx_chunk_transfer", "transfer_id"),
    )


class NextcloudCredential(Base):
    __tablename__ = "nextcloud_credential"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    server_url = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    encrypted_password = Column(Text, nullable=False)
    key_version = Column(Integer, nullable=False, default=1)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "server_url"),
        Index("idx_credential_user", "user_id"),
    )