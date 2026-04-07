import sys
import glob
import importlib
import logging
import asyncio
import time
import random
import pytz
import warnings
from pathlib import Path
from datetime import date, datetime
from pyrogram import Client, filters, idle
from aiohttp import web

# Faltu warnings ko hide karo
warnings.filterwarnings("ignore", category=DeprecationWarning)

from database.users_chats_db import db
from config import *
from utils import temp
from Script import script
from plugins import web_server

from UHDBots.bot import UHDBots
from UHDBots.util.keepalive import ping_server
from UHDBots.bot.clients import initialize_clients

# ---------------- LOGS CLEANER (Sirf Errors dikhayega) ----------------
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("UHD")
logger.setLevel(logging.INFO)

# ---------------- Globals ----------------
START_TIME = time.time()
EMOJI_LIST = ["😎", "🔥", "❤️", "🤖"]

# ---------------- Plugin Loader ----------------
def load_plugins():
    ppath = "plugins/*.py"
    files = glob.glob(ppath)
    for name in files:
        plugin_path = Path(name)
        plugin_name = plugin_path.stem
        import_path = f"plugins.{plugin_name}"
        spec = importlib.util.spec_from_file_location(import_path, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[import_path] = module

# ---------------- ALL COMMAND HANDLERS ----------------
def add_command_handlers():

    async def react_command(message):
        try: await message.react(random.choice(EMOJI_LIST))
        except: pass

    # PING CMD
    @UHDBots.on_message(filters.command("ping") & filters.user(ADMINS))
    async def ping_handler(client, message):
        await react_command(message)
        start_t = time.time()
        m = await message.reply_text("🏓 Pinging...")
        await m.edit_text(f"✅ Pong! `{round((time.time() - start_t) * 1000)} ms`")

    # UPTIME CMD
    @UHDBots.on_message(filters.command("uptime") & filters.user(ADMINS))
    async def uptime_handler(client, message):
        await react_command(message)
        uptime = time.time() - START_TIME
        days, rem = divmod(int(uptime), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        await message.reply_text(f"⏱ Uptime: `{days}d {hours}h {minutes}m {seconds}s`")

    # BAN CMD
    @UHDBots.on_message(filters.command("ban") & filters.user(ADMINS))
    async def ban_handler(client, message):
        await react_command(message)
        if not message.reply_to_message:
            return await message.reply_text("⚠️ Reply to a user to ban them.")
        user_id = message.reply_to_message.from_user.id
        await db.banned_users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "banned_at": datetime.utcnow()}},
            upsert=True
        )
        await message.reply_text(f"🚫 User `{user_id}` has been banned.")

    # UNBAN CMD
    @UHDBots.on_message(filters.command("unban") & filters.user(ADMINS))
    async def unban_handler(client, message):
        await react_command(message)
        if not message.reply_to_message:
            return await message.reply_text("⚠️ Reply to a user to unban them.")
        user_id = message.reply_to_message.from_user.id
        result = await db.banned_users.delete_one({"user_id": user_id})
        if result.deleted_count:
            await message.reply_text(f"✅ User `{user_id}` has been unbanned.")
        else:
            await message.reply_text("⚠️ This user is not banned.")

    # STATS CMD
    @UHDBots.on_message(filters.command("stats"))
    async def stats_handler(client, message):
        await react_command(message)
        try: total_users = await db.users.count_documents({})
        except: total_users = 0
        try: total_chats = await db.chats.count_documents({})
        except: total_chats = 0
        await message.reply_text(f"📊 **Statistics**\n\n👤 Users: {total_users}\n💬 Chats: {total_chats}")

# ---------------- Bot Startup (COMMANDS FIX) ----------------
async def start():
    # --- CLEAN LOGS ---
    print("\n" + "═"*35)
    print(" 🚀 UHD BOTS ENGINE STARTING...")
    print(" ✨ Status: Premium Speed Active")
    print(" 📢 Visit: t.me/UHDBots")
    print("═"*35 + "\n")

    # 1. Start Client First
    await UHDBots.start()
    
    # 2. Add Handlers IMMEDIATELY after start
    add_command_handlers() 
    
    # 3. Load Plugins
    load_plugins()
    
    bot_info = await UHDBots.get_me()
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    temp.BOT, temp.ME = UHDBots, bot_info.id
    temp.U_NAME, temp.B_NAME = bot_info.username, bot_info.first_name

    # 4. Web Server Startup
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    print(f" ✅ @{bot_info.username} is now Listening to Commands!\n")
    
    # 5. Keep Alive (idle block fix)
    await idle()

# ---------------- Main Execution ----------------
if __name__ == "__main__":
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

    # Yahan hum try-except loop banayenge taaki crash na ho
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"❌ Error: {e}")
