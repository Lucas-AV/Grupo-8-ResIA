from pairing_store import PairingStore


def test_create_returns_a_pending_code():
    store = PairingStore()
    code = store.create()
    assert store.get_status(code) == "pending"


def test_unknown_code_is_not_found():
    store = PairingStore()
    assert store.get_status("nope") == "not_found"


def test_mark_completed_then_status_is_completed():
    store = PairingStore()
    code = store.create()
    store.mark_completed(code, {"access_token": "at"})
    assert store.get_status(code) == "completed"


def test_mark_completed_on_unknown_code_is_a_no_op():
    store = PairingStore()
    store.mark_completed("nope", {"access_token": "at"})
    assert store.get_status("nope") == "not_found"


def test_consume_returns_tokens_and_removes_entry():
    store = PairingStore()
    code = store.create()
    store.mark_completed(code, {"access_token": "at"})

    tokens = store.consume(code)

    assert tokens == {"access_token": "at"}
    assert store.get_status(code) == "not_found"


def test_consume_on_pending_code_returns_none_and_keeps_entry():
    store = PairingStore()
    code = store.create()

    tokens = store.consume(code)

    assert tokens is None
    assert store.get_status(code) == "pending"


def test_consume_on_unknown_code_returns_none():
    store = PairingStore()
    assert store.consume("nope") is None


def test_entry_expires_after_ttl():
    fake_time = [1000.0]
    store = PairingStore(clock=lambda: fake_time[0])
    code = store.create()

    fake_time[0] += 5 * 60

    assert store.get_status(code) == "not_found"


def test_entry_still_valid_just_before_ttl():
    fake_time = [1000.0]
    store = PairingStore(clock=lambda: fake_time[0])
    code = store.create()

    fake_time[0] += 5 * 60 - 1

    assert store.get_status(code) == "pending"


def test_codes_are_unique_and_url_safe():
    store = PairingStore()
    code1 = store.create()
    code2 = store.create()
    assert code1 != code2
    assert len(code1) > 10
