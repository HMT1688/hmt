# 📱 PC Screen Mobile Monitor

내 PC 화면을 휴대폰 브라우저에서 실시간으로 모니터링할 수 있는 간단한 앱입니다.
같은 Wi-Fi 에서 쓰는 **LAN 모드**와 외출 중에도 접속 가능한
**원거리(Cloudflare Tunnel) 모드** 를 모두 지원합니다.

## ✨ 기능
- mss 로 PC 전체/특정 모니터를 캡처 → JPEG 로 WebSocket 스트리밍
- 반응형 모바일 뷰어 (FPS / 품질 / 최대 폭 / 모니터 선택 / 풀스크린)
- Basic Auth + URL 토큰 **이중 인증**
- Cloudflare Tunnel 자동 기동으로 공유기 포트포워딩 없이 외부 접속
- **📷 서버 시작 시 접속 URL QR 코드 터미널 출력** — 폰 카메라로 스캔 한 번에 접속
- 백그라운드 탭 감지 / 자동 재연결

## 📦 설치
```bash
cd pc_monitor
python -m pip install -r requirements.txt
```

원거리 모드(`--remote`) 를 사용하려면 `cloudflared` 바이너리가 필요합니다.
- macOS : `brew install cloudflared`
- Windows : `winget install --id Cloudflare.cloudflared`
- Linux : <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>

## 🚀 실행

### LAN 에서만 사용 (집 안에서 본인 Wi-Fi)
```bash
MONITOR_USER=me MONITOR_PASS=pw \
MONITOR_TOKEN=$(python -c "import secrets;print(secrets.token_urlsafe(12))") \
python run.py
```
터미널에 뜨는 `http://<PC-IP>:8000/?token=...` 를 같은 Wi-Fi 의 폰으로 엽니다.

### 원거리(외부 인터넷)
```bash
MONITOR_USER=me MONITOR_PASS=pw python run.py --remote --auto-token
```
몇 초 후 다음처럼 공개 URL 이 출력됩니다:
```
┌─────────────────────────────────────────────┐
│  📱 PC Monitor is live!                     │
│  Public URL : https://xxxx.trycloudflare.com/?token=... │
│  아이디/비밀번호: MONITOR_USER / MONITOR_PASS │
└─────────────────────────────────────────────┘
```
폰에서 해당 URL 을 열면 Basic Auth 창이 뜨고, 로그인 후 화면이 스트리밍됩니다.

## ⚙️ 환경 변수

| 이름 | 기본값 | 설명 |
|------|--------|------|
| `MONITOR_USER`       | _(없음)_ | Basic Auth 아이디 |
| `MONITOR_PASS`       | _(없음)_ | Basic Auth 비밀번호 |
| `MONITOR_TOKEN`      | _(없음)_ | URL 토큰 (`?token=`) |
| `MONITOR_FPS`        | `8`     | 기본 프레임레이트 |
| `MONITOR_QUALITY`    | `60`    | JPEG 품질 (20-95) |
| `MONITOR_MAX_WIDTH`  | `1280`  | 리사이즈 최대 폭 |
| `MONITOR_INDEX`      | `1`     | 기본 모니터 인덱스 (0 = 전체) |

## 🔒 보안 주의
- Cloudflare Tunnel URL 은 공개입니다. **반드시** Basic Auth 와 토큰을 모두 설정하세요.
- 장기간 상시 운영이 필요하면 Cloudflare Access + 고정 터널(named tunnel) 사용을 권장합니다.
- 이 앱은 개인 용도/임시 시청 목적으로 설계되어 있으며, 암호는 Basic Auth 특성상 HTTPS 상에서만 안전합니다.

## 🪟 Windows 원클릭 실행 (.exe)

Python 설치 없이 쓰고 싶으면 PyInstaller 로 단일 실행파일을 만들면 됩니다.

### GitHub Actions 에서 자동 빌드
`.github/workflows/build-pc-monitor.yml` 가 `pc_monitor/**` 변경 시마다
Windows / macOS / Linux 3대 OS 빌드를 돌리고 아래 아티팩트를 업로드합니다:
- `PCMonitorServer-windows-x86_64` → `PCMonitorServer.exe`
- `PCMonitorServer-macos-universal` → `PCMonitorServer`
- `PCMonitorServer-linux-x86_64` → `PCMonitorServer`

Actions 탭 → "Build PC Monitor Server" → 최근 Run 의 **Artifacts** 에서 다운로드.

### 로컬에서 직접 빌드
```bash
cd pc_monitor
./build.sh          # 현재 OS 용
./build.sh --clean  # 산출물 정리
```

### 사용 흐름 (Windows)
1. `PCMonitorServer.exe` 다운로드
2. **더블클릭** (필요 시 "추가 정보 ▸ 실행")
3. 창에 배너 + QR 코드가 뜬다
4. 폰 카메라로 QR 스캔 → 자동 생성된 토큰으로 바로 접속
5. (선택) 로그인 프롬프트가 뜨면 미리 설정한 `MONITOR_USER`/`MONITOR_PASS` 입력

> Basic Auth 자격증명은 환경변수로 전달하거나, exe 와 같은 폴더에 `.env` 파일을 두어 지정할 수 있습니다. 예:
> ```
> MONITOR_USER=me
> MONITOR_PASS=strongpw
> ```

## 📁 파일
```
pc_monitor/
├── server.py              # FastAPI 본체 (캡처/스트림/인증)
├── run.py                 # 통합 실행 엔트리 (LAN/Remote, QR 출력)
├── app_entry.py           # PyInstaller frozen entrypoint (--auto-token 기본)
├── tunnel.py              # Cloudflare Tunnel 런처
├── templates/index.html   # 모바일 뷰어
├── build.sh               # PyInstaller onefile 빌드 스크립트
├── requirements.txt
└── README.md
```
