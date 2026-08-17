from vocab_bridge.wordbook import CurrentWordbook


def test_wordbook_membership_is_case_insensitive(tmp_path):
    path = tmp_path / "book.txt"
    path.write_text("precipitation\ncompulsory\n", encoding="utf-8")
    book = CurrentWordbook(path)

    assert book.configured
    assert book.contains("Precipitation")
    assert not book.contains("extraneous")
