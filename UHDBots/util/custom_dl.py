import math
import asyncio
import logging
import time
from typing import Dict, Union
from config import *
from UHDBots.bot import work_loads
from pyrogram import Client, utils, raw
from UHDBots.util.file_properties import get_file_ids
from pyrogram.session import Session, Auth
from pyrogram.errors import AuthBytesInvalid
from UHDBots.server.exceptions import FileNotFound
from pyrogram.file_id import FileId, FileType, ThumbnailSource


class ByteStreamer:
    def __init__(self, client: Client):
        """
        A custom class for handling Telegram file streaming with caching & session management.
        """
        self.clean_timer = 30 * 60  # default: 30 min
        self.client: Client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        self.cache_last_access: Dict[int, float] = {}
        self._stop = False

        asyncio.create_task(self.clean_cache())

    async def stop(self):
        """Stop cache cleaner gracefully."""
        self._stop = True

    async def get_file_properties(self, id: int) -> FileId:
        """Return cached file properties or generate them if not cached."""
        if id not in self.cached_file_ids:
            await self.generate_file_properties(id)
            logging.debug(f"Cached file properties for message with ID {id}")
        self.cache_last_access[id] = time.time()
        return self.cached_file_ids[id]

    async def generate_file_properties(self, id: int) -> FileId:
        """Generate and cache file metadata from a Telegram message."""
        file_id = await get_file_ids(self.client, LOG_CHANNEL, id)
        if not file_id:
            logging.warning(f"Message with ID {id} not found in LOG_CHANNEL={LOG_CHANNEL}")
            raise FileNotFound(f"Message ID {id} not found")

        self.cached_file_ids[id] = file_id
        self.cache_last_access[id] = time.time()
        logging.debug(f"Generated and cached file ID for message ID {id}")
        return file_id

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        """Create or reuse a media session for the given DC."""
        media_session = client.media_sessions.get(file_id.dc_id)

        if media_session:
            logging.debug(f"Using cached media session for DC {file_id.dc_id}")
            return media_session

        # Create new session if not exists
        if file_id.dc_id != await client.storage.dc_id():
            media_session = Session(
                client,
                file_id.dc_id,
                await Auth(client, file_id.dc_id, await client.storage.test_mode()).create(),
                await client.storage.test_mode(),
                is_media=True,
            )
            await media_session.start()

            # Export auth and import in new DC
            for attempt in range(6):
                exported_auth = await client.invoke(
                    raw.functions.auth.ExportAuthorization(dc_id=file_id.dc_id)
                )
                try:
                    await media_session.send(
                        raw.functions.auth.ImportAuthorization(
                            id=exported_auth.id, bytes=exported_auth.bytes
                        )
                    )
                    break
                except AuthBytesInvalid:
                    logging.warning(f"Auth import failed for DC {file_id.dc_id}, retry {attempt+1}/6")
                    continue
            else:
                await media_session.stop()
                raise AuthBytesInvalid(f"Failed to authorize DC {file_id.dc_id}")
        else:
            media_session = Session(
                client,
                file_id.dc_id,
                await client.storage.auth_key(),
                await client.storage.test_mode(),
                is_media=True,
            )
            await media_session.start()

        client.media_sessions[file_id.dc_id] = media_session
        logging.debug(f"Created new media session for DC {file_id.dc_id}")
        return media_session

    @staticmethod
    async def get_location(file_id: FileId) -> Union[
        raw.types.InputPhotoFileLocation,
        raw.types.InputDocumentFileLocation,
        raw.types.InputPeerPhotoFileLocation,
    ]:
        """Return correct Telegram file location object based on file type."""
        if file_id.file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            elif file_id.chat_access_hash == 0:
                peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
            else:
                peer = raw.types.InputPeerChannel(
                    channel_id=utils.get_channel_id(file_id.chat_id),
                    access_hash=file_id.chat_access_hash,
                )
            return raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )

        if file_id.file_type == FileType.PHOTO:
            return raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )

        return raw.types.InputDocumentFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size,
        )

    async def yield_file(
        self,
        file_id: FileId,
        index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ):
        """Yield chunks of a Telegram file for streaming."""
        client = self.client
        work_loads[index] += 1
        logging.debug(f"[{index}] Start streaming | offset={offset} | parts={part_count}")

        media_session = await self.generate_media_session(client, file_id)
        location = await self.get_location(file_id)
        current_part = 1

        try:
            while current_part <= part_count:
                r = await media_session.send(
                    raw.functions.upload.GetFile(location=location, offset=offset, limit=chunk_size)
                )
                if not isinstance(r, raw.types.upload.File):
                    logging.error(f"Unexpected response type at offset {offset}")
                    break

                chunk = r.bytes
                if not chunk:
                    logging.debug("No more chunks received, stopping.")
                    break

                # Slice first and last parts if needed
                if part_count == 1:
                    yield chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    yield chunk[first_part_cut:]
                elif current_part == part_count:
                    yield chunk[:last_part_cut]
                else:
                    yield chunk

                # Prepare next iteration
                offset += chunk_size
                current_part += 1

                del chunk  # free memory for large files

        except (TimeoutError, AttributeError) as e:
            logging.error(f"Stream error at offset {offset}: {e}")
        finally:
            work_loads[index] -= 1
            logging.debug(f"[{index}] Finished streaming {current_part-1}/{part_count} parts")

    async def clean_cache(self) -> None:
        """Periodically clean unused cache entries."""
        while not self._stop:
            await asyncio.sleep(self.clean_timer)
            now = time.time()
            expired = [
                msg_id for msg_id, last_used in self.cache_last_access.items()
                if now - last_used > self.clean_timer
            ]
            for msg_id in expired:
                self.cached_file_ids.pop(msg_id, None)
                self.cache_last_access.pop(msg_id, None)
                logging.debug(f"Cache cleared for message ID {msg_id}")

