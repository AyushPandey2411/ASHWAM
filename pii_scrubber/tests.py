from scrubber import process_entry


def test_email():
    entry = {"entry_id": "1", "text": "Contact me at test@mail.com"}
    out = process_entry(entry)
    assert "[EMAIL]" in out["scrubbed_text"]


def test_phone_real():
    entry = {"entry_id": "2", "text": "Call me on +61 412 345 678"}
    out = process_entry(entry)
    assert "[PHONE]" in out["scrubbed_text"]


def test_false_phone():
    entry = {"entry_id": "3", "text": "Steps today 6234 (not a phone)"}
    out = process_entry(entry)
    assert "6234" in out["scrubbed_text"]


def test_health_preserved():
    entry = {"entry_id": "4", "text": "Cramps intensity 6/10"}
    out = process_entry(entry)
    assert "6/10" in out["scrubbed_text"]


def test_name_detection():
    entry = {"entry_id": "5", "text": "Patient: S. Iyer visited today"}
    out = process_entry(entry)
    assert "[NAME]" in out["scrubbed_text"]


def test_url_over_email_overlap():
    entry = {"entry_id": "6", "text": "Visit https://test.com/mail@x.com"}
    out = process_entry(entry)
    assert "[URL]" in out["scrubbed_text"]


def test_hinglish_preserved():
    entry = {"entry_id": "7", "text": "Aaj thoda bloated feel ho raha hai"}
    out = process_entry(entry)
    assert "bloated" in out["scrubbed_text"]


if __name__ == "__main__":
    test_email()
    test_phone_real()
    test_false_phone()
    test_health_preserved()
    test_name_detection()
    test_url_over_email_overlap()
    test_hinglish_preserved()
    print("All tests passed ✅")
