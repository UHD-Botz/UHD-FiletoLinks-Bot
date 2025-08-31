import re, math, logging, secrets, mimetypes
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from config import *
from UHDBots.bot import multi_clients, work_loads, UHDBots
from UHDBots.server.exceptions import FIleNotFound, InvalidHash
from UHDBots import StartTime, __version__
from UHDBots.util.custom_dl import ByteStreamer
from UHDBots.util.time_format import get_readable_time
from UHDBots.util.render_template import render_page

routes = web.RouteTableDef()
_stream_cache = {}

@routes.get("/", allow_head=True)
async def home(request: web.Request):
    return web.json_response({"status": "running", "service": "UHD-FiletoLinks"})

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash, file_id = match.group(1), int(match.group(2))
        else:
            file_id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(text=await render_page(file_id, secure_hash), content_type="text/html")
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        logging.warning("Client connection dropped")
    except Exception as e:
        logging.exception("Unexpected error in watch_handler")
        raise web.HTTPInternalServerError(text="Internal Server Error")

@routes.get(r"/{path:\S+}", allow_head=True)
async def file_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash, file_id = match.group(1), int(match.group(2))
        else:
            file_id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await _stream_file(request, file_id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        logging.warning("Client connection dropped")
    except Exception as e:
        logging.exception("Unexpected error in file_stream_handler")
        raise web.HTTPInternalServerError(text="Internal Server Error")

async def _stream_file(request: web.Request, file_id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    client_index = min(work_loads, key=work_loads.get)
    active_client = multi_clients[client_index]

    if MULTI_CLIENT:
        logging.info(f"Client {client_index} serving request from {request.remote}")

    tg_client = _stream_cache.get(active_client)
    if not tg_client:
        tg_client = ByteStreamer(active_client)
        _stream_cache[active_client] = tg_client

    file = await tg_client.get_file_properties(file_id)

    if file.unique_id[:6] != secure_hash:
        logging.error(f"Invalid hash for file {file_id}")
        raise InvalidHash

    file_size = file.file_size
    if range_header:
        start, end = range_header.replace("bytes=", "").split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
    else:
        start = request.http_range.start or 0
        end = (request.http_range.stop or file_size) - 1

    if (end > file_size) or (start < 0) or (end < start):
        return web.Response(
            status=416,
            text="416: Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    chunk_size = 1024 * 1024
    end = min(end, file_size - 1)
    offset = start - (start % chunk_size)
    first_cut = start - offset
    last_cut = end % chunk_size + 1
    total_length = end - start + 1
    parts = math.ceil(end / chunk_size) - math.floor(offset / chunk_size)

    body = tg_client.yield_file(file, client_index, offset, first_cut, last_cut, parts, chunk_size)

    mime_type = file.mime_type or "application/octet-stream"
    file_name = file.file_name or f"{secrets.token_hex(2)}.bin"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": mime_type,
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(total_length),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes"
        }
    )
