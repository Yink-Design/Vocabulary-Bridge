from __future__ import annotations

import time
import uuid

import pyperclip
from pynput.keyboard import Controller, Key

from .text import normalize_selection


class SelectionCapture:
    def __init__(self, delay_ms: int = 140, restore_clipboard: bool = True):
        self.delay_ms = delay_ms
        self.restore_clipboard = restore_clipboard
        self.keyboard = Controller()

    def capture(self) -> str:
        old_text: str | None = None
        if self.restore_clipboard:
            try:
                old_text = pyperclip.paste()
            except Exception:
                old_text = None

        sentinel = f"__VOCAB_BRIDGE_{uuid.uuid4().hex}__"
        try:
            pyperclip.copy(sentinel)
        except Exception:
            sentinel = ""

        time.sleep(self.delay_ms / 1000)
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("c")
            self.keyboard.release("c")
        time.sleep(0.12)

        try:
            selected = pyperclip.paste()
        except Exception:
            selected = ""
        if sentinel and selected == sentinel:
            selected = ""

        if self.restore_clipboard and old_text is not None:
            time.sleep(0.03)
            try:
                pyperclip.copy(old_text)
            except Exception:
                pass

        return normalize_selection(selected)
