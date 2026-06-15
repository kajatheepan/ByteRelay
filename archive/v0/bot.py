from pyrogram import Client, filters
from pyrogram.types import Message
from v0.config import Configs as Config
from v0.helper.logger import logging

api_id = Config.API_ID
api_hash = Config.API_HASH  
bot_token = Config.BOT_TOKEN  
workers = Config.WORKERS  # Number of workers for handling requests
plugins = dict(root="plugins")  # Directory where your plugins are located

app = Client("TGbot", bot_token=bot_token,
             plugins=plugins,
             workers=workers,  # Number of workers for handling requests
             max_concurrent_transmissions=Config.MAX_CONCURRENT_TRANSMISSIONS,  # Maximum number of concurrent transmissions
             sleep_threshold=60,
             api_id=api_id,
             api_hash=api_hash)  # Sleep threshold to avoid rate limits


app.user_sessions = {}
app.cooldown_pool = {}  # Set to track users in cooldown
logging.info("Bot is Starting...")
#Run the bot
app.run()



