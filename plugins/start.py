import random
import humanize
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import URL, LOG_CHANNEL, SHORTLINK
from urllib.parse import quote_plus
from UHDBots.util.file_properties import get_name, get_hash, get_media_file_size
from UHDBots.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink



@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    try:
        file = getattr(message, message.media.value)
        filename = file.file_name
        filesize = humanize.naturalsize(file.file_size)
        fileid = file.file_id
        user_id = message.from_user.id
        username = message.from_user.mention

        log_msg = await client.send_cached_media(
            chat_id=LOG_CHANNEL,
            file_id=fileid,
        )

        fileName = get_name(log_msg)

        if not SHORTLINK:
            stream = f"{URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            download = f"{URL}{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        else:
            stream = await get_shortlink(
                f"{URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            )
            download = await get_shortlink(
                f"{URL}{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            )

        await log_msg.reply_text(
            text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id}\n"
                 f"•• ᴜꜱᴇʀɴᴀᴍᴇ : {username}\n\n"
                 f"•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                    InlineKeyboardButton("🖥️ Watch Online 🖥️", url=stream)
                ]]
            )
        )

        rm = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("sᴛʀᴇᴀᴍ 🖥", url=stream),
                InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=download)
            ]]
        )

        msg_text = (
            "<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>\n\n"
            f"<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> <i>{fileName}</i>\n\n"
            f"<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{humanbytes(get_media_file_size(file))}</i>\n\n"
            f"<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <i>{download}</i>\n\n"
            f"<b>🖥 Wᴀᴛᴄʜ :</b> <i>{stream}</i>\n\n"
            "<b>🚸 Nᴏᴛᴇ : ʟɪɴᴋ ᴡᴏɴ'ᴛ ᴇxᴘɪʀᴇ ᴛɪʟʟ ɪ ᴅᴇʟᴇᴛᴇ</b>"
        )

        await message.reply_text(
            text=msg_text,
            quote=True,
            disable_web_page_preview=True,
            reply_markup=rm
        )

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")
