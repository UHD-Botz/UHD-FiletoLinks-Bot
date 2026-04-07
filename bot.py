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

# ---------------- LOGS CLEANER ----------------
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

    @UHDBots.on_message(filters.command("ping") & filters.user(ADMINS))
    async def ping_handler(client, message):
        await react_command(message)
        start_t = time.time()
        m = await message.reply_text("🏓 Pinging...")
        await m.edit_text(f"✅ Pong! `{round((time.time() - start_t) * 1000)} ms`")

    @UHDBots.on_message(filters.command("uptime") & filters.user(ADMINS))
    async def uptime_handler(client, message):
        await react_command(message)
        uptime = time.time() - START_TIME
        days, rem = divmod(int(uptime), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        await message.reply_text(f"⏱ Uptime: `{days}d {hours}h {minutes}m {seconds}s`")

    @UHDBots.on_message(filters.command("stats"))
    async def stats_handler(client, message):
        await react_command(message)
        try: 
            total_users = await db.users.count_documents({})
            total_chats = await db.chats.count_documents({})
        except: 
            total_users = total_chats = 0
        await message.reply_text(f"📊 **Statistics**\n\n👤 Users: {total_users}\n💬 Chats: {total_chats}")

# ---------------- Bot Startup ----------------
async def start():
    print("\n" + "═"*35)
    print(" 🚀 UHD BOTS ENGINE STARTING...")
    print("═"*35 + "\n")

    await UHDBots.start()
    
    # Handlers aur Plugins load karo
    add_command_handlers()
    load_plugins()
    
    bot_info = await UHDBots.get_me()
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    temp.BOT, temp.ME = UHDBots, bot_info.id
    temp.U_NAME, temp.B_NAME = bot_info.username, bot_info.first_name

    # Web Server Startup
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    print(f" ✅ Bot @{bot_info.username} is UP & RUNNING!\n")
    await idle()

# ---------------- Main Execution (SIMPLE & CLEAN) ----------------
if __name__ == "__main__":
    # uvloop ko poori tarah hata diya hai crash fix karne ke liye
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        print("🛑 Stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
