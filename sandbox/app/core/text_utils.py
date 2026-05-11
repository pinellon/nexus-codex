"""Utilitarios de texto para voz e roteamento."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", (text or "").strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, options: Iterable[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(option) in normalized for option in options)


def remove_wake_word(text: str, wake_word: str = "nexus") -> str:
    normalized = normalize_text(text)
    wake = normalize_text(wake_word)
    if normalized.startswith(wake):
        return normalized[len(wake):].strip(" ,:")
    return normalized


def safe_filename(name: str, default: str = "arquivo.py") -> str:
    cleaned = normalize_text(name).replace(" ", "_")
    cleaned = re.sub(r"[^a-z0-9_.-]", "", cleaned).strip("._-")
    if not cleaned:
        return default
    if "." not in cleaned:
        cleaned += ".py"
    return cleaned
