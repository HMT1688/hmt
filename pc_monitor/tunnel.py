#!/usr/bin/env python3
"""
☁️ Cloudflare Tunnel Launcher
`cloudflared tunnel --url http://localhost:<port>` 를 서브프로세스로 실행하고
공개 URL(https://*.trycloudflare.com) 을 stdout 에서 파싱해 반환한다.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Callable, Optional

log = logging.getLogger("pc_monitor.tunnel")

_TRYCF_RE = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com", re.IGNORECASE)

_INSTALL_HINT = """\
cloudflared 바이너리가 필요합니다.
  • macOS    : brew install cloudflared
  • Windows  : winget install --id Cloudflare.cloudflared
  • Linux    : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
설치 후 다시 실행해 주세요.
"""


def has_cloudflared() -> bool:
    return shutil.which("cloudflared") is not None


class CloudflareTunnel:
    def __init__(self, port: int, on_url: Optional[Callable[[str], None]] = None):
        self.port = port
        self.on_url = on_url
        self.proc: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self._reader: Optional[threading.Thread] = None
        self._stopped = False

    def start(self) -> None:
        if not has_cloudflared():
            print(_INSTALL_HINT, file=sys.stderr)
            raise RuntimeError("cloudflared not found in PATH")

        cmd = [
            "cloudflared", "tunnel",
            "--no-autoupdate",
            "--url", f"http://localhost:{self.port}",
        ]
        log.info("launching: %s", " ".join(cmd))
        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
        )
        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()

    def _read_output(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            log.info("cloudflared | %s", line)
            if not self.public_url:
                m = _TRYCF_RE.search(line)
                if m:
                    self.public_url = m.group(0)
                    if self.on_url:
                        try:
                            self.on_url(self.public_url)
                        except Exception as e:
                            log.warning("on_url callback failed: %s", e)

    def wait_for_url(self, timeout: float = 30.0) -> Optional[str]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.public_url:
                return self.public_url
            if self.proc and self.proc.poll() is not None:
                return None
            time.sleep(0.2)
        return self.public_url

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            except Exception as e:
                log.warning("failed to stop cloudflared: %s", e)
