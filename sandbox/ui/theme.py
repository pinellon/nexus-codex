"""Tema visual do NEXUS."""

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg": "#07070f",
    "panel": "#0d0d1a",
    "card": "#111122",
    "card_hover": "#17172d",
    "border": "#1a1a35",
    "border_hi": "#2a2a5d",
    "cyan": "#00e5ff",
    "cyan_dim": "#00a8c0",
    "cyan_bg": "#001a22",
    "green": "#00ff9d",
    "green_dim": "#00c075",
    "green_bg": "#001a0f",
    "purple": "#7b4fff",
    "yellow": "#ffcc00",
    "success": "#00ff9d",
    "warning": "#ffcc00",
    "error": "#ff3366",
    "info": "#00e5ff",
    "text": "#d0d8ff",
    "text_dim": "#7f8ac6",
    "text_muted": "#485073",
    "text_bright": "#ffffff",
}

F = {
    "display": ("Consolas", 28, "bold"),
    "title": ("Consolas", 16, "bold"),
    "heading": ("Consolas", 13, "bold"),
    "body": ("Consolas", 12),
    "small": ("Consolas", 10),
    "tiny": ("Consolas", 9),
    "mono": ("Courier New", 11),
    "btn": ("Consolas", 11, "bold"),
    "btn_sm": ("Consolas", 10, "bold"),
}

BTN = {
    "primary": dict(
        fg_color=C["cyan"], hover_color=C["cyan_dim"],
        text_color="#000000", font=F["btn"], corner_radius=6, border_width=0,
    ),
    "secondary": dict(
        fg_color=C["card"], hover_color=C["card_hover"],
        text_color=C["cyan"], font=F["btn_sm"], corner_radius=6,
        border_width=1, border_color=C["border_hi"],
    ),
    "ghost": dict(
        fg_color="transparent", hover_color=C["card"],
        text_color=C["text_dim"], font=F["btn_sm"], corner_radius=6, border_width=0,
    ),
    "danger": dict(
        fg_color=C["card"], hover_color="#220a12",
        text_color=C["error"], font=F["btn_sm"], corner_radius=6,
        border_width=1, border_color="#330011",
    ),
    "success": dict(
        fg_color=C["card"], hover_color=C["green_bg"],
        text_color=C["green"], font=F["btn_sm"], corner_radius=6,
        border_width=1, border_color="#003320",
    ),
}

COLORS = C
FONTS = F
BTN_PRIMARY = BTN["primary"]
BTN_SECONDARY = BTN["secondary"]
BTN_GHOST = BTN["ghost"]
BTN_DANGER = BTN["danger"]

