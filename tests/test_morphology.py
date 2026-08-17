from vocab_bridge.morphology import spelling_candidates


def test_plural_lettuces_falls_back_to_lettuce():
    candidates = spelling_candidates("lettuces")
    assert candidates[0] == "lettuces"
    assert "lettuce" in candidates


def test_plural_strawberries_falls_back_to_strawberry():
    candidates = spelling_candidates("Strawberries")
    assert candidates[0] == "strawberries"
    assert "strawberry" in candidates


def test_common_verb_forms_have_base_candidates():
    assert "study" in spelling_candidates("studied")
    assert "start" in spelling_candidates("started")
    assert "run" in spelling_candidates("running")
    assert "make" in spelling_candidates("making")


def test_irregular_plural_has_base_candidate():
    assert "child" in spelling_candidates("children")
