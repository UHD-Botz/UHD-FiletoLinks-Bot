from pyrogram import Client
from typing import Any, Optional, Union
from pyrogram.types import Message
from pyrogram.file_id import FileId
from pyrogram.raw.types.messages import Messages
from UHDBots.server.exceptions import FileNotFound


def get_media_from_message(message: Union[Message, Messages]) -> Any:
    """Extract the media object from a Telegram message."""
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media
    return None


async def parse_file_id(message: Union[Message, Messages]) -> Optional[FileId]:
    media = get_media_from_message(message)
    if media:
        return FileId.decode(media.file_id)
    return None


async def parse_file_unique_id(message: Union[Message, Messages]) -> Optional[str]:
    media = get_media_from_message(message)
    if media:
        return media.file_unique_id
    return None


async def get_file_ids(client: Client, chat_id: int, id: int) -> FileId:
    """Fetch message and return file metadata inside FileId object."""
    message = await client.get_messages(chat_id, id)

    if not message or message.empty:
        raise FileNotFound(f"No message found for chat_id={chat_id}, id={id}")

    media = get_media_from_message(message)
    if not media:
        raise FileNotFound(f"No media found in message id={id}")

    file_id = await parse_file_id(message)
    file_unique_id = await parse_file_unique_id(message)

    if not file_id:
        raise FileNotFound(f"Unable to decode file_id for message id={id}")

    # Attach extra metadata safely
    setattr(file_id, "file_size", getattr(media, "file_size", 0))
    setattr(file_id, "mime_type", getattr(media, "mime_type", "unknown"))
    setattr(file_id, "file_name", getattr(media, "file_name", f"file_{id}"))
    setattr(file_id, "unique_id", file_unique_id or "")

    return file_id


def get_hash(media_msg: Message) -> str:
    """Return short hash (first 6 chars of file_unique_id)."""
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]


def get_name(media_msg: Message) -> str:
    """Return original filename if exists, else empty string."""
    media = get_media_from_message(media_msg)
    return getattr(media, "file_name", "")


def get_media_file_size(message: Message) -> int:
    """Return file size in bytes (0 if unknown)."""
    media = get_media_from_message(message)
    return getattr(media, "file_size", 0)


def get_extension(media_msg: Message) -> str:
    """Return file extension if filename exists."""
    name = get_name(media_msg)
    return name.split(".")[-1] if "." in name else ""


def is_streamable(media_msg: Message) -> bool:
    """Check if media can be streamed (video/audio)."""
    media = get_media_from_message(media_msg)
    mime = getattr(media, "mime_type", "") or ""
    return mime.startswith("video") or mime.startswith("audio")

