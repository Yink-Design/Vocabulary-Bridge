from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

from .api import MaiMemoAuthError, MaiMemoClient, MaiMemoError, VocabularyNotFoundError
from .config import get_token, save_token
from .scheduler import SmartStudyRouter
from .text import looks_like_single_word, normalize_selection

TOKEN_PORTAL_URL = "https://open.maimemo.com/open/api/v1/tokens/openapi"


class TokenDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, on_saved=None, *, open_portal: bool = False):
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
            text="Token 仅保存到 Windows Credential Manager。失效后可打开墨墨官方领取页，登录并复制新 Token。",
            justify="left",
            wraplength=460,
        ).pack(anchor="w", pady=(4, 10))
        self.entry = tk.Entry(body, width=62, show="•")
        self.entry.pack(fill="x")
        self.entry.focus_set()

        row = tk.Frame(body)
        row.pack(fill="x", pady=(12, 0))
        tk.Button(row, text="打开官方领取页", width=15, command=self._open_portal).pack(side="left")
        tk.Button(row, text="取消", width=10, command=self.destroy).pack(side="right")
        tk.Button(row, text="保存并验证", width=12, command=self._save).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._save())
        self._place_center()

        if open_portal:
            self.after(250, self._open_portal)

    @staticmethod
    def _open_portal():
        webbrowser.open(TOKEN_PORTAL_URL)

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
        width, height = 520, 200
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
        self.entry = tk.Entry(body, textvariable=self.word_var, width=38, font=("Segoe UI", 14))
        self.entry.pack(fill="x", pady=(4, 6))
        self.entry.select_range(0, "end")
        self.entry.focus_set()

        self.hint_var = tk.StringVar(value=self._initial_hint(text))
        self.hint = tk.Label(body, textvariable=self.hint_var, justify="left", anchor="w", wraplength=410)
        self.hint.pack(fill="x", pady=(0, 10))

        row = tk.Frame(body)
        row.pack(fill="x")
        self.sync_btn = tk.Button(row, text="按规则同步", width=15, command=self._submit)
        self.sync_btn.pack(side="left")
        tk.Button(row, text="取消", width=9, command=self.destroy).pack(side="right")

        self.status_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.status_var, anchor="w", wraplength=410, justify="left").pack(fill="x", pady=(10, 0))
        self.bind("<Return>", lambda _e: self._submit())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._place_near_pointer()

    @staticmethod
    def _initial_hint(text: str) -> str:
        if not text:
            return "没有读取到选中文字，可直接输入。"
        if looks_like_single_word(text):
            return "程序会自动判断：已在记忆规划→提前复习；新词→加入记忆。"
        return "当前选择包含空格或非单词字符，请先编辑成一个英文单词再提交。"

    def _set_busy(self, busy: bool):
        self.sync_btn.config(state="disabled" if busy else "normal")

    def _submit(self):
        word = normalize_selection(self.word_var.get())
        if not word:
            self.status_var.set("请输入一个单词。")
            return
        if not looks_like_single_word(word):
            self.status_var.set("请只保留一个英文单词。")
            return

        token = get_token()
        if not token:
            if self.on_need_token:
                self.on_need_token(True)
            self.status_var.set("请先配置墨墨 API Token。")
            return

        self._set_busy(True)
        self.status_var.set("正在核对单词…")

        def worker():
            try:
                client = MaiMemoClient(token)
                resolved = client.resolve_vocabulary(word)
                if resolved.spelling.lower() != word.lower():
                    self.after(
                        0,
                        lambda: self._confirm_fallback(word, resolved.spelling),
                    )
                    return
                result = SmartStudyRouter(client).process(resolved.spelling)
                self.after(0, lambda: self._result(result.message, result.close_after_ms))
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

    def _confirm_fallback(self, original: str, resolved: str):
        self._set_busy(False)
        answer = messagebox.askyesno(
            "确认词形还原",
            f"您想加入的词是不是：{resolved}？\n\n原划词：{original}\n\n选择“是”将按 {resolved} 继续；选择“否”可手动修改。",
            parent=self,
        )
        if answer:
            self.word_var.set(resolved)
            self.status_var.set(f"已确认：{original} → {resolved}，正在同步…")
            self._sync_confirmed(resolved)
            return

        self.word_var.set(original)
        self.status_var.set("请在上方手动输入正确单词，再点击“按规则同步”。")
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def _sync_confirmed(self, word: str):
        token = get_token()
        if not token:
            if self.on_need_token:
                self.on_need_token(True)
            self.status_var.set("请先配置墨墨 API Token。")
            return

        self._set_busy(True)

        def worker():
            try:
                result = SmartStudyRouter(MaiMemoClient(token)).process(word)
                self.after(0, lambda: self._result(result.message, result.close_after_ms))
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

    def _result(self, message: str, close_after_ms: int | None):
        self._set_busy(False)
        self.status_var.set(message)
        if close_after_ms is not None:
            self.after(close_after_ms, self.destroy)

    def _error(self, message: str, need_token: bool = False):
        self._set_busy(False)
        self.status_var.set(message)
        if need_token and self.on_need_token:
            self.on_need_token(True)

    def _place_near_pointer(self):
        self.update_idletasks()
        width, height = 450, 190
        px, py = self.winfo_pointerx(), self.winfo_pointery()
        x = min(max(10, px + 16), self.winfo_screenwidth() - width - 10)
        y = min(max(10, py + 16), self.winfo_screenheight() - height - 50)
        self.geometry(f"{width}x{height}+{x}+{y}")
