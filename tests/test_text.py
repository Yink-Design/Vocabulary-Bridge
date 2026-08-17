from vocab_bridge.text import looks_like_single_word, normalize_selection


def test_normalize_selection():
    assert normalize_selection("  precipitation\n") == "precipitation"
    assert normalize_selection("“compulsory,”") == "compulsory"
    assert normalize_selection("state-of-the-art") == "state-of-the-art"
    assert normalize_selection("don't") == "don't"


def test_single_word_detection():
    assert looks_like_single_word("precipitation")
    assert looks_like_single_word("state-of-the-art")
    assert looks_like_single_word("don't")
    assert not looks_like_single_word("civil engineering")
