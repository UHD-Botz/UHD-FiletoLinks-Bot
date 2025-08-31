import logging
import datetime, time, asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from database.users_chats_db import db
from config import ADMINS


@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def pm_broadcast(bot, message):
    b_msg = await bot.ask(chat_id=message.from_user.id, text="Please send the broadcast message now.")
    
    try:
        users = await db.get_all_users()
        status_msg = await message.reply_text('Broadcast has started...')
        start_time = time.time()
        
        total_users = await db.total_users_count()
        done = success = blocked = deleted = failed = 0

        async for user in users:
            if 'id' in user:
                sent, status = await broadcast_messages(int(user['id']), b_msg)
                if sent:
                    success += 1
                else:
                    if status == "Blocked":
                        blocked += 1
                    elif status == "Deleted":
                        deleted += 1
                    elif status == "Error":
                        failed += 1
                done += 1

                if not done % 20:
                    await status_msg.edit(
                        f"Broadcast in progress:\n\n"
                        f"Total Users: {total_users}\n"
                        f"Completed: {done} / {total_users}\n"
                        f"Success: {success}\n"
                        f"Blocked: {blocked}\n"
                        f"Deleted: {deleted}\n"
                        f"Failed: {failed}"
                    )
            else:
                done += 1
                failed += 1
                if not done % 20:
                    await status_msg.edit(
                        f"Broadcast in progress:\n\n"
                        f"Total Users: {total_users}\n"
                        f"Completed: {done} / {total_users}\n"
                        f"Success: {success}\n"
                        f"Blocked: {blocked}\n"
                        f"Deleted: {deleted}\n"
                        f"Failed: {failed}"
                    )

        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await status_msg.edit(
            f"✅ Broadcast Completed!\n\n"
            f"⏱ Duration: {time_taken}\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📌 Completed: {done}\n"
            f"✅ Success: {success}\n"
            f"⛔ Blocked: {blocked}\n"
            f"🗑 Deleted: {deleted}\n"
            f"⚠ Failed: {failed}"
        )
    except Exception as e:
        logging.error(f"Broadcast Error: {e}")


async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} removed from DB (Deleted Account).")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} removed from DB (Invalid PeerId).")
        return False, "Error"
    except Exception as e:
        logging.error(f"Error while broadcasting to {user_id}: {e}")
        return False, "Error"

