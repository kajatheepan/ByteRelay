from pyrogram import Client as bot
from pyrogram import filters, enums
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from v0.translation import Translation,InlineKeyboard
from v0.helper.logger import logging as logger
from v0.helper import utils
from v0.helper import nextcloud

@bot.on_callback_query()
async def handle_callback_query(client: bot, callback_query: CallbackQuery):
    # This will handle all callback queries
    # You can use callback_query.data to check which button was pressed
    query_data = callback_query.data
    message = callback_query.message
    user_id = callback_query.from_user.id
    if query_data.startswith("login"):
        #get user nextcloud client object
        if client.user_sessions.get(user_id) is not None:
            nextcloud_client = client.user_sessions[user_id]
            if nextcloud_client.islogged_in:
                await message.edit_text(
                    Translation.LOGIN_ALREADY,
                    reply_markup=InlineKeyboard.CLOSE,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
        else:
            await message.edit_text(
                Translation.LOGIN_HELP,
                reply_markup=InlineKeyboard.CLOSE,
                parse_mode=enums.ParseMode.MARKDOWN
            )
    elif query_data.startswith("help"):
        await message.edit_text(
            Translation.HELP,
            reply_markup=InlineKeyboard.HELP,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif query_data.startswith("about"):
        await message.edit_text(
            Translation.ABOUT.format(bot_username=await utils.get_bot_username(client)),
            reply_markup=InlineKeyboard.ABOUT,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif query_data.startswith("back_to_start"):
        await message.edit_text(
            Translation.WELCOME.format(bot_username=await utils.get_bot_username(client),username=message.from_user.first_name,nextcloud_url = nextcloud.nextcloud.nextcloud_server),
            reply_markup=InlineKeyboard.START,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    elif query_data.startswith("close"):
        await message.delete()

    