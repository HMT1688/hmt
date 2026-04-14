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
