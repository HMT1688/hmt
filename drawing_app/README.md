# 🎨 Simple Drawing App

Tkinter 로 만든 가벼운 GUI 드로잉 앱입니다.

## 기능
- 마우스로 자유 그리기
- 컬러 피커로 펜 색상 변경
- 브러시 굵기 슬라이더 (1-40px)
- 펜 / 지우개 토글
- 실행 취소 (Ctrl+Z)
- 전체 지우기
- PNG 로 저장 (Ctrl+S)

## 설치 & 실행
```bash
cd drawing_app
pip install -r requirements.txt
python drawing_app.py
```

> Tkinter 는 파이썬 표준 라이브러리에 포함돼 있습니다.
> 일부 Linux 배포판은 `sudo apt install python3-tk` 가 필요할 수 있습니다.

## 단축키
| 동작 | 키 |
|------|----|
| 실행 취소 | `Ctrl + Z` |
| PNG 저장 | `Ctrl + S` |

## 🛠 실행파일로 빌드 (PyInstaller)

스크립트 하나로 플랫폼별 단일 실행파일을 만들 수 있습니다.

```bash
cd drawing_app
./build.sh          # Linux / macOS
# Windows (git-bash / MSYS):  bash build.sh
```

- Linux  → `dist/SimpleDrawing` (ELF)
- macOS  → `dist/SimpleDrawing` + `.app` 번들 (`--windowed`)
- Windows → `dist/SimpleDrawing.exe` (`--windowed`)

`./build.sh --clean` 으로 `build/` `dist/` `*.spec` 을 정리할 수 있습니다.

> ⚠️ PyInstaller 는 **빌드한 OS/아키텍처용 바이너리만 생성**합니다.
> 예: Windows .exe 가 필요하면 Windows 에서 `build.sh` 를 실행하세요.

### GitHub Actions 로 3대 OS 동시 빌드

`.github/workflows/build-drawing-app.yml` 워크플로가 Linux / macOS / Windows
러너에서 동시에 빌드하고 산출물을 업로드합니다.

- **자동 실행**: `drawing_app/**` 변경이 브랜치에 push 되거나 PR 이 열릴 때
- **수동 실행**: GitHub 의 Actions 탭 → "Build Drawing App" → **Run workflow**

산출 아티팩트:
- `SimpleDrawing-linux-x86_64`
- `SimpleDrawing-macos-universal`
- `SimpleDrawing-windows-x86_64`

Actions 실행이 끝나면 해당 Run 페이지 아래의 **Artifacts** 섹션에서 각
파일을 다운로드할 수 있습니다(보관 기간 14일).
