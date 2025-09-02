import random
import humanize
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import URL, LOG_CHANNEL
from urllib.parse import quote_plus
from UHDBots.util.file_properties import get_name, get_hash, get_media_file_size
from UHDBots.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp


# ------------------ START COMMAND ------------------ #
@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply_text(
        text=(
            "👋 Hello! I am your **File to Link Bot**.\n\n"
            "📤 Send me any file or video, and I will give you:\n"
            "🔗 Direct Download Link\n"
            "🖥 Online Streaming Link\n\n"
            "⚡ Fast & Secure Links - No Expiry!"
        ),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💡 About", callback_data="about")]]
        ),
        disable_web_page_preview=True,
        quote=True
    )


# ------------------ FILE HANDLER ------------------ #
@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name
        filesize = humanize.naturalsize(file.file_size)
        fileid = file.file_id
        user_id = message.from_user.id
        username = message.from_user.mention

        # Save file in log channel
        log_msg = await client.send_cached_media(
            chat_id=LOG_CHANNEL,
            file_id=fileid,
        )

        fileName = get_name(log_msg)

        # ✅ Direct links only (no shortlink feature)
        stream = f"{URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        download = f"{URL}{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        # Log message in log channel
        await log_msg.reply_text(
            text=f"📌 Link Generated for user {username} (ID: {user_id})\n\n"
                 f"📂 File Name: {fileName}",
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🚀 Fast Download", url=download),
                    InlineKeyboardButton("🖥 Watch Online", url=stream)
                ]]
            )
        )

        # Send links to user
        msg_text = (
            "<i><u>✅ Your Link is Ready!</u></i>\n\n"
            f"<b>📂 File Name:</b> <i>{fileName}</i>\n"
            f"<b>📦 File Size:</b> <i>{humanbytes(get_media_file_size(file))}</i>\n\n"
            f"<b>📥 Download:</b> <i>{download}</i>\n"
            f"<b>🖥 Watch:</b> <i>{stream}</i>\n\n"
            "<b>🚸 Note:</b> Links will work until I delete the file."
        )

        await message.reply_text(
            text=msg_text,
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("📥 Download", url=download),
                    InlineKeyboardButton("🖥 Watch", url=stream)
                ]]
            )
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")
