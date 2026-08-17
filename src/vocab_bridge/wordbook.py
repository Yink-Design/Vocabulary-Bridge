from __future__ import annotations

import csv
import re
from pathlib import Path

from .config import app_data_dir

_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
WORDLIST_PATH = app_data_dir() / "current_wordbook.txt"


class CurrentWordbook:
    def __init__(self, path: Path = WORDLIST_PATH):
        self.path = path
        self._words: set[str] | None = None

    @property
    def configured(self) -> bool:
        return self.path.exists() and self.path.stat().st_size > 0

    def words(self) -> set[str]:
        if self._words is None:
            if not self.configured:
                self._words = set()
            else:
                self._words = {
                    line.strip().lower()
                    for line in self.path.read_text(encoding="utf-8").splitlines()
                    if _WORD_RE.fullmatch(line.strip())
                }
        return self._words

    def contains(self, word: str) -> bool:
        return word.strip().lower() in self.words()


def import_wordbook_file(source: str | Path) -> int:
    source = Path(source)
    words: set[str] = set()

    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.reader(handle):
                if not row:
                    continue
                candidate = row[0].strip()
                if _WORD_RE.fullmatch(candidate):
                    words.add(candidate.lower())
    else:
        for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
            candidate = raw_line.strip()
            if "\t" in candidate:
                candidate = candidate.split("\t", 1)[0].strip()
            if _WORD_RE.fullmatch(candidate):
                words.add(candidate.lower())

    if not words:
        raise ValueError("没有读取到有效英文单词。请使用每行一个单词的 TXT，或单词位于第一列的 CSV。")

    WORDLIST_PATH.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    return len(words)
