#!/usr/bin/env bash
#
# PCMonitorServer 단일 실행파일 빌드 (PyInstaller)
#   ./build.sh            → dist/PCMonitorServer(.exe)
#   ./build.sh --clean    → 산출물 정리
#
# macOS/Windows 에선 --noconsole 대신 --console 로 남겨서 QR 코드와 로그를 볼 수 있게 한다.

set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf build dist __pycache__ PCMonitorServer.spec
  echo "cleaned."
  exit 0
fi

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PY=".venv/Scripts/python.exe"
else
  PY="${PYTHON:-python3}"
fi

echo "🔧 using: $($PY -V)"
$PY -m pip install --quiet --upgrade pyinstaller
$PY -m pip install --quiet -r requirements.txt

# PyInstaller 의 --add-data 구분자는 Windows 는 ';', 그 외는 ':'
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) SEP=';' ;;
  *)                    SEP=':' ;;
esac

echo "📦 building PCMonitorServer…"
$PY -m PyInstaller \
  --noconfirm --clean --onefile \
  --name PCMonitorServer \
  --console \
  --add-data "templates${SEP}templates" \
  --hidden-import uvicorn.lifespan.on \
  --hidden-import uvicorn.lifespan.off \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.http.h11_impl \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.protocols.websockets.websockets_impl \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.loops.asyncio \
  app_entry.py

echo
echo "✅ build complete → dist/"
ls -lh dist/ | sed 's/^/   /'
