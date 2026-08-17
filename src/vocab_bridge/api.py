from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .morphology import spelling_candidates

BASE_URL = "https://open.maimemo.com/open/"
DEFAULT_TIMEOUT = 15


class MaiMemoError(RuntimeError):
    pass


class MaiMemoAuthError(MaiMemoError):
    pass


class VocabularyNotFoundError(MaiMemoError):
    pass


@dataclass(frozen=True)
class ResolvedVocabulary:
    requested_spelling: str
    spelling: str
    vocabulary_id: str


@dataclass
class AddResult:
    word: str
    resolved_word: str
    vocabulary_id: str
    added_count: int
    advance: bool


@dataclass
class StudyProgress:
    finished: int
    total: int
    study_time: int = 0

    @property
    def is_complete(self) -> bool:
        return self.finished >= self.total


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

    def validate_token(self) -> bool:
        """Validate the token with a read-only vocabulary request."""
        self._request(
            "POST",
            "/api/v1/vocabulary/query",
            json={"spellings": ["apple"], "ids": []},
        )
        return True

    def resolve_vocabulary(self, spelling: str) -> ResolvedVocabulary:
        candidates = spelling_candidates(spelling)
        if not candidates:
            raise VocabularyNotFoundError(f'墨墨词库中没有找到“{spelling}”。')

        data = self._request(
            "POST",
            "/api/v1/vocabulary/query",
            json={"spellings": candidates, "ids": []},
        )
        vocabularies = data.get("voc") or []

        by_spelling: dict[str, dict[str, Any]] = {}
        for item in vocabularies:
            if not isinstance(item, dict):
                continue
            item_spelling = str(item.get("spelling") or "").strip().lower()
            if item_spelling:
                by_spelling[item_spelling] = item

        for candidate in candidates:
            item = by_spelling.get(candidate.lower())
            if not item:
                continue
            voc_id = item.get("id")
            if not voc_id:
                continue
            resolved_spelling = str(item.get("spelling") or candidate)
            return ResolvedVocabulary(
                requested_spelling=spelling,
                spelling=resolved_spelling,
                vocabulary_id=str(voc_id),
            )

        raise VocabularyNotFoundError(f'墨墨词库中没有找到“{spelling}”及其常见原形。')

    def resolve_vocabulary_id(self, spelling: str) -> str:
        return self.resolve_vocabulary(spelling).vocabulary_id

    def get_study_progress(self) -> StudyProgress:
        data = self._request(
            "POST",
            "/api/v1/study/get_study_progress",
            json={},
        )
        progress = data.get("progress") or {}
        return StudyProgress(
            finished=int(progress.get("finished", 0)),
            total=int(progress.get("total", 0)),
            study_time=int(progress.get("study_time", 0)),
        )

    def query_study_record(self, spelling: str) -> dict[str, Any] | None:
        resolved = self.resolve_vocabulary(spelling)
        data = self._request(
            "POST",
            "/api/v1/study/query_study_records",
            json={
                "voc_ids": [resolved.vocabulary_id],
                "spellings": [],
                "as_count": False,
                "limit": 1,
            },
        )
        records = data.get("records") or []
        first = records[0] if records else None
        return first if isinstance(first, dict) else None

    def is_in_study_plan(self, spelling: str) -> bool:
        return self.query_study_record(spelling) is not None

    def add_word(self, spelling: str, *, advance: bool = False) -> AddResult:
        resolved = self.resolve_vocabulary(spelling)
        data = self._request(
            "POST",
            "/api/v1/study/add_words",
            json={"words": [{"id": resolved.vocabulary_id}], "advance": bool(advance)},
        )
        return AddResult(
            word=spelling,
            resolved_word=resolved.spelling,
            vocabulary_id=resolved.vocabulary_id,
            added_count=int(data.get("added_count", 0)),
            advance=bool(advance),
        )

    def advance_word(self, spelling: str) -> int:
        resolved = self.resolve_vocabulary(spelling)
        data = self._request(
            "POST",
            "/api/v1/study/advance_study",
            json={"voc_ids": [resolved.vocabulary_id]},
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
