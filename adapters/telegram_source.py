from adapters.base import Source


# Real Source implementation: streams a file's bytes directly from Telegram.
class TelegramSource(Source):
    def __init__(self, client, message, chunk_size: int):
        """message is a live Telethon message object holding the file's media."""
        self._client = client
        self._message = message
        self._chunk_size = chunk_size

    async def get_metadata(self):
        """Returns the file's name and size as reported by Telegram."""
        return {"filename": self._message.file.name, "size_bytes": self._message.file.size}

    async def stream(self):
        """Yields the file's bytes in chunks, without buffering the whole file in memory."""
        async for chunk in self._client.iter_download(
            self._message.media, chunk_size=self._chunk_size, request_size=self._chunk_size
        ):
            yield chunk
