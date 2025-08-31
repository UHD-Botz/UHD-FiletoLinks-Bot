import asyncio
import logging
from config import API_ID, API_HASH, SLEEP_THRESHOLD
from pyrogram import Client
from UHDBots.util.config_parser import TokenParser
from UHDBots.bot import multi_clients, work_loads, UHDBots


async def initialize_clients():
    """
    Initialize all bot clients (main + multi-token clients).
    """
    # Default client setup
    multi_clients[0] = UHDBots
    work_loads[0] = 0

    # Load tokens from environment
    all_tokens = TokenParser().parse_from_env()
    if not all_tokens:
        print("⚠️ No additional clients found, using default client only.")
        return

    async def start_client(client_id: int, token: str):
        """
        Start an additional client with given ID and token.
        """
        try:
            print(f"🚀 Starting - Client {client_id}")
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                print("⏳ This may take a little while, please wait...")

            client = await Client(
                name=f"uhd_client_{client_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                sleep_threshold=SLEEP_THRESHOLD,
                no_updates=True,
                in_memory=True
            ).start()

            # Initialize workload counter for this client
            work_loads[client_id] = 0

            print(f"✅ Client {client_id} started successfully")
            return client_id, client

        except Exception as e:
            logging.error(f"❌ Failed to start Client {client_id}: {e}", exc_info=True)
            return None

    # Launch all clients in parallel
    results = await asyncio.gather(
        *[start_client(i, token) for i, token in all_tokens.items()],
        return_exceptions=False
    )

    # Filter out failed clients
    started_clients = {cid: client for cid, client in results if cid is not None}

    # Update global client dictionary
    multi_clients.update(started_clients)

    # Log status
    if len(multi_clients) > 1:
        print(f"✅ Multi-Client Mode Enabled ({len(multi_clients)} clients active)")
    else:
        print("⚠️ No additional clients were initialized, using default client only.")

