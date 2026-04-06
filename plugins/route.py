import re, math, logging, secrets, mimetypes, asyncio
from aiohttp import web
from config import *
from UHDBots.bot import multi_clients, work_loads, UHDBots
from UHDBots.server.exceptions import FileNotFound, InvalidHash
from UHDBots.util.custom_dl import ByteStreamer
from UHDBots.util.render_template import render_page

routes = web.RouteTableDef()
_stream_cache = {}

@routes.get("/", allow_head=True)
async def home(request: web.Request):
    return web.json_response({"status": "active", "service": "UHD Bots Premium"})

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        secure_hash, file_id = (match.group(1), int(match.group(2))) if match else (request.rel_url.query.get("hash"), int(re.search(r"(\d+)", path).group(1)))
        return web.Response(text=await render_page(file_id, secure_hash), content_type="text/html")
    except Exception:
        raise web.HTTPNotFound(text="Invalid Link")

@routes.get(r"/{path:\S+}", allow_head=True)
async def file_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        secure_hash, file_id = (match.group(1), int(match.group(2))) if match else (request.rel_url.query.get("hash"), int(re.search(r"(\d+)", path).group(1)))
        return await _stream_file(request, file_id, secure_hash)
    except Exception:
        raise web.HTTPInternalServerError(text="Stream Error")

async def _stream_file(request: web.Request, file_id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    client_index = min(work_loads, key=work_loads.get)
    active_client = multi_clients[client_index]

    # Caching Streamer for speed
    tg_client = _stream_cache.get(active_client) or ByteStreamer(active_client)
    _stream_cache[active_client] = tg_client

    file = await tg_client.get_file_properties(file_id)
    if file.unique_id[:6] != secure_hash: raise InvalidHash

    file_size = file.file_size
    start = request.http_range.start or 0
    end = (request.http_range.stop or file_size) - 1

    # Chunk Optimization for Fast Playback
    chunk_size = 2 * 1024 * 1024 # 2MB Chunks for better speed
    offset = start - (start % chunk_size)
    total_length = end - start + 1

    body = tg_client.yield_file(file, client_index, offset, start - offset, end % chunk_size + 1, math.ceil(end / chunk_size) - math.floor(offset / chunk_size), chunk_size)

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": file.mime_type or "video/mp4",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(total_length),
            "Content-Disposition": f'attachment; filename="{file.file_name}"',
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*" # Fast load for web players
        }
    )
