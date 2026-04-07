import re, math, logging, secrets, mimetypes, asyncio, base64
from aiohttp import web
from config import *
from UHDBots.bot import multi_clients, work_loads, UHDBots
from UHDBots.server.exceptions import FileNotFound, InvalidHash
from UHDBots.util.custom_dl import ByteStreamer
from UHDBots.util.render_template import render_page

_0x_r = web.RouteTableDef()
_0x_c = {}

def _0x_dec(_0x_s):
    return base64.b64decode(_0x_s).decode('utf-8')

@_0x_r.get("/", allow_head=True)
async def _0x_h(_0x_req):
    return web.json_response({_0x_dec('c3RhdHVz'): _0x_dec('YWN0aXZl'), _0x_dec('c2VydmljZQ=='): _0x_dec('VUhEIEJvdHMgUHJlbWl1bQ==')})

@_0x_r.get(r"/watch/{path:\S+}", allow_head=True)
async def _0x_w(_0x_req):
    try:
        _0x_p = _0x_req.match_info["path"]
        _0x_m = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", _0x_p)
        _0x_h, _0x_f = (_0x_m.group(1), int(_0x_m.group(2))) if _0x_m else (_0x_req.rel_url.query.get(_0x_dec('aGFzaA==')), int(re.search(r"(\d+)", _0x_p).group(1)))
        return web.Response(text=await render_page(_0x_f, _0x_h), content_type=_0x_dec('dGV4dC9odG1s'))
    except Exception:
        raise web.HTTPNotFound(text=_0x_dec('SW52YWxpZCBMaW5r'))

@_0x_r.get(r"/{path:\S+}", allow_head=True)
async def _0x_fs(_0x_req):
    try:
        _0x_p = _0x_req.match_info["path"]
        _0x_m = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", _0x_p)
        _0x_h, _0x_f = (_0x_m.group(1), int(_0x_m.group(2))) if _0x_m else (_0x_req.rel_url.query.get(_0x_dec('aGFzaA==')), int(re.search(r"(\d+)", _0x_p).group(1)))
        return await _0x_sf(_0x_req, _0x_f, _0x_h)
    except Exception as _0x_e:
        logging.error(f"ERR: {_0x_e}")
        raise web.HTTPInternalServerError(text=_0x_dec('U3RyZWFtIEVycm9y'))

async def _0x_sf(_0x_rq, _0x_fid, _0x_hsh):
    _0x_rh = _0x_rq.headers.get(_0x_dec('UmFuZ2U='), 0)
    _0x_ci = min(work_loads, key=work_loads.get)
    _0x_ac = multi_clients[_0x_ci]
    _0x_tc = _0x_c.get(_0x_ac) or ByteStreamer(_0x_ac)
    _0x_c[_0x_ac] = _0x_tc
    _0x_f = await _0x_tc.get_file_properties(_0x_fid)
    if _0x_f.unique_id[:6] != _0x_hsh: raise InvalidHash
    
    _0x_fsz = _0x_f.file_size
    _0x_st = _0x_rq.http_range.start or 0
    _0x_en = (_0x_rq.http_range.stop or _0x_fsz) - 1

    # --- ENCRYPTED RENAME & CHUNK LOGIC ---
    _0x_t = _0x_dec('QFVIREJvdHM=') # @UHDBots
    _0x_on = _0x_f.file_name or f"{secrets.token_hex(2)}.bin"
    _0x_fn = f"[{_0x_t}] {_0x_on.replace('_', ' ').replace('-', ' ')}" if _0x_t not in _0x_on else _0x_on

    _0x_cs = 1048576 # 1MB Fix
    _0x_os = _0x_st - (_0x_st % _0x_cs)
    _0x_tl = _0x_en - _0x_st + 1
    _0x_pr = math.ceil(_0x_en / _0x_cs) - math.floor(_0x_os / _0x_cs)

    _0x_bd = _0x_tc.yield_file(_0x_f, _0x_ci, _0x_os, _0x_st - _0x_os, _0x_en % _0x_cs + 1, _0x_pr, _0x_cs)

    return web.Response(
        status=206 if _0x_rh else 200,
        body=_0x_bd,
        headers={
            _0x_dec('Q29udGVudC1UeXBl'): _0x_f.mime_type or _0x_dec('dmlkZW8vbXA0'),
            _0x_dec('Q29udGVudC1SYW5nZQ=='): f"bytes {_0x_st}-{_0x_en}/{_0x_fsz}",
            _0x_dec('Q29udGVudC1MZW5ndGg='): str(_0x_tl),
            _0x_dec('Q29udGVudC1EaXNwb3NpdGlvbg=='): f'attachment; filename="{_0x_fn}"',
            _0x_dec('QWNjZXB0LVJhbmdlcw=='): _0x_dec('Ynl0ZXM='),
            _0x_dec('QWNjZXNzLUNvbnRyb2wtQWxsb3ctT3JpZ2lu'): "*"
        }
    )
    
# Yeh line purane system se connect karegi
routes = _0x_r
