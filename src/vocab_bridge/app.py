from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw
import pystray
from pynput import keyboard

from .api import MaiMemoAuthError, MaiMemoClient
from .capture import SelectionCapture
from .config import AppConfig, get_token
from .scheduler import SmartStudyRouter
from .ui import CaptureDialog, TokenDialog
from .wordbook import import_wordbook_file


class VocabularyBridgeApp:
    def __init__(self):
        self.config = AppConfig.load()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.capture = SelectionCapture(
            delay_ms=self.config.capture_delay_ms,
            restore_clipboard=self.config.restore_clipboard,
        )
        self.listener: keyboard.GlobalHotKeys | None = None
        self.tray: pystray.Icon | None = None
        self._capture_lock = threading.Lock()

    def run(self):
        self._start_hotkey()
        self._start_tray()
        if not get_token():
            self.root.after(300, self.open_token_dialog)
        else:
            self.root.after(600, self._flush_pending_async)
        self.root.mainloop()

    def _start_hotkey(self):
        self.listener = keyboard.GlobalHotKeys({self.config.hotkey: self._hotkey_callback})
        self.listener.start()

    def _hotkey_callback(self):
        self.root.after(0, self.capture_selected_word)

    def capture_selected_word(self):
        if not self._capture_lock.acquire(blocking=False):
            return

        def worker():
            try:
                text = self.capture.capture()
                self.root.after(0, lambda: CaptureDialog(self.root, text, self.open_token_dialog))
            finally:
                self._capture_lock.release()

        threading.Thread(target=worker, daemon=True).start()

    def open_token_dialog(self):
        TokenDialog(self.root, on_saved=self._flush_pending_async)

    def _import_wordbook(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            title="导入当前词书词表",
            filetypes=[
                ("词表文件", "*.txt *.csv"),
                ("Text", "*.txt"),
                ("CSV", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            count = import_wordbook_file(path)
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc), parent=self.root)
            return
        messagebox.showinfo(
            "当前词书已更新",
            f"已导入 {count} 个单词。\n从现在起，词书外单词会被拦截并显示“为词书外单词”。",
            parent=self.root,
        )

    def _flush_pending_async(self):
        token = get_token()
        if not token:
            return

        def worker():
            try:
                count = SmartStudyRouter(MaiMemoClient(token)).flush_due()
                if count and self.tray:
                    self.tray.notify(f"已同步 {count} 个昨日顺延单词", "Vocabulary Bridge")
            except MaiMemoAuthError:
                self.root.after(0, self.open_token_dialog)
            except Exception:
                # Pending items remain on disk and will be retried later.
                return

        threading.Thread(target=worker, daemon=True).start()

    def _start_tray(self):
        icon_image = self._make_icon()
        self.tray = pystray.Icon(
            "IELTSVocabularyBridge",
            icon_image,
            "IELTS Vocabulary Bridge · F8 捕获",
            menu=pystray.Menu(
                pystray.MenuItem("捕获选中单词 (F8)", lambda _icon, _item: self.root.after(0, self.capture_selected_word)),
                pystray.MenuItem("导入当前词书词表", lambda _icon, _item: self.root.after(0, self._import_wordbook)),
                pystray.MenuItem("配置墨墨 API Token", lambda _icon, _item: self.root.after(0, self.open_token_dialog)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", lambda _icon, _item: self.root.after(0, self.quit)),
            ),
        )
        self.tray.run_detached()

    @staticmethod
    def _make_icon() -> Image.Image:
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((7, 7, 57, 57), radius=13, fill=(35, 35, 40, 255))
        draw.text((20, 14), "V", fill=(245, 245, 245, 255))
        draw.text((31, 29), "+", fill=(245, 245, 245, 255))
        return image

    def quit(self):
        if self.listener:
            self.listener.stop()
        if self.tray:
            self.tray.stop()
        self.root.quit()
        self.root.destroy()


def main():
    VocabularyBridgeApp().run()


if __name__ == "__main__":
    main()
