import logging

# Basic logging config for Heroku (stdout)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)
logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)
logging.getLogger("pyrogram.connection.connection").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.auth").setLevel(logging.WARNING)
# Create a logger for importing
logger = logging.getLogger("TelegramBot")
