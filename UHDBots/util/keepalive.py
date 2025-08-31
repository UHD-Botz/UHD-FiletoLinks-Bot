import asyncio
import logging
import aiohttp
import traceback
import time
from config import *


async def ping_server():
    """Continuously ping the server to prevent it from idling."""
    sleep_time = PING_INTERVAL

    headers = {
        "User-Agent": "UHDBots-KeepAlive/1.0",
        "Accept": "*/*",
    }

    while True:
        await asyncio.sleep(sleep_time)
        try:
            start_time = time.perf_counter()

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers=headers
            ) as session:
                async with session.get(URL) as resp:
                    latency = (time.perf_counter() - start_time) * 1000
                    logging.info(
                        f"Pinged {URL} | Status: {resp.status} | Latency: {latency:.2f} ms"
                    )

                    # If server returns error, retry sooner
                    if resp.status >= 500:
                        logging.warning("Server error detected, retrying in 30s...")
                        sleep_time = 30
                    else:
                        sleep_time = PING_INTERVAL

        except asyncio.TimeoutError:
            logging.warning(f"Ping timeout while connecting to {URL}!")
            sleep_time = 30

        except aiohttp.ClientError as e:
            logging.error(f"Client error while pinging {URL}: {e}")
            sleep_time = 60  # retry slower if connection fails

        except Exception:
            logging.error("Unexpected error in keepalive ping:")
            traceback.print_exc()
            sleep_time = 60

