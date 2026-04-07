# ⚡️ Do Not Remove Credit - Made by @UHDBots
# 💬 For Any Help Join Support Group: @UHDBots_Support
# 🚫 Removing or Modifying these Lines will Cause the bot to Stop Working.


from aiohttp import web
from .route import routes

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app


