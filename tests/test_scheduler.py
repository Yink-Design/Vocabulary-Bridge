from datetime import date, timedelta

from vocab_bridge.scheduler import PendingStore, decide_route


def test_route_existing_unfinished_advances_today():
    decision = decide_route(existing=True, today_complete=False)
    assert decision.action == "advance_today"


def test_route_new_unfinished_adds_today():
    decision = decide_route(existing=False, today_complete=False)
    assert decision.action == "add_today"


def test_route_complete_queues_tomorrow():
    assert decide_route(existing=True, today_complete=True).action == "queue_tomorrow"
    assert decide_route(existing=False, today_complete=True).action == "queue_tomorrow"


def test_pending_store_deduplicates_and_becomes_due(tmp_path):
    store = PendingStore(tmp_path / "pending.json")
    store.enqueue_tomorrow("precipitation")
    store.enqueue_tomorrow("Precipitation")

    assert store.due_words(date.today()) == []
    assert store.due_words(date.today() + timedelta(days=1)) == ["precipitation"]

    store.remove("PRECIPITATION")
    assert store.due_words(date.today() + timedelta(days=1)) == []
