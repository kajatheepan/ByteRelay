from v0.helper.logger import logger
from v0.translation import Translation
from v0.config import Configs
import time 

def get_file_name(message):
    if message.document:
        if isinstance(message.document.file_name, str):
            return message.document.file_name
        else:
            return f"document_{message.document.file_id}.bin"
    elif message.video:
        if isinstance(message.video.file_name, str):
            return message.video.file_name
        else:
            return f"video_{message.video.file_id}.mp4"
    elif message.audio:
        if isinstance(message.audio.file_name, str):
            return message.audio.file_name
        else:
            return f"audio_{message.audio.file_id}.mp3"
    elif message.photo:
        if isinstance(message.photo.file_name, str):
            return message.photo.file_name
        else:
            return f"photo_{message.photo.file_id}.jpg"
    return "unknown_file"


def get_file_size(message):
    if message.document:
        return message.document.file_size
    elif message.video:
        return message.video.file_size
    elif message.audio:
        return message.audio.file_size
    elif message.photo:
        return message.photo.file_size
    return 0



async def cooldown_user(client, message):
    
        #Cooldown feature to handle user requests
    user_id = message.from_user.id
    if user_id not in client.cooldown_pool:
        client.cooldown_pool[user_id] = 0

    user_cooldowns = client.cooldown_pool[user_id]
    logger.info(f"User {message.from_user.id} user cooldown {user_cooldowns}")
    now = time.time() 

    if now - user_cooldowns < Configs.COOLDOWN_SECONDS:
        wait_time = Configs.COOLDOWN_SECONDS - (now - user_cooldowns)
        await message.reply(Translation.COOLDOWN_TEXT.format(wait_time = int(wait_time)))
        logger.info(f'User {user_id} Wait Time: {wait_time}')
        return True
    # Update the user's cooldown timestamp
    client.cooldown_pool[user_id] = now
    logger.info(f"User {message.from_user.id} cooldown updated to {now}")
    return False

async def get_bot_username(client):
    me = await client.get_me()
    return f"[{me.first_name + ' ' + me.last_name if me.first_name and me.last_name else me.first_name if me.first_name else  ''}](https://t.me/{me.username})"