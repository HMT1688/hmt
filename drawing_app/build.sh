#!/usr/bin/env bash
#
# PyInstaller 로 SimpleDrawing 단일 실행파일을 빌드한다.
#   ./build.sh            → 현재 플랫폼용 onefile 빌드 (dist/SimpleDrawing)
#   ./build.sh --clean    → 빌드 산출물 정리
#
# macOS 는 .app 번들, Windows 는 .exe, Linux 는 ELF 바이너리가 생성된다.

set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf build dist __pycache__ SimpleDrawing.spec
  echo "cleaned."
  exit 0
fi

# venv 가 있으면 그걸 사용, 아니면 시스템 파이썬 사용
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

echo "🔧 using: $($PY -V)"
$PY -m pip install --quiet --upgrade pyinstaller Pillow

EXTRA=()
case "$(uname -s)" in
  Darwin*)  EXTRA+=(--windowed --osx-bundle-identifier com.hmt.simpledrawing) ;;
  MINGW*|MSYS*|CYGWIN*) EXTRA+=(--windowed) ;;
esac

echo "📦 building SimpleDrawing…"
$PY -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name SimpleDrawing \
  "${EXTRA[@]}" \
  drawing_app.py

echo
echo "✅ build complete → dist/"
ls -lh dist/ | sed 's/^/   /'
