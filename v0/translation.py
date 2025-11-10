from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Translation(object):
    """
    Contains all user-facing messages and responses for the TG2DMS Bot.
    """
    WELCOME = (
        "**Hello {username}!** 👋\n\n"
        "I'm your **{bot_username}** Bot, helping you upload files from Telegram to NextCloud. 🚀\n\n"
        "• NextCloud domain: **{nextcloud_url}** 🌐\n"
        "• To get started, please log in to your NextCloud account. 🔑\n"
        "• To upload files, reply to any media message with `/upload` 📤\n\n"
    )

    HELP = (
        "**Here's how you can use me:**\n\n"
        "🔹 `/start` – Start the bot\n"
        "🔹 `/help` – Show this help message\n"
        "🔹 `/login username password` – Log in to your WebDAV account\n"
        "🔹 `/upload` – Upload a Telegram file to your NextCloud\n"
        "🔹 `/batch` – Upload multiple files at once\n\n"
        "_Note: Make sure you're logged in before using upload or batch features._"
    )

    ABOUT = (
        "**About {bot_username} Bot** ℹ️\n\n"
        "🤖 A Telegram bot that helps you upload files directly to Your NextCloud.\n\n"
        "👨‍💻 **Developer:** [Kajatheepan](https://github.com/kajatheepan)\n"
        "📦 **Version:** 1.0.0\n"
        "🔗 **Repo:** [github.com/kajatheepan/Telegram2NextCloud](https://github.com/kajatheepan/Telegram2NextCloud)\n\n"
        "Feel free to star the repo if you find this bot useful! ⭐"
    )

    ERROR = (
        "**Oops! Something went wrong.**\n"
        "Please try again later."
    )
    DOWNLOAD_START = (
        "**Downloading file:** `{file_name}`\n"
        "**Size:** `{size}`"
    )
    
    DOWNLOAD_PROGRESS = (
        "⬇️ **Downloading:** `{percent:.2f}%`\n\n"
        "📥 **Downloaded:** `{current}`\n\n"
        "📄 **File:** `{file_name}`\n\n"
        "📦 **Size:** `{total}`\n\n"
        
    )
    DOWNLOAD_SUCCESS = ("**File downloaded successfully!** 🎉"
                        "\n\n"
                        "Now Uploading to Your NextCloud...")

    DOWNLOAD_FAILURE = (
        "**Download failed!**\n"
        "Please check the file path and try again."
    )

    FILE_NOT_FOUND = (
        "**File not found!**\n"
        "Please double-check the file name or path."
    )

    INVALID_COMMAND = (
        "**Invalid command!**\n"
        "Type `/help` to see the available options."
    )

    INVALID_LOGIN_CMD = "**Invalid Login Command**\n\nUsage: `/login username password`"

    LOGIN_SUCCESS = (
        "**Login successful!**\n"
        "You're all set to use the bot. 🔓"
        "\n\n"
        "**🗑️ Used Quota:** `{used_quota}`\n" \
        "**📦 Total Quota:** `{total_quota}`\n"
    )

    LOGIN_ALREADY = (
        "You're already logged in! No need for a double-dip. 😄"
    )

    LOGIN_REQUIRED = ("**You need to login to continue.**"
                    "\n\nUse `/login username password` to log in to your NextCloud account.")

    LOGIN_HELP = (
        "**Login Command Help**\n\n"
        "To log in, use the command:\n"
        "`/login username password`\n\n"
        "Replace `username` and `password` with your NextCloud credentials.\n"
    )

    LOGIN_FAILURE = (
        "**Login failed!**\n"
        "Please check your credentials and try again."
    )

    UPLOAD_PROGRESS = (
        "⬆️ **Uploading:** `{percent:.2f}%`\n\n"
        "📤 **Uploaded:** `{bytes_read}`\n\n"
        "📄 **File:** `{file_name}`\n\n"
        "📦 **Size:** `{total_size}`\n"
        
    )

    UPLOAD_SUCCESS = (
        "**Upload complete!**\n\n"
        "**📄 File:** `{file_name}`\n"
        "**📦 Size:** `{size}`"
    )

    UPLOAD_FAILURE = (
        "**Upload failed!**\n"
        "Please check your login and try again."
    )

    INSUFFICIENT_QUOTA = (
        "**Not enough space to upload this file!**\n\n"
        "🗑️ Maybe delete a few files and try again 😅"
    )

    COOLDOWN_TEXT = (
        "⏳ Please wait {wait_time} seconds before using this again."
    )


class InlineKeyboard(object):
    """
    Contains all inline keyboard buttons for the TG2DMS Bot.
    """
    LOGIN_BUTTON = InlineKeyboardButton("🔐 Login", callback_data="login")

    UPLOAD_BUTTON = InlineKeyboardButton("📤 Upload File", callback_data="upload")

    BATCH_UPLOAD_BUTTON = InlineKeyboardButton("📚 Batch Upload", callback_data="batch_upload")

    ABOUT_BUTTON = InlineKeyboardButton("ℹ️ About", callback_data="about")

    HELP_BUTTON = InlineKeyboardButton("❔ Help", callback_data="help")

    REPO_URL = InlineKeyboardButton(
        "⭐ GitHub Repo", url="https://github.com/kajatheepan/Telegram2Nextcloud")
    ABOUT_ME_URL = InlineKeyboardButton(
        "👨‍💻 About Me", url="https://github.com/kajatheepan/")
    BACK = InlineKeyboardButton("Back", callback_data="back_to_start")
    CLOSE = InlineKeyboardButton("Close", callback_data="close")
    START = InlineKeyboardMarkup(
        [
            [
                LOGIN_BUTTON,
                HELP_BUTTON,
            ],
            [
                ABOUT_BUTTON,
                CLOSE
            ]
        ])
    
    ABOUT = InlineKeyboardMarkup(
        [
            [
                REPO_URL,
                ABOUT_ME_URL
            ],
            [
                BACK,
                CLOSE
            ]
        ])  
    HELP = InlineKeyboardMarkup(
        [[CLOSE]]
    )