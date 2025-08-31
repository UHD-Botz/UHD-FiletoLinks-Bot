import logging
import logging.config
from typing import Union, Optional, AsyncGenerator

from pyrogram import Client, types
from aiohttp import web

from config import *
from utils import temp


# ✅ Logging setup
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Suppress noisy loggers
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)


class UHDXBots(Client):
    """Custom Pyrogram Client for UHD Bots"""

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
            in_memory=True  # ✅ Avoids session file overhead
        )

    async def set_self(self):
        """Store self reference globally in utils.temp"""
        temp.BOT = self

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """
        Custom async generator to iterate chat messages sequentially.

        Args:
            chat_id (int | str): Target chat (ID or username)
            limit (int): Total messages to fetch
            offset (int, optional): Starting point. Defaults to 0.

        Yields:
            types.Message: Messages one by one
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(
                chat_id, list(range(current, current + new_diff + 1))
            )
            for message in messages:
                yield message
                current += 1


# ✅ Default Client instance
UHDBots = UHDXBots()

# ✅ Multi-client support storage
multi_clients: dict[int, Client] = {}
work_loads: dict[int, int] = {}



