#!/usr/bin/env python3
"""
📱 PC Screen → Mobile Monitor
- mss 로 PC 화면 캡처
- FastAPI + WebSocket 으로 JPEG 프레임 실시간 전송
- 모바일 브라우저에서 접속하여 실시간 시청
- Basic Auth + URL 토큰 이중 인증 지원

실행 예:
    MONITOR_USER=me MONITOR_PASS=pw MONITOR_TOKEN=xyz python server.py
모바일에서 접속:
    http://<PC의 LAN IP>:8000/?token=xyz   (아이디/비밀번호 프롬프트)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import io
import logging
import os
import secrets
import socket
import sys
from pathlib import Path
from typing import Optional

import mss
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="📺 [%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pc_monitor")

# PyInstaller 로 frozen 될 경우 리소스는 _MEIPASS 에 풀린다.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="PC Screen Mobile Monitor", version="1.0.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

TOKEN = os.getenv("MONITOR_TOKEN", "").strip()
BASIC_USER = os.getenv("MONITOR_USER", "").strip()
BASIC_PASS = os.getenv("MONITOR_PASS", "").strip()

DEFAULT_FPS = float(os.getenv("MONITOR_FPS", "8"))
DEFAULT_QUALITY = int(os.getenv("MONITOR_QUALITY", "60"))
DEFAULT_MAX_WIDTH = int(os.getenv("MONITOR_MAX_WIDTH", "1280"))
DEFAULT_MONITOR_INDEX = int(os.getenv("MONITOR_INDEX", "1"))  # 1 = primary


# ---------------------------------------------------------------------------
# 인증
# ---------------------------------------------------------------------------
def _check_token(provided: Optional[str]) -> bool:
    if not TOKEN:
        return True
    return secrets.compare_digest(provided or "", TOKEN)


def _check_basic(header: Optional[str]) -> bool:
    """Basic Auth 자격증명이 맞으면 True. 설정이 비어 있으면 항상 True."""
    if not (BASIC_USER and BASIC_PASS):
        return True
    if not header or not header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8", "ignore")
    except Exception:
        return False
    if ":" not in decoded:
        return False
    user, pw = decoded.split(":", 1)
    return secrets.compare_digest(user, BASIC_USER) and secrets.compare_digest(pw, BASIC_PASS)


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """HTTP 경로 전역에 Basic Auth 적용 (WebSocket 은 엔드포인트에서 별도 처리)."""

    async def dispatch(self, request: Request, call_next):
        if not (BASIC_USER and BASIC_PASS):
            return await call_next(request)
        if _check_basic(request.headers.get("authorization")):
            return await call_next(request)
        return Response(
            status_code=401,
            content="Authentication required.",
            headers={"WWW-Authenticate": 'Basic realm="PC Monitor"'},
        )


app.add_middleware(BasicAuthMiddleware)


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------
def _get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _capture_jpeg(
    sct: "mss.base.MSSBase",
    monitor_index: int,
    max_width: int,
    quality: int,
) -> bytes:
    monitors = sct.monitors
    idx = monitor_index if 0 <= monitor_index < len(monitors) else 1
    shot = sct.grab(monitors[idx])
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    if max_width and img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, max(1, int(img.height * ratio)))
        img = img.resize(new_size, Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=False)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 라우트
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    token = request.query_params.get("token")
    if not _check_token(token):
        return HTMLResponse(
            "<h1>🔒 Access Denied</h1><p>Valid <code>?token=...</code> required.</p>",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "token": token or "",
            "default_fps": DEFAULT_FPS,
            "default_quality": DEFAULT_QUALITY,
            "default_max_width": DEFAULT_MAX_WIDTH,
            "default_monitor": DEFAULT_MONITOR_INDEX,
        },
    )


@app.get("/monitors")
async def list_monitors(token: Optional[str] = None):
    if not _check_token(token):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    with mss.mss() as sct:
        return {
            "monitors": [
                {
                    "index": i,
                    "width": m["width"],
                    "height": m["height"],
                    "left": m["left"],
                    "top": m["top"],
                }
                for i, m in enumerate(sct.monitors)
            ]
        }


@app.get("/snapshot")
async def snapshot(
    token: Optional[str] = None,
    monitor: int = DEFAULT_MONITOR_INDEX,
    max_width: int = DEFAULT_MAX_WIDTH,
    quality: int = DEFAULT_QUALITY,
):
    if not _check_token(token):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    with mss.mss() as sct:
        data = _capture_jpeg(sct, monitor, max_width, quality)
    return Response(content=data, media_type="image/jpeg")


@app.websocket("/ws")
async def stream(ws: WebSocket):
    # WebSocket 은 HTTP 미들웨어를 지나기는 하지만, 자격증명이 없을 경우
    # 브라우저는 Basic Auth 를 자동 전송해 통과됨. 그래도 방어적으로 재확인.
    if not _check_basic(ws.headers.get("authorization")):
        await ws.close(code=4401)
        return

    token = ws.query_params.get("token")
    if not _check_token(token):
        await ws.close(code=4401)
        return

    try:
        fps = float(ws.query_params.get("fps", DEFAULT_FPS))
        quality = int(ws.query_params.get("quality", DEFAULT_QUALITY))
        max_width = int(ws.query_params.get("max_width", DEFAULT_MAX_WIDTH))
        monitor_index = int(ws.query_params.get("monitor", DEFAULT_MONITOR_INDEX))
    except ValueError:
        await ws.close(code=4400)
        return

    fps = max(1.0, min(fps, 30.0))
    quality = max(20, min(quality, 95))
    max_width = max(320, min(max_width, 3840))
    interval = 1.0 / fps

    await ws.accept()
    log.info(
        "client connected: fps=%.1f quality=%d max_w=%d monitor=%d",
        fps, quality, max_width, monitor_index,
    )

    loop = asyncio.get_event_loop()
    try:
        with mss.mss() as sct:
            while True:
                frame = await loop.run_in_executor(
                    None, _capture_jpeg, sct, monitor_index, max_width, quality
                )
                await ws.send_bytes(frame)
                await asyncio.sleep(interval)
    except WebSocketDisconnect:
        log.info("client disconnected")
    except Exception as e:
        log.exception("stream error: %s", e)
        try:
            await ws.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="PC Screen Mobile Monitor")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    ip = _get_lan_ip()
    qs = f"?token={TOKEN}" if TOKEN else ""
    log.info("Starting PC Monitor on http://%s:%d", args.host, args.port)
    log.info("📱 LAN URL:  http://%s:%d/%s", ip, args.port, qs)
    if not TOKEN:
        log.warning("MONITOR_TOKEN is empty — anyone reaching this port can access.")
    if not (BASIC_USER and BASIC_PASS):
        log.warning("MONITOR_USER/MONITOR_PASS not set — no Basic Auth layer!")

    import uvicorn
    uvicorn.run(
        "server:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
