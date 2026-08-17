from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://open.maimemo.com/open/"
DEFAULT_TIMEOUT = 15


class MaiMemoError(RuntimeError):
    pass


class MaiMemoAuthError(MaiMemoError):
    pass


class VocabularyNotFoundError(MaiMemoError):
    pass


@dataclass
class AddResult:
    word: str
    vocabulary_id: str
    added_count: int
    advance: bool


class MaiMemoClient:
    def __init__(self, token: str, timeout: int = DEFAULT_TIMEOUT):
        self.token = token.strip()
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method: str, path: str, *, json: Any | None = None) -> dict[str, Any]:
        url = BASE_URL + path.lstrip("/")
        response = self.session.request(
            method,
            url,
            json=json,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        if response.status_code == 401:
            raise MaiMemoAuthError("API Token 已失效或无权限，请重新配置。")
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {}
        if not response.ok:
            raise MaiMemoError(_extract_error(payload) or f"HTTP {response.status_code}: 请求失败")
        if isinstance(payload, dict) and payload.get("success") is False:
            raise MaiMemoError(_extract_error(payload) or "墨墨 API 返回失败。")
        if isinstance(payload, dict) and payload.get("errors"):
            raise MaiMemoError(_extract_error(payload))
        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            return payload["data"]
        return payload if isinstance(payload, dict) else {}

    def resolve_vocabulary_id(self, spelling: str) -> str:
        data = self._request(
            "POST",
            "/api/v1/vocabulary/query",
            json={"spellings": [spelling], "ids": []},
        )
        vocabularies = data.get("voc") or []
        if not vocabularies:
            lower = spelling.lower()
            if lower != spelling:
                data = self._request(
                    "POST",
                    "/api/v1/vocabulary/query",
                    json={"spellings": [lower], "ids": []},
                )
                vocabularies = data.get("voc") or []
        if not vocabularies:
            raise VocabularyNotFoundError(f'墨墨词库中没有找到“{spelling}”。')
        first = vocabularies[0]
        voc_id = first.get("id") if isinstance(first, dict) else None
        if not voc_id:
            raise VocabularyNotFoundError(f'墨墨词库中没有找到“{spelling}”。')
        return str(voc_id)

    def add_word(self, spelling: str, *, advance: bool = False) -> AddResult:
        voc_id = self.resolve_vocabulary_id(spelling)
        data = self._request(
            "POST",
            "/api/v1/study/add_words",
            json={"words": [{"id": voc_id}], "advance": bool(advance)},
        )
        return AddResult(
            word=spelling,
            vocabulary_id=voc_id,
            added_count=int(data.get("added_count", 0)),
            advance=bool(advance),
        )

    def advance_word(self, spelling: str) -> int:
        voc_id = self.resolve_vocabulary_id(spelling)
        data = self._request(
            "POST",
            "/api/v1/study/advance_study",
            json={"voc_ids": [voc_id]},
        )
        return int(data.get("advanced_count", 0))


def _extract_error(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        parts: list[str] = []
        for item in errors:
            if isinstance(item, dict):
                code = item.get("code")
                message = item.get("message")
                parts.append(f"{code}: {message}" if code else str(message or item))
            else:
                parts.append(str(item))
        return "; ".join(parts)
    message = payload.get("message")
    return str(message) if message else ""
