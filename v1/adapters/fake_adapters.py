import uuid

from adapters.base import Source, Destination


# In-memory Source for tests — no real Telegram calls.
class FakeSource(Source):
    def __init__(self, data: bytes, filename="test.bin"):
        self._data = data
        self._filename = filename

    async def get_metadata(self):
        return {"filename": self._filename, "size_bytes": len(self._data)}

    async def stream(self):
        chunk_size = 1024
        for i in range(0, len(self._data), chunk_size):
            yield self._data[i:i + chunk_size]


# In-memory Destination for tests — no real Nextcloud calls.
# fail_on_chunk lets a test simulate a network drop at a specific chunk.
class FakeDestination(Destination):
    def __init__(self, fail_on_chunk: int | None = None):
        self.chunks = {}
        self.aborted = False
        self.finished = False
        self._fail_on_chunk = fail_on_chunk

    async def start(self, file_name, total_size):
        self.session_id = str(uuid.uuid4())
        return self.session_id

    async def upload_chunk(self, chunk_bytes, chunk_number):
        if self._fail_on_chunk == chunk_number:
            raise ConnectionError("simulated network drop")
        self.chunks[chunk_number] = chunk_bytes

    async def finish(self):
        self.finished = True
        return "final_test.bin"

    async def abort(self):
        self.aborted = True
