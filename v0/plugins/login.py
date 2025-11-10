from pyrogram import Client as bot
from pyrogram.types import Message  
from pyrogram import filters,enums
from v0.translation import Translation
from xml.etree import ElementTree
from v0.helper.humanbytes import humanbytes
from v0.helper.checkquota import check_quota
from v0.helper.nextcloud import nextcloud
from v0.helper.logger import logger

@bot.on_message(filters.command(['login']))
async def login_command(client: bot, message: Message):
    logger.info(f"Login attempt from user ID: {message.from_user.id}")
    
    if await check_login(client, message):
        await message.reply_text(Translation.LOGIN_ALREADY,parse_mode=enums.ParseMode.MARKDOWN)
        return
    await message.delete()
    message_text = message.text.strip().split()
    if len(message_text) != 3:
        await message.reply_text(Translation.INVALID_LOGIN_CMD,parse_mode=enums.ParseMode.MARKDOWN)
    else:
        username = message_text[1]
        password = message_text[2]
        try:
            logger.info(f"Attempting Nextcloud login for user: {username}")
            nextcloud_client = nextcloud(username, password)
            response = await nextcloud_client.login()
            
            if response:
                client.user_sessions[message.from_user.id] = nextcloud_client
                used_quota = humanbytes(nextcloud_client.used_quota)
                total_quota = humanbytes(nextcloud_client.used_quota+nextcloud_client.available_quota)
                await message.reply_text(Translation.LOGIN_SUCCESS.format(used_quota=used_quota, total_quota=total_quota), parse_mode=enums.ParseMode.MARKDOWN)
            else:
                logger.error(f"Login failed for user {username}: Invalid credentials")
                await message.reply_text(Translation.LOGIN_FAILURE, parse_mode=enums.ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Login failed for user {username}: {str(e)}")
            await message.reply_text(f"Login failed: {str(e)}")
            return

async def check_login(client: bot, message: Message):
    is_logged = client.user_sessions.get(message.from_user.id) and client.user_sessions[message.from_user.id].islogged_in
    if is_logged:
        logger.debug(f"Login check: User {message.from_user.id} is already logged in")
    return is_logged
