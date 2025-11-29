import uuid
from datetime import datetime, timezone

import httpx

from adapters.base import Destination
from core.credentials import decrypt_password
from core.retry import AuthenticationError, InsufficientStorageError, NonRetryableError

# Real Destination implementation: uploads a file to a user's Nextcloud via
# its chunked upload WebDAV API (MKCOL -> PUT chunks -> MOVE).
class NextcloudDestination(Destination):
    def __init__(self, credential, original_filename: str):
        """credential holds one user's saved Nextcloud server URL and encrypted password."""
        self._base = credential.server_url.rstrip("/")
        self._username = credential.username
        self._auth = (credential.username, decrypt_password(credential.encrypted_password))
        self._original_filename = original_filename
        self._session_id = None
        self._total_size = None
        self._client = httpx.AsyncClient(auth=self._auth)  # reused across all calls in this upload

    async def start(self, file_name, total_size):
        """Creates a new upload session folder on the server via MKCOL."""
        self._session_id = str(uuid.uuid4())
        self._total_size = total_size
        url = f"{self._base}/remote.php/dav/uploads/{self._username}/{self._session_id}"
        resp = await self._client.request("MKCOL", url)
        self._raise_for_status(resp)
        return self._session_id

    async def upload_chunk(self, chunk_bytes, chunk_number):
        """PUTs one chunk into the upload session, named with a zero-padded chunk number."""
        url = f"{self._base}/remote.php/dav/uploads/{self._username}/{self._session_id}/{chunk_number:05d}"
        resp = await self._client.put(url, content=chunk_bytes)
        self._raise_for_status(resp)

    async def finish(self):
        """Assembles the uploaded chunks into the final file via MOVE, renaming on a name conflict."""
        final_name = self._original_filename
        dest_url = f"{self._base}/remote.php/dav/files/{self._username}/{final_name}"
        source_url = f"{self._base}/remote.php/dav/uploads/{self._username}/{self._session_id}/.file"
        headers = {
            "Destination": dest_url,
            "OC-Total-Length": str(self._total_size),
            "Overwrite": "F",
        }
        resp = await self._client.request("MOVE", source_url, headers=headers)

        if resp.status_code == 412:  # destination already exists
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            name, ext = final_name.rsplit(".", 1) if "." in final_name else (final_name, "")
            final_name = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
            headers["Destination"] = f"{self._base}/remote.php/dav/files/{self._username}/{final_name}"
            resp = await self._client.request("MOVE", source_url, headers=headers)

        self._raise_for_status(resp)
        await self._client.aclose()
        return final_name

    async def abort(self):
        """Deletes the incomplete upload session folder, if one was started."""
        if not self._session_id:
            await self._client.aclose()
            return
        url = f"{self._base}/remote.php/dav/uploads/{self._username}/{self._session_id}"
        try:
            await self._client.delete(url)
        except Exception:
            pass
        finally:
            await self._client.aclose()

    def _raise_for_status(self, resp):
        """Maps Nextcloud's HTTP status codes to the exception types core/retry.py classifies."""
        if resp.status_code == 507:
            raise InsufficientStorageError("Nextcloud storage is full")
        if resp.status_code in (401, 403):
            raise AuthenticationError("Your saved Nextcloud credentials look incorrect — please redo setup")
        if resp.status_code >= 500:
            raise ConnectionError(f"Nextcloud server error: {resp.status_code}")
        if resp.status_code >= 400 and resp.status_code != 412:
            raise NonRetryableError(f"Unexpected error: {resp.status_code}")
