from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .api import MaiMemoClient
from .config import app_data_dir

PENDING_PATH = app_data_dir() / "pending_words.json"


@dataclass(frozen=True)
class RouteDecision:
    existing: bool
    today_complete: bool
    action: str


def decide_route(existing: bool, today_complete: bool) -> RouteDecision:
    if today_complete:
        return RouteDecision(existing, today_complete, "queue_tomorrow")
    if existing:
        return RouteDecision(existing, today_complete, "advance_today")
    return RouteDecision(existing, today_complete, "add_today")


@dataclass
class ProcessResult:
    status: str
    message: str
    close_after_ms: int | None = 1100


class PendingStore:
    def __init__(self, path: Path = PENDING_PATH):
        self.path = path

    def _load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save(self, items: list[dict[str, str]]) -> None:
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def enqueue_tomorrow(self, word: str) -> None:
        items = self._load()
        key = word.strip().lower()
        due = (date.today() + timedelta(days=1)).isoformat()
        for item in items:
            if item.get("word", "").lower() == key:
                item["due_date"] = due
                self._save(items)
                return
        items.append(
            {
                "word": word.strip(),
                "due_date": due,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        self._save(items)

    def due_words(self, today: date | None = None) -> list[str]:
        today = today or date.today()
        due: list[str] = []
        for item in self._load():
            try:
                due_date = date.fromisoformat(item.get("due_date", ""))
            except ValueError:
                continue
            if due_date <= today and item.get("word"):
                due.append(str(item["word"]))
        return due

    def remove(self, word: str) -> None:
        key = word.strip().lower()
        items = [item for item in self._load() if item.get("word", "").lower() != key]
        self._save(items)


class SmartStudyRouter:
    def __init__(self, client: MaiMemoClient, *, pending: PendingStore | None = None):
        self.client = client
        self.pending = pending or PendingStore()

    def process(self, word: str) -> ProcessResult:
        word = word.strip()
        existing = self.client.is_in_study_plan(word)
        progress = self.client.get_study_progress()
        decision = decide_route(existing, progress.is_complete)

        if decision.action == "queue_tomorrow":
            self.pending.enqueue_tomorrow(word)
            if existing:
                return ProcessResult("queued", "✓ 已在记忆规划；今日任务已完成，已顺延到明日复习")
            return ProcessResult("queued", "✓ 新词；今日任务已完成，已顺延到明日新学")

        if decision.action == "advance_today":
            self.client.advance_word(word)
            return ProcessResult("advanced", "✓ 已在记忆规划，已提前到今天复习")

        # For a new word, advance=True brings it into the active study flow now.
        result = self.client.add_word(word, advance=True)
        if result.added_count == 0:
            # The plan may have changed between the status query and add request.
            self.client.advance_word(word)
            return ProcessResult("advanced", "✓ 已在记忆规划，已提前到今天复习")
        return ProcessResult("added", "✓ 新词，已加入记忆并安排今天新学")

    def flush_due(self) -> int:
        words = self.pending.due_words()
        if not words:
            return 0

        progress = self.client.get_study_progress()
        if progress.is_complete:
            return 0

        processed = 0
        for word in words:
            if self.client.is_in_study_plan(word):
                self.client.advance_word(word)
            else:
                result = self.client.add_word(word, advance=True)
                if result.added_count == 0:
                    self.client.advance_word(word)
            self.pending.remove(word)
            processed += 1
        return processed
