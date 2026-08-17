from __future__ import annotations

# Small, dependency-free spelling fallback for words selected from running text.
# Candidates are never accepted on morphology alone: MaiMemo's vocabulary API
# must confirm that a candidate actually exists before it is used.

_IRREGULAR: dict[str, tuple[str, ...]] = {
    "children": ("child",),
    "men": ("man",),
    "women": ("woman",),
    "people": ("person",),
    "mice": ("mouse",),
    "geese": ("goose",),
    "teeth": ("tooth",),
    "feet": ("foot",),
}


def spelling_candidates(spelling: str) -> list[str]:
    """Return conservative base-form candidates in preferred lookup order.

    The first item is always the normalized original spelling. Later items are
    only fallbacks and still have to be found by MaiMemo's vocabulary API.
    """
    word = spelling.strip().lower()
    if not word:
        return []

    candidates: list[str] = []

    def add(value: str) -> None:
        value = value.strip().lower()
        if len(value) >= 2 and value not in candidates:
            candidates.append(value)

    add(word)

    for irregular in _IRREGULAR.get(word, ()):
        add(irregular)

    # Plural nouns: strawberries -> strawberry, lettuces -> lettuce,
    # boxes -> box. We keep several possible spellings and let MaiMemo decide.
    if len(word) > 4 and word.endswith("ies"):
        add(word[:-3] + "y")
    if len(word) > 4 and word.endswith("ves"):
        add(word[:-3] + "f")
        add(word[:-3] + "fe")
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        add(word[:-1])
    if len(word) > 4 and word.endswith("es"):
        add(word[:-2])

    # Common verb forms: studied -> study, started -> start,
    # running -> run, making -> make.
    if len(word) > 4 and word.endswith("ied"):
        add(word[:-3] + "y")
    if len(word) > 4 and word.endswith("ed"):
        stem = word[:-2]
        add(stem)
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            add(stem[:-1])
        add(stem + "e")
    if len(word) > 5 and word.endswith("ing"):
        stem = word[:-3]
        add(stem)
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            add(stem[:-1])
        add(stem + "e")

    # Frequent comparative/superlative forms in reading passages.
    if len(word) > 4 and word.endswith("er"):
        stem = word[:-2]
        add(stem)
        add(stem + "e")
    if len(word) > 5 and word.endswith("est"):
        stem = word[:-3]
        add(stem)
        add(stem + "e")

    return candidates
