from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox

from .api import MaiMemoAuthError, MaiMemoClient, MaiMemoError, VocabularyNotFoundError
from .config import get_token, save_token
from .text import looks_like_single_word, normalize_selection


class TokenDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, on_saved=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("Vocabulary Bridge · API Token")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        body = tk.Frame(self, padx=16, pady=14)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="墨墨 Open API Token", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(
            body,
            text="Token 仅保存到 Windows Credential Manager，不会写入项目文件。",
            justify="left",
            wraplength=430,
        ).pack(anchor="w", pady=(4, 10))
        self.entry = tk.Entry(body, width=62, show="•")
        self.entry.pack(fill="x")
        self.entry.focus_set()

        row = tk.Frame(body)
        row.pack(fill="x", pady=(12, 0))
        tk.Button(row, text="取消", width=10, command=self.destroy).pack(side="right")
        tk.Button(row, text="保存", width=12, command=self._save).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._save())
        self._place_center()

    def _save(self):
        token = self.entry.get().strip()
        if not token:
            messagebox.showwarning("Token 不能为空", "请粘贴墨墨 Open API Token。", parent=self)
            return
        save_token(token)
        if self.on_saved:
            self.on_saved()
        self.destroy()

    def _place_center(self):
        self.update_idletasks()
        width, height = 500, 180
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")


class CaptureDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, text: str, on_need_token=None):
        super().__init__(master)
        self.on_need_token = on_need_token
        self.title("Vocabulary Bridge")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        body = tk.Frame(self, padx=14, pady=12)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="捕获到的词", font=("Segoe UI", 9)).pack(anchor="w")
        self.word_var = tk.StringVar(value=text)
        entry = tk.Entry(body, textvariable=self.word_var, width=38, font=("Segoe UI", 14))
        entry.pack(fill="x", pady=(4, 6))
        entry.select_range(0, "end")
        entry.focus_set()

        self.hint_var = tk.StringVar(value=self._initial_hint(text))
        self.hint = tk.Label(body, textvariable=self.hint_var, justify="left", anchor="w", wraplength=410)
        self.hint.pack(fill="x", pady=(0, 10))

        row = tk.Frame(body)
        row.pack(fill="x")
        self.add_btn = tk.Button(row, text="加入学习规划", width=15, command=lambda: self._submit(False))
        self.add_btn.pack(side="left")
        self.advance_btn = tk.Button(row, text="加入并提前复习", width=16, command=lambda: self._submit(True))
        self.advance_btn.pack(side="left", padx=(8, 0))
        tk.Button(row, text="取消", width=9, command=self.destroy).pack(side="right")

        self.status_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(10, 0))
        self.bind("<Escape>", lambda _e: self.destroy())
        self._place_near_pointer()

    @staticmethod
    def _initial_hint(text: str) -> str:
        if not text:
            return "没有读取到选中文字。可直接在上方输入单词。"
        if looks_like_single_word(text):
            return "确认后会直接写入墨墨学习规划。"
        return "当前选择包含空格或非单词字符，可先编辑成一个英文单词再提交。"

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.add_btn.config(state=state)
        self.advance_btn.config(state=state)

    def _submit(self, advance: bool):
        word = normalize_selection(self.word_var.get())
        if not word:
            self.status_var.set("请输入一个单词。")
            return
        token = get_token()
        if not token:
            if self.on_need_token:
                self.on_need_token()
            self.status_var.set("请先配置墨墨 API Token。")
            return

        self._set_busy(True)
        self.status_var.set("正在同步…")

        def worker():
            try:
                result = MaiMemoClient(token).add_word(word, advance=advance)
                self.after(0, lambda: self._success(result.added_count, advance))
            except MaiMemoAuthError as exc:
                message = str(exc)
                self.after(0, lambda msg=message: self._error(msg, need_token=True))
            except (VocabularyNotFoundError, MaiMemoError) as exc:
                message = str(exc)
                self.after(0, lambda msg=message: self._error(msg))
            except Exception as exc:
                message = f"同步失败：{exc}"
                self.after(0, lambda msg=message: self._error(msg))

        threading.Thread(target=worker, daemon=True).start()

    def _success(self, added_count: int, advance: bool):
        action = "已加入并提前复习" if advance else "已加入学习规划"
        suffix = "" if added_count else "（可能已在学习规划中）"
        self.status_var.set(f"✓ {action}{suffix}")
        self.after(900, self.destroy)

    def _error(self, message: str, need_token: bool = False):
        self._set_busy(False)
        self.status_var.set(message)
        if need_token and self.on_need_token:
            self.on_need_token()

    def _place_near_pointer(self):
        self.update_idletasks()
        width, height = 450, 190
        px, py = self.winfo_pointerx(), self.winfo_pointery()
        x = min(max(10, px + 16), self.winfo_screenwidth() - width - 10)
        y = min(max(10, py + 16), self.winfo_screenheight() - height - 50)
        self.geometry(f"{width}x{height}+{x}+{y}")
