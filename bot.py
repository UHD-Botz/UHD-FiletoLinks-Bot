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
from pyrogram import idle
from aiohttp import web

# Faltu warnings ko mute karo
warnings.filterwarnings("ignore", category=DeprecationWarning)

from database.users_chats_db import db
from config import *
from utils import temp
from Script import script
from plugins import web_server

from UHDBots.bot import UHDBots
from UHDBots.util.keepalive import ping_server
from UHDBots.bot.clients import initialize_clients

# ---------------- LOGS CLEANER (PRO) ----------------
logging.basicConfig(level=logging.ERROR) # Sirf errors dikhao
logger = logging.getLogger("UHD")
logger.setLevel(logging.INFO)

# ---------------- Globals ----------------
START_TIME = time.time()
EMOJI_LIST = ["😎", "🔥", "❤️", "🤖"]

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

# ---------------- Bot Startup ----------------
async def start():
    # --- CLEAN LOGS OUTPUT ---
    print("\n" + "="*30)
    print("🚀 UHD BOTS ENGINE STARTING...")
    print("✨ Status: Premium Speed Active")
    print("📢 Visit: t.me/UHDBots")
    print("🌐 Site: bit.ly/4dCws8h")
    print("⭐ Star: github.com/UHD-Botz/UHD-FiletoLinks-Bot")
    print("="*30 + "\n")

    await UHDBots.start()
    bot_info = await UHDBots.get_me()
    await initialize_clients()
    load_plugins()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    temp.BOT, temp.ME = UHDBots, bot_info.id
    temp.U_NAME, temp.B_NAME = bot_info.username, bot_info.first_name

    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    await UHDBots.send_message(chat_id=LOG_CHANNEL, text=f"🚀 **Bot Restarted!**\n📅 {date.today()}\n🕒 {now.strftime('%I:%M:%S %p')}")

    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    add_command_handlers()
    print("✅ UHD Bots is now UP and RUNNING!\n")
    await idle()

# ---------------- Run Bot ----------------
if __name__ == "__main__":
    # Linux speed optimization (uvloop)
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
