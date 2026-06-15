from pyrogram import Client as bot
from pyrogram import filters, enums
from pyrogram.types import Message
from v0.translation import Translation
from v0.helper.humanbytes import humanbytes
from v0.helper.logger import logging as logger
from v0.helper.progress import DownloadProgressReader
from v0.helper.nextcloud import nextcloud
from v0.helper.utils import get_file_name, get_file_size
from pyrogram.errors import FloodWait
import asyncio,os
from v0.helper.utils import cooldown_user

COOLDOWN_SECONDS = 60  # Cooldown time in seconds

@bot.on_message(filters.command(['upload']))
async def download_command(client, message):
    """Handles the /upload command to download media from a message and upload it to NextCloud. """

    # Check if the user is in cooldown
    if await cooldown_user(client, message):
        return
    
    # Get the NextCloud client instance for the current user
    nextcloud_client = client.user_sessions.get(message.from_user.id, None)

    # Check if the user is logged in to NextCloud
    if nextcloud_client == None or nextcloud_client.islogged_in == False:
        await message.reply_text(Translation.LOGIN_REQUIRED, parse_mode=enums.ParseMode.MARKDOWN)
        return

    # Check if the command is replying to a message
    if message.reply_to_message:
        reply_message = message.reply_to_message
    
        # Verify if the replied message contains downloadable media
        if reply_message.document or reply_message.video or reply_message.audio or reply_message.photo:
            # Extract file information
            file_name = get_file_name(reply_message)
            file_size = get_file_size(reply_message)
            file_path = f"./downloads/{file_name}"
            
            logger.info(f"Preparing to download file: {file_name} ({humanbytes(file_size)})")

            # Verify available quota before download
            if file_size > await nextcloud_client.get_available_quota() - nextcloud_client.infile_quota:
                logger.warning(f"Insufficient quota for user {message.from_user.id}. Required: {humanbytes(file_size)}")
                await message.reply_text(Translation.DOWNLOAD_FAILURE + "\n" + Translation.INSUFFICIENT_QUOTA, 
                                      parse_mode=enums.ParseMode.MARKDOWN)
                return
            
            try:
                logger.info(f"Starting download of file: {file_name}")
                
                # Send initial download status message
                parse_message = await message.reply_text(
                    Translation.DOWNLOAD_START.format(file_name=file_name, size=humanbytes(file_size)), 
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                
                # Initialize progress tracker
                download_progress = DownloadProgressReader()
                
                # Download media with flood wait handling
                try:
                    nextcloud_client.infile_quota += file_size  # Deduct quota before download
                    await client.download_media(
                        reply_message,
                        file_path,
                        progress=download_progress.download_progress,
                        progress_args=(parse_message, file_name)
                    )
                except FloodWait as e:
                    logger.warning(f"Flood wait encountered: {e.x} seconds. Retrying download after waiting.")
                    await asyncio.sleep(e.x)
                    await client.download_media(
                        reply_message,
                        file_path,
                        progress=download_progress.download_progress,
                        progress_args=(parse_message, file_name)
                    )
                
                # Update status after successful download
                await parse_message.edit_text(Translation.DOWNLOAD_SUCCESS, parse_mode=enums.ParseMode.MARKDOWN)
                logger.info(f"Download completed: {file_name}")

                # Verify quota again before upload
                if file_size > nextcloud_client.available_quota:
                    logger.warning(f"Insufficient quota for user {message.from_user.id}. Required: {humanbytes(file_size)}")
                    await parse_message.edit_text(Translation.INSUFFICIENT_QUOTA, parse_mode=enums.ParseMode.MARKDOWN)
                    return

                # Upload file to NextCloud
                upload_response = await nextcloud_client.upload(file_path, file_name, parse_message)
                nextcloud_client.infile_quota -= file_size
                if upload_response == True:
                    await parse_message.edit_text(
                        Translation.UPLOAD_SUCCESS.format(file_name=file_name, size=humanbytes(file_size)),
                        parse_mode=enums.ParseMode.MARKDOWN
                    )

                #Remove the downloaded file after upload
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed local file after upload: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing local file after upload: {str(e)}", exc_info=True)

            except Exception as e:
                logger.error(f"Error during download/upload process: {str(e)}", exc_info=True)
                await parse_message.edit_text(f"{Translation.DOWNLOAD_FAILURE}\nError: {str(e)}")

    else:
        logger.warning(f"User {message.from_user.id} did not reply to a media message")
        await message.reply_text("Please reply to a media message to download it.", 
                               parse_mode=enums.ParseMode.MARKDOWN)
