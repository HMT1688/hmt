#!/usr/bin/env python3
"""
🎨 Simple GUI Drawing App (Tkinter)

기능:
  - 마우스/트랙패드로 자유 그리기
  - 색상 선택 (컬러 피커)
  - 브러시 굵기 슬라이더 (1-40px)
  - 펜 / 지우개 토글
  - 전체 지우기 (Clear)
  - Undo (Ctrl+Z)
  - PNG 로 저장 (파일 대화상자)

실행:
    python drawing_app.py

필요:
    Pillow (pip install Pillow)   — PNG 저장용
"""
from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageDraw

CANVAS_W, CANVAS_H = 960, 600
BG_COLOR = "#ffffff"


class DrawingApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🎨 Simple Drawing")
        self.root.minsize(720, 520)

        self.pen_color = "#111111"
        self.brush_size = tk.IntVar(value=5)
        self.tool = tk.StringVar(value="pen")  # "pen" or "eraser"

        # 그려진 선을 PIL 이미지에도 함께 기록해 PNG 저장 가능하게 함
        self.image = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
        self.draw = ImageDraw.Draw(self.image)

        # 실행 취소용 스트로크 스택: 각 스트로크는 Canvas item id 리스트
        self.undo_stack: list[list[int]] = []
        self._current_stroke: list[int] = []
        self._last_xy: tuple[int, int] | None = None

        self._build_toolbar()
        self._build_canvas()
        self._bind_events()

    # ------------------------------------------------------------------ UI
    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(bar, text="🎨 색상", command=self.choose_color).pack(side=tk.LEFT)

        self.color_swatch = tk.Label(
            bar, width=3, relief="solid", borderwidth=1,
            background=self.pen_color,
        )
        self.color_swatch.pack(side=tk.LEFT, padx=(6, 16))

        ttk.Label(bar, text="굵기").pack(side=tk.LEFT)
        ttk.Scale(
            bar, from_=1, to=40, orient=tk.HORIZONTAL,
            variable=self.brush_size, length=160,
        ).pack(side=tk.LEFT, padx=6)
        self.size_label = ttk.Label(bar, width=3, text=str(self.brush_size.get()))
        self.size_label.pack(side=tk.LEFT)
        self.brush_size.trace_add(
            "write",
            lambda *_: self.size_label.config(text=str(self.brush_size.get())),
        )

        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)

        ttk.Radiobutton(bar, text="✏️ 펜", variable=self.tool, value="pen").pack(side=tk.LEFT)
        ttk.Radiobutton(bar, text="🧽 지우개", variable=self.tool, value="eraser").pack(
            side=tk.LEFT, padx=(6, 16)
        )

        ttk.Button(bar, text="↶ 실행취소", command=self.undo).pack(side=tk.LEFT)
        ttk.Button(bar, text="🗑 전체지우기", command=self.clear).pack(side=tk.LEFT, padx=6)

        ttk.Button(bar, text="💾 PNG 저장", command=self.save_png).pack(side=tk.RIGHT)

    def _build_canvas(self) -> None:
        wrap = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        wrap.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            wrap, width=CANVAS_W, height=CANVAS_H,
            bg=BG_COLOR, highlightthickness=1,
            highlightbackground="#bfbfbf", cursor="pencil",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_events(self) -> None:
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Control-z>", lambda _e: self.undo())
        self.root.bind("<Control-s>", lambda _e: self.save_png())

    # ---------------------------------------------------------------- tools
    def choose_color(self) -> None:
        color = colorchooser.askcolor(color=self.pen_color, title="펜 색상 선택")
        if color and color[1]:
            self.pen_color = color[1]
            self.color_swatch.config(background=self.pen_color)
            self.tool.set("pen")

    def _active_color(self) -> str:
        return BG_COLOR if self.tool.get() == "eraser" else self.pen_color

    # --------------------------------------------------------------- drawing
    def on_press(self, event: tk.Event) -> None:
        self._current_stroke = []
        self._last_xy = (event.x, event.y)
        # 점 하나로 찍히는 경우를 위해 작은 원 하나 그리기
        self._draw_segment(event.x, event.y, event.x, event.y)

    def on_drag(self, event: tk.Event) -> None:
        if self._last_xy is None:
            self._last_xy = (event.x, event.y)
            return
        x0, y0 = self._last_xy
        self._draw_segment(x0, y0, event.x, event.y)
        self._last_xy = (event.x, event.y)

    def on_release(self, _event: tk.Event) -> None:
        if self._current_stroke:
            self.undo_stack.append(self._current_stroke)
            self._current_stroke = []
        self._last_xy = None

    def _draw_segment(self, x0: int, y0: int, x1: int, y1: int) -> None:
        color = self._active_color()
        size = max(1, int(self.brush_size.get()))

        item = self.canvas.create_line(
            x0, y0, x1, y1,
            fill=color, width=size,
            capstyle=tk.ROUND, smooth=True, splinesteps=6,
        )
        self._current_stroke.append(item)

        # PIL 에도 동일하게 그림 (PNG 저장용)
        self.draw.line(
            [(x0, y0), (x1, y1)],
            fill=color, width=size, joint="curve",
        )
        r = size / 2
        self.draw.ellipse([(x0 - r, y0 - r), (x0 + r, y0 + r)], fill=color)
        self.draw.ellipse([(x1 - r, y1 - r), (x1 + r, y1 + r)], fill=color)

    # --------------------------------------------------------------- actions
    def undo(self) -> None:
        if not self.undo_stack:
            return
        stroke = self.undo_stack.pop()
        for item in stroke:
            self.canvas.delete(item)
        # PIL 이미지는 Canvas 에서 재구성하는 대신, Canvas 벡터 기반 재렌더링
        self._rebuild_pil_image()

    def clear(self) -> None:
        if not self.undo_stack:
            return
        if not messagebox.askyesno("전체 지우기", "정말 모두 지우시겠어요?"):
            return
        self.canvas.delete("all")
        self.undo_stack.clear()
        self.image = Image.new("RGB", self._pil_size(), BG_COLOR)
        self.draw = ImageDraw.Draw(self.image)

    def _pil_size(self) -> tuple[int, int]:
        return (self.image.width, self.image.height)

    def _rebuild_pil_image(self) -> None:
        """Canvas 에 남아 있는 모든 아이템을 바탕으로 PIL 이미지를 다시 렌더."""
        w, h = self._pil_size()
        self.image = Image.new("RGB", (w, h), BG_COLOR)
        self.draw = ImageDraw.Draw(self.image)
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            color = self.canvas.itemcget(item, "fill") or "#000000"
            try:
                width = int(float(self.canvas.itemcget(item, "width") or 1))
            except ValueError:
                width = 1
            if len(coords) >= 4:
                pts = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
                self.draw.line(pts, fill=color, width=width, joint="curve")
                r = width / 2
                for x, y in (pts[0], pts[-1]):
                    self.draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)

    def save_png(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
            title="PNG 로 저장",
        )
        if not path:
            return

        # 실제 캔버스 표시 크기에 맞춰 저장 (윈도우 리사이즈 대응)
        try:
            w = int(self.canvas.winfo_width())
            h = int(self.canvas.winfo_height())
            pil_w, pil_h = self._pil_size()
            if (w, h) != (pil_w, pil_h) and w > 0 and h > 0:
                out = self.image.resize((w, h), Image.BILINEAR)
            else:
                out = self.image
            out.save(path, "PNG")
            messagebox.showinfo("저장 완료", f"저장되었습니다:\n{path}")
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))


def main() -> None:
    root = tk.Tk()
    try:
        # macOS/Windows 에서 기본 테마 개선
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    DrawingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
