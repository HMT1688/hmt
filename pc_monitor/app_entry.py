#!/usr/bin/env python3
"""
PyInstaller frozen entrypoint for PC Monitor Server.

더블클릭 배포용: 기본으로 --auto-token 을 켜고 run.main() 을 호출한다.
커맨드 라인 인자를 넣으면 그 값이 우선이며, 없으면 --auto-token 이 적용된다.
"""
from __future__ import annotations

import sys

# 기본 플래그: 사용자가 인자 없이 실행해도 토큰이 자동 생성되도록
if "--auto-token" not in sys.argv:
    sys.argv.append("--auto-token")

from run import main

if __name__ == "__main__":
    main()
