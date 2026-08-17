from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

import keyring

APP_NAME = "IELTSVocabularyBridge"
KEYRING_SERVICE = "IELTS Vocabulary Bridge / MaiMemo"
KEYRING_USER = "api-token"


def app_data_dir() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home()))
    folder = root / APP_NAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _config_path() -> Path:
    return app_data_dir() / "config.json"


@dataclass
class AppConfig:
    hotkey: str = "<f8>"
    capture_delay_ms: int = 100
    restore_clipboard: bool = True

    @classmethod
    def load(cls) -> "AppConfig":
        path = _config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        except Exception:
            return cls()

    def save(self) -> None:
        _config_path().write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def get_token() -> str | None:
    token = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    return token.strip() if token else None


def save_token(token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token.strip())


def delete_token() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except keyring.errors.PasswordDeleteError:
        pass
