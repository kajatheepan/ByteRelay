import os
import time
import asyncio
from v0.translation import Translation
from v0.helper.humanbytes import humanbytes


CHUNK_SIZE = 1024*1024 # 1 MB

# Class to handle file reading with progress updates for uploads
class FileWithProgress:
    def __init__(self, file_path, message, chunk_size=CHUNK_SIZE):
        # Initialize file properties and progress tracking variables
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.total_size = os.path.getsize(file_path)
        self.bytes_read = 0
        self.message = message
        self.last_update_time = time.time()

    def __aiter__(self):
        # Open file for reading in binary mode and return iterator
        self.file = open(self.file_path, 'rb')
        return self

    async def __anext__(self):
        # Read next chunk asynchronously
        chunk = await asyncio.to_thread(self.file.read, self.chunk_size)
        if not chunk:
            self.file.close()
            raise StopAsyncIteration
        # Update progress and return chunk
        self.bytes_read += len(chunk)
        await self._show_progress()
        return chunk

    async def _show_progress(self):
        # Update progress message every 3 seconds
        current_time = time.time()
        if current_time - self.last_update_time < 3:  # Update every 3 seconds
            return
        # Calculate and display progress percentage
        percent = (self.bytes_read / self.total_size) * 100
        await self.message.edit_text(Translation.UPLOAD_PROGRESS.format(
            percent=percent, file_name=os.path.basename(self.file_path),total_size=humanbytes(self.total_size),
            bytes_read=humanbytes(self.bytes_read)
        ))
        self.last_update_time = current_time
    
class DownloadProgressReader:
    def __init__ (self):
        self.last_update_time = time.time()

    async def download_progress(self, current, total, message,file_name):
        current_time = time.time()
        if current_time - self.last_update_time < 3:  # Update every 3 seconds
            return
        percent = (current / total) * 100
        await message.edit_text(Translation.DOWNLOAD_PROGRESS.format(
            percent=percent, current=humanbytes(current), total=humanbytes(total),file_name=file_name
        ))
        self.last_update_time = current_time
