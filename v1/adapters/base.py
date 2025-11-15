from abc import ABC, abstractmethod
from typing import AsyncIterator


class Source(ABC):
    @abstractmethod
    async def get_metadata(self) -> dict:
        """Returns {'filename': str, 'size_bytes': int}"""

    @abstractmethod
    def stream(self) -> AsyncIterator[bytes]:
        """Yields raw byte chunks in order."""


class Destination(ABC):
    @abstractmethod
    async def start(self, file_name: str, total_size: int) -> str:
        """Begins an upload session, returns a fresh upload_session_id."""

    @abstractmethod
    async def upload_chunk(self, chunk_bytes: bytes, chunk_number: int) -> None:
        ...

    @abstractmethod
    async def finish(self) -> str:
        """Assembles the file, returns the final filename actually used."""

    @abstractmethod
    async def abort(self) -> None:
        """Cleans up a failed/incomplete upload session."""