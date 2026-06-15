# Telegram to NextCloud Bot 🤖

**A simple bot that automatically saves your Telegram media files to your NextCloud instance.
**
## What it does

- Saves photos, videos, and documents from Telegram to your NextCloud
- Easy to set up and use
## Setup

1. Get API credentials from [my.telegram.org](https://my.telegram.org):

2. Get your bot token from [@BotFather](https://t.me/BotFather) on Telegram

3. Clone this repository:
```bash
git clone https://github.com/kajatheepan/Telegram2NextCloud.git
cd Telegram-to-NextCloud
```

4. Configure environment variables:
     - Copy `.env.example` to `.env`
     - Edit `.env` with your settings:
    
     ```env
     API_ID="your_api_id" # API ID from my.telegram.org
     API_HASH="your_api_hash" # API hash from my.telegram.org
     BOT_TOKEN="your_telegram_bot_token" # Your Telegram bot token from @BotFather
     UPLOAD_POINT="https://nextcloud.example.com/remote.php/webdav/" # Your NextCloud WebDAV URL
     ```

5. Start the bot:
```bash
python main.py
```

## Usage

1. Login to your NextCloud with `/login` command
2. Send media files to the bot
3. Reply to any media with `/upload` command
4. Bot will save them to your NextCloud



## Need Help?

Open an issue if you run into problems!

## Contributing

Contributions are welcome! Feel free to open issues, submit pull requests, suggest features, or improve documentation.

