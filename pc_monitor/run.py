#!/usr/bin/env python3
"""
🚀 PC Monitor 통합 실행 엔트리
- 기본: LAN 전용으로 FastAPI 서버 실행
- --remote: 서버 + Cloudflare Tunnel 동시 실행 (공개 URL 자동 발급)

사용 예:
    python run.py
    MONITOR_USER=me MONITOR_PASS=pw python run.py --remote
"""
from __future__ import annotations

import argparse
import logging
import os
import secrets
import signal
import sys
import threading
import time
from urllib.parse import quote

logging.basicConfig(
    level=logging.INFO,
    format="🚀 [%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pc_monitor.run")


def _banner(lines):
    width = max(len(s) for s in lines) + 4
    bar = "─" * width
    print("\n┌" + bar + "┐")
    for s in lines:
        print("│  " + s.ljust(width - 4) + "  │")
    print("└" + bar + "┘\n")


def _print_qr(url: str) -> None:
    """서버 접속 URL 을 터미널 ASCII QR 로 표시. qrcode 패키지가 없으면 조용히 스킵."""
    try:
        import qrcode
    except ImportError:
        log.info("(QR 코드 표시하려면  pip install qrcode  실행)")
        return
    qr = qrcode.QRCode(border=1, box_size=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(url)
    qr.make(fit=True)
    print("📷 폰 카메라로 스캔하세요:\n")
    qr.print_ascii(invert=True)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="PC Monitor launcher")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--remote", action="store_true",
                        help="Cloudflare Tunnel 로 공개 URL 생성")
    parser.add_argument("--auto-token", action="store_true",
                        help="MONITOR_TOKEN 미설정 시 랜덤 토큰 생성")
    args = parser.parse_args()

    # 토큰 자동 생성 옵션
    if args.auto_token and not os.environ.get("MONITOR_TOKEN"):
        os.environ["MONITOR_TOKEN"] = secrets.token_urlsafe(16)
        log.info("generated MONITOR_TOKEN=%s", os.environ["MONITOR_TOKEN"])

    # 보안 경고
    if args.remote:
        if not (os.environ.get("MONITOR_USER") and os.environ.get("MONITOR_PASS")):
            log.warning("⚠️  --remote 사용 시 MONITOR_USER/MONITOR_PASS 설정을 강력 권장합니다.")
        if not os.environ.get("MONITOR_TOKEN"):
            log.warning("⚠️  MONITOR_TOKEN 이 비어 있습니다. --auto-token 또는 env 설정을 고려하세요.")

    # 서버를 백그라운드 스레드에서 실행 (uvicorn 은 블로킹)
    import uvicorn
    from server import app  # noqa: E402

    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # 서버 기동 대기
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)

    token = os.environ.get("MONITOR_TOKEN", "")
    qs = f"?token={quote(token)}" if token else ""

    tunnel = None
    if args.remote:
        from tunnel import CloudflareTunnel, has_cloudflared
        if not has_cloudflared():
            log.error("cloudflared 미설치 — --remote 실행 불가. README 참고.")
            sys.exit(1)
        tunnel = CloudflareTunnel(port=args.port)
        tunnel.start()
        url = tunnel.wait_for_url(timeout=40)
        if url:
            full = f"{url}/{qs}"
            _banner([
                "📱 PC Monitor is live!",
                f"Public URL : {full}",
                "아이디/비밀번호: MONITOR_USER / MONITOR_PASS",
            ])
            _print_qr(full)
        else:
            log.error("Cloudflare Tunnel URL 을 확보하지 못했습니다.")
    else:
        from server import _get_lan_ip  # noqa: E402
        ip = _get_lan_ip()
        full = f"http://{ip}:{args.port}/{qs}"
        _banner([
            "📺 PC Monitor (LAN)",
            f"LAN URL : {full}",
        ])
        _print_qr(full)

    # 메인 스레드는 신호 대기
    stop_evt = threading.Event()

    def _shutdown(*_):
        log.info("shutting down…")
        stop_evt.set()

    signal.signal(signal.SIGINT, _shutdown)
    try:
        signal.signal(signal.SIGTERM, _shutdown)
    except Exception:
        pass

    try:
        while not stop_evt.is_set() and server_thread.is_alive():
            stop_evt.wait(0.5)
    finally:
        if tunnel:
            tunnel.stop()
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
