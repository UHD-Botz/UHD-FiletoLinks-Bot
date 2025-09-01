import re
from os import environ

# ──────────────────────── Regex Pattern ─────────────────────────
id_pattern = re.compile(r'^-?\d+$')

# ──────────────────────── Bot Information ───────────────────────
SESSION = environ.get("SESSION", "UHDFiletoLinksBot")
API_ID = int(environ.get("API_ID", "0"))
API_HASH = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")

# ──────────────────────── Server Settings ───────────────────────
PORT = int(environ.get("PORT", "8080"))
MULTI_CLIENT = False
SLEEP_THRESHOLD = int(environ.get("SLEEP_THRESHOLD", "60"))
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
ON_HEROKU = "DYNO" in environ
URL = environ.get("URL", "https://traditional-emera-gdrives7511-6c52eaab.koyeb.app/")

# ──────────────────────── Admins & Channels ─────────────────────
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "0"))
ADMINS = [
    int(admin) if id_pattern.match(admin) else admin
    for admin in environ.get("ADMINS", "").split()
]

# ──────────────────────── Database Settings ─────────────────────
DATABASE_URI = environ.get("DATABASE_URI", "")
DATABASE_NAME = environ.get("DATABASE_NAME", "HDMoviesEarth")
