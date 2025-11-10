from pyrogram import Client as bot
from pyrogram.types import Message  
from pyrogram import filters, enums
from v0.translation import Translation,InlineKeyboard
import re
from xml.etree import ElementTree
from v0.helper.nextcloud import nextcloud 
from v0.helper.logger import logger
from v0.helper.utils import get_bot_username

@bot.on_message(filters.command(['start']))
async def start_command(client: bot, message: Message):

    try:
        url = nextcloud.upload_point
        match = re.match(r"(https?://[^/]+/)", url)
        if match:
            base_url = match.group(1)
            nextcloud.nextcloud_server = base_url

        #get username
        bot_username = await get_bot_username(client)
        
        logger.info(f"Start command received from user {message.from_user.first_name} (ID: {message.from_user.id})")
        await message.reply_text(Translation.WELCOME.format(username=message.from_user.first_name, nextcloud_url=base_url, bot_username=bot_username),reply_markup=InlineKeyboard.START, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in start_command: {str(e)}")
        await message.reply_text("An error occurred while processing your request.")

@bot.on_message(filters.command(['help']))
async def help_command(client: bot, message: Message):
    try:
        await message.reply_text(Translation.HELP, reply_markup=InlineKeyboard.HELP, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in help_command: {str(e)}")
        await message.reply_text("An error occurred while processing your request.")

@bot.on_message(filters.command('about'))
async def about_command(client:bot,message:Message):
    try:
        #get username
        bot_username = await get_bot_username(client)
        await message.reply_text(Translation.ABOUT.format(bot_username=bot_username),reply_markup=InlineKeyboard.ABOUT, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f'Error in about_command: {str(e)}')