import re

_EDGE_PUNCTUATION = " \t\r\n\"“”‘’`.,;:!?()[]{}<>，。；：！？（）【】《》"


def normalize_selection(text: str) -> str:
    """Normalize selected text without guessing a lemma."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(_EDGE_PUNCTUATION)
    return text


def looks_like_single_word(text: str) -> bool:
    if not text:
        return False
    return bool(re.fullmatch(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text))
