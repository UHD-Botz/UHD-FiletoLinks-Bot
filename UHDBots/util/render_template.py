import jinja2
import urllib.parse
import logging
import aiohttp
from config import *
from UHDBots.bot import UHDBots
from UHDBots.util.human_readable import humanbytes
from UHDBots.util.file_properties import get_file_ids
from UHDBots.server.exceptions import InvalidHash


# Setup Jinja Environment (Cleaner than manually opening files)
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("UHDBots/template"),
    autoescape=True
)


async def render_page(id, secure_hash, src=None):
    try:
        # Fetch file info
        file = await UHDBots.get_messages(int(LOG_CHANNEL), int(id))
        file_data = await get_file_ids(UHDBots, int(LOG_CHANNEL), int(id))

        # Validate secure hash
        if file_data.unique_id[:6] != secure_hash:
            logging.warning(f"Invalid hash for file {id} | given={secure_hash}, expected={file_data.unique_id[:6]}")
            raise InvalidHash

        # Build secure file URL
        src = urllib.parse.urljoin(
            URL,
            f"{id}/{urllib.parse.quote_plus(file_data.file_name)}?hash={secure_hash}"
        )

        # Extract file metadata
        tag = file_data.mime_type.split("/")[0].strip()
        file_size = humanbytes(file_data.file_size)

        # Choose template (req.html for video/audio, dl.html otherwise)
        if tag in ["video", "audio"]:
            template = jinja_env.get_template("req.html")
        else:
            template = jinja_env.get_template("dl.html")
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(src) as u:
                        if u.status == 200 and u.headers.get("Content-Length"):
                            file_size = humanbytes(int(u.headers.get("Content-Length")))
            except Exception as e:
                logging.error(f"Failed to fetch file size from {src}: {e}")

        # Replace underscores with spaces for a nicer display
        file_name = file_data.file_name.replace("_", " ")

        # Render final HTML
        return template.render(
            file_name=file_name,
            file_url=src,
            file_size=file_size,
            file_unique_id=file_data.unique_id,
            mime_type=file_data.mime_type,
            is_streamable=(tag in ["video", "audio"])
        )

    except InvalidHash:
        template = jinja_env.get_template("error.html")
        return template.render(
            error_message="Invalid or expired link. Please regenerate a new link."
        )

    except Exception as e:
        logging.error(f"Error rendering page for ID {id}: {e}")
        template = jinja_env.get_template("error.html")
        return template.render(
            error_message="Something went wrong while processing your request."
        )


