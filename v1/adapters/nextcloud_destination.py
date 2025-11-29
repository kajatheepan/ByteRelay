import logging
import math
import random
from datetime import datetime, timezone

import httpx
from core.config import settings

from adapters.base import Destination
from core.credentials import decrypt_password
from core.retry import AuthenticationError, InsufficientStorageError, NonRetryableError

logger = logging.getLogger(__name__)


# Real Destination implementation: uploads a file to Nextcloud using the
# legacy WebDAV chunking convention (OC-Chunked header + filename suffix
# "-chunking-{transferid}-{totalchunks}-{chunkindex}").
class NextcloudDestination(Destination):
    def __init__(self, credential, original_filename: str):
        """credential holds one user's saved Nextcloud server URL and encrypted password."""
        self._base = credential.server_url.rstrip("/")
        self._username = credential.username
        self._auth = (credential.username, decrypt_password(credential.encrypted_password))
        self._original_filename = original_filename
        self._final_name = None
        self._transfer_id = None
        self._total_chunks = None
        self._client = httpx.AsyncClient(auth=self._auth, timeout=httpx.Timeout(60.0))  # server is slow; default 5s times out mid-chunk

    async def start(self, file_name, total_size):
        """Picks the final filename (renaming on conflict) and computes the chunk count."""
        self._final_name = await self._resolve_filename(self._original_filename)
        self._transfer_id = str(random.randint(10**9, 10**10 - 1))  # must be numeric — server 502s on hex/uuid ids
        self._total_chunks = max(1, math.ceil(total_size / settings.chunk_size_bytes))
        logger.info("nextcloud_upload_start", extra={
            "note": f"{self._final_name} ({self._total_chunks} chunks, transfer_id={self._transfer_id})",
        })
        return self._transfer_id

    async def _resolve_filename(self, name):
        """Returns name unchanged if free, otherwise appends a UTC timestamp to avoid overwriting."""
        check_url = f"{self._base}/remote.php/webdav/{name}"
        resp = await self._client.request("PROPFIND", check_url, headers={"Depth": "0"})
        if resp.status_code == 404:
            return name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem, ext = name.rsplit(".", 1) if "." in name else (name, "")
        return f"{stem}_{timestamp}.{ext}" if ext else f"{stem}_{timestamp}"

    async def upload_chunk(self, chunk_bytes, chunk_number):
        """PUTs one chunk using the legacy chunking filename convention."""
        chunk_index = chunk_number - 1
        url = (
            f"{self._base}/remote.php/webdav/"
            f"{self._final_name}-chunking-{self._transfer_id}-{self._total_chunks}-{chunk_index}"
        )
        # chunk_bytes may be a memoryview (e.g. from Telethon) — httpx needs real bytes or raises a confusing error
        try:
            resp = await self._client.put(url, content=bytes(chunk_bytes), headers={"OC-Chunked": "1"})
        except httpx.TimeoutException as e:
            logger.warning("nextcloud_chunk_timeout", extra={"note": f"chunk {chunk_number}/{self._total_chunks}"})
            raise ConnectionError(f"Nextcloud request timed out: {e}")  # let retry.py retry instead of hard-failing
        logger.info("nextcloud_chunk_uploaded", extra={
            "note": f"chunk {chunk_number}/{self._total_chunks}, status={resp.status_code}",
        })
        self._raise_for_status(resp)

    async def finish(self):
        """The server assembles the file automatically after the last chunk lands."""
        check_url = f"{self._base}/remote.php/webdav/{self._final_name}"
        resp = await self._client.request("PROPFIND", check_url, headers={"Depth": "0"})
        if resp.status_code == 404:
            logger.error("nextcloud_upload_incomplete", extra={"note": self._final_name})
            raise NonRetryableError("Upload did not complete: assembled file not found")
        logger.info("nextcloud_upload_finished", extra={"note": self._final_name})
        await self._client.aclose()
        return self._final_name

    async def abort(self):
        """No server-side cleanup needed: incomplete chunk sets are never assembled."""
        logger.warning("nextcloud_upload_aborted", extra={"note": self._final_name})
        await self._client.aclose()

    def _raise_for_status(self, resp):
        """Maps Nextcloud's HTTP status codes to the exception types core/retry.py classifies."""
        if resp.status_code == 507:
            raise InsufficientStorageError("Nextcloud storage is full")
        if resp.status_code in (401, 403):
            raise AuthenticationError("Your saved Nextcloud credentials look incorrect — please redo setup")
        if resp.status_code >= 500:
            raise ConnectionError(f"Nextcloud server error: {resp.status_code}")
        if resp.status_code >= 400:
            raise NonRetryableError(f"Unexpected error: {resp.status_code}")
