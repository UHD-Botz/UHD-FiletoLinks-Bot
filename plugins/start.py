import humanize
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import URL, LOG_CHANNEL
from urllib.parse import quote_plus
from UHDBots.util.file_properties import get_name, get_hash, get_media_file_size
from UHDBots.util.human_readable import humanbytes


@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name if file.file_name else "Untitled"
        filesize = humanize.naturalsize(file.file_size)
        fileid = file.file_id
        user_id = message.from_user.id
        username = message.from_user.mention

        # Send file to log channel
        log_msg = await client.send_cached_media(
            chat_id=LOG_CHANNEL,
            file_id=fileid,
        )

        fileName = get_name(log_msg)

        # Stream & Download links (without shortlink)
        stream = f"{URL}watch/{log_msg.id}/{quote_plus(fileName)}?hash={get_hash(log_msg)}"
        download = f"{URL}{log_msg.id}/{quote_plus(fileName)}?hash={get_hash(log_msg)}"

        # Send details in log channel
        await log_msg.reply_text(
            text=f"📌 ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ <code>{user_id}</code>\n"
                 f"👤 ᴜꜱᴇʀ : {username}\n\n"
                 f"📂 ꜰɪʟᴇ ɴᴀᴍᴇ : <b>{fileName}</b>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🚀 Fast Download", url=download),
                    InlineKeyboardButton("🖥 Watch Online", url=stream)
                ]]
            )
        )

        # Reply to user with links
        rm = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🖥 Watch", url=stream),
                InlineKeyboardButton("📥 Download", url=download)
            ]]
        )

        msg_text = (
            "<i><u>✅ Your Link is Ready!</u></i>\n\n"
            f"📂 <b>File Name :</b> <i>{fileName}</i>\n"
            f"📦 <b>File Size :</b> <i>{humanbytes(get_media_file_size(file))}</i>\n\n"
            f"📥 <b>Download :</b> <code>{download}</code>\n"
            f"🖥 <b>Watch :</b> <code>{stream}</code>\n\n"
            "⚠️ <b>Note:</b> Links will stay active until I delete the file."
        )

        await message.reply_text(
            text=msg_text,
            disable_web_page_preview=True,
            reply_markup=rm
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")
