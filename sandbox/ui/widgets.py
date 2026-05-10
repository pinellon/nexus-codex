"""Widgets Canvas reutilizaveis do NEXUS."""

from __future__ import annotations

import math
import tkinter as tk
from collections import deque
from ui.theme import C, F


class SoundBus:
    """Feedback sonoro leve, sem arquivos externos."""

    enabled = True

    _tones = {
        "hover": (880, 18),
        "click": (1200, 28),
        "success": (1320, 55),
        "info": (980, 35),
        "warning": (620, 70),
        "error": (330, 95),
        "start": (1040, 45),
        "stop": (520, 55),
    }

    @classmethod
    def play(cls, name: str = "click"):
        if not cls.enabled:
            return
        try:
            import winsound
            freq, duration = cls._tones.get(name, cls._tones["click"])
            winsound.Beep(freq, duration)
        except Exception:
            try:
                root = tk._default_root
                if root:
                    root.bell()
            except Exception:
                pass


class AmbientScanner(tk.Canvas):
    """Linha de varredura e particulas discretas para dar vida ao painel."""

    def __init__(self, parent, height: int = 60, bg: str | None = None, **kwargs):
        super().__init__(parent, height=height, bg=bg or C["panel"], highlightthickness=0, **kwargs)
        self._height = height
        self._phase = 0
        self._running = False
        self.bind("<Configure>", lambda _e: self._draw())

    def start(self):
        if self._running:
            return
        self._running = True
        self._animate()

    def stop(self):
        self._running = False

    def _animate(self):
        if not self._running:
            return
        self._phase = (self._phase + 4) % max(1, self.winfo_width() + 80)
        self._draw()
        self.after(45, self._animate)

    def _draw(self):
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height() or self._height)
        for y in range(8, height, 14):
            self.create_line(0, y, width, y, fill=C["border"], width=1)
        x = self._phase - 40
        self.create_line(x, 0, x + 38, height, fill=C["cyan"], width=2)
        self.create_line(x - 15, 0, x + 8, height, fill=C["cyan_dim"], width=1)
        for i in range(10):
            px = (self._phase * (i + 2) + i * 73) % width
            py = 8 + ((i * 17 + self._phase // 3) % max(12, height - 12))
            color = C["green"] if i % 3 == 0 else C["cyan_dim"]
            self.create_rectangle(px, py, px + 2, py + 2, fill=color, outline="")


class StatusTicker:
    """Anima textos curtos em um StringVar."""

    def __init__(self, root: tk.Misc, var: tk.StringVar, phrases: list[str], interval: int = 1800):
        self.root = root
        self.var = var
        self.phrases = phrases
        self.interval = interval
        self.index = 0
        self._running = False

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running or not self.phrases:
            return
        self.var.set(self.phrases[self.index % len(self.phrases)])
        self.index += 1
        self.root.after(self.interval, self._tick)


class LiveGraph(tk.Canvas):
    def __init__(
        self,
        parent,
        label: str = "",
        color: str | None = None,
        max_points: int = 48,
        width: int = 190,
        height: int = 58,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=C["card"],
            highlightthickness=1,
            highlightbackground=C["border"],
            **kwargs,
        )
        self._label = label
        self._color = color or C["cyan"]
        self._data: deque[float] = deque([0.0] * max_points, maxlen=max_points)
        self._width = width
        self._height = height
        self._draw()

    def push(self, value: float):
        self._data.append(max(0.0, min(100.0, float(value))))
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h, pad = self._width, self._height, 5
        for i in range(1, 4):
            y = pad + (h - 2 * pad) * i / 4
            self.create_line(pad, y, w - pad, y, fill=C["border"], width=1)

        pts = []
        data = list(self._data)
        step = (w - 2 * pad) / max(1, len(data) - 1)
        for i, value in enumerate(data):
            x = pad + i * step
            y = h - pad - (value / 100) * (h - 2 * pad)
            pts.append((x, y))

        if len(pts) >= 2:
            poly = [pad, h - pad]
            for x, y in pts:
                poly.extend([x, y])
            poly.extend([pts[-1][0], h - pad])
            self.create_polygon(poly, fill=C["cyan_bg"], outline="")
            self.create_line(
                *[coord for pt in pts for coord in pt],
                fill=self._color,
                width=2,
                smooth=True,
            )

        lx, ly = pts[-1]
        pulse = 2 + abs(math.sin(len(data))) * 2
        self.create_oval(lx - pulse, ly - pulse, lx + pulse, ly + pulse, fill=self._color, outline="")
        val = data[-1] if data else 0
        val_color = C["error"] if val >= 80 else self._color
        self.create_text(pad + 2, pad + 2, anchor="nw", text=self._label, fill=C["text_dim"], font=F["tiny"])
        self.create_text(w - pad - 2, pad + 2, anchor="ne", text=f"{val:.0f}%", fill=val_color, font=("Consolas", 9, "bold"))


class MiniBar(tk.Canvas):
    def __init__(self, parent, label: str = "", color: str | None = None, width: int = 190, height: int = 18, **kwargs):
        super().__init__(parent, width=width, height=height, bg=C["card"], highlightthickness=0, **kwargs)
        self._label = label
        self._color = color or C["cyan"]
        self._width = width
        self._height = height
        self._value = 0.0
        self._draw()

    def set_value(self, pct: float):
        self._value = max(0.0, min(100.0, float(pct)))
        self._draw()

    def _draw(self):
        self.delete("all")
        pct = self._value
        color = C["error"] if pct >= 80 else C["warning"] if pct >= 65 else self._color
        w, h = self._width, self._height
        self.create_rectangle(2, 2, w - 2, h - 2, fill=C["border"], outline="")
        fill_w = int((w - 4) * pct / 100)
        if fill_w:
            self.create_rectangle(2, 2, 2 + fill_w, h - 2, fill=color, outline="")
        self.create_text(6, h // 2, anchor="w", text=self._label, fill=C["text_bright"], font=F["tiny"])
        self.create_text(w - 5, h // 2, anchor="e", text=f"{pct:.0f}%", fill=color, font=F["tiny"])


class PulseIndicator(tk.Canvas):
    def __init__(self, parent, color: str | None = None, size: int = 22, **kwargs):
        super().__init__(parent, width=size, height=size, bg=C["panel"], highlightthickness=0, **kwargs)
        self._color = color or C["cyan"]
        self._size = size
        self._active = False
        self._phase = 0.0
        self._draw_idle()

    def start(self, color: str | None = None):
        if color:
            self._color = color
        self._active = True
        self._animate()

    def stop(self):
        self._active = False
        self._draw_idle()

    def _draw_idle(self):
        self.delete("all")
        c = self._size // 2
        self.create_oval(c - 4, c - 4, c + 4, c + 4, fill=C["text_muted"], outline="")

    def _animate(self):
        if not self._active:
            return
        self.delete("all")
        c = self._size // 2
        self._phase = (self._phase + 0.2) % (2 * math.pi)
        r = 6 + int(abs(math.sin(self._phase)) * 5)
        self.create_oval(c - r, c - r, c + r, c + r, outline=self._color, width=1)
        self.create_oval(c - 4, c - 4, c + 4, c + 4, fill=self._color, outline="")
        self.after(55, self._animate)


class Toast:
    def __init__(self, root: tk.Misc, message: str, kind: str = "info", duration: int = 3000):
        colors = {
            "info": (C["cyan"], C["cyan_bg"]),
            "success": (C["green"], C["green_bg"]),
            "error": (C["error"], "#220010"),
            "warning": (C["warning"], "#221a00"),
        }
        fg, bg = colors.get(kind, colors["info"])
        SoundBus.play(kind)
        self._root = root
        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.configure(bg=bg)
        icons = {"info": "●", "success": "✓", "error": "✕", "warning": "⚠"}
        tk.Label(
            self._win,
            text=f"{icons.get(kind, '●')}  {message}",
            bg=bg,
            fg=fg,
            font=("Consolas", 11),
            padx=14,
            pady=10,
        ).pack()
        self._place()
        root.after(duration, self._dismiss)

    def _place(self):
        self._win.update_idletasks()
        x = self._root.winfo_screenwidth() - self._win.winfo_width() - 24
        y = self._root.winfo_screenheight() - self._win.winfo_height() - 64
        self._win.geometry(f"+{x}+{y}")

    def _dismiss(self):
        try:
            self._win.destroy()
        except Exception:
            pass


def show_toast(root, message: str, kind: str = "info", duration: int = 3000):
    Toast(root, message, kind, duration)


def bind_button_fx(widget, sound: str = "click"):
    """Adiciona hover/click sonoro e pequeno pulso visual a botoes CTk/tk."""
    state = {"armed": False}

    def on_enter(_event):
        if state["armed"]:
            return
        state["armed"] = True
        SoundBus.play("hover")

    def on_leave(_event):
        state["armed"] = False

    def on_click(_event):
        SoundBus.play(sound)

    try:
        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")
        widget.bind("<Button-1>", on_click, add="+")
    except Exception:
        pass
    return widget
