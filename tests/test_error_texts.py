from soundtouchbose.api.client import SoundTouchRequestError
from soundtouchbose.core.error_texts import is_valid_source, source_display_text, user_error_text


def test_invalid_source_is_translated() -> None:
    assert source_display_text("invalid_source") == "Keine gültige Quelle verfügbar"
    assert not is_valid_source("invalid_source")


def test_user_error_text_for_connection_failures() -> None:
    text = user_error_text(RuntimeError("SoundTouch request failed for http://1.2.3.4:8090"))
    assert "Verbindung" in text


def test_user_error_text_for_http_api_rejection() -> None:
    text = user_error_text(SoundTouchRequestError("http://1.2.3.4:8090/select", status_code=500))
    assert "HTTP 500" in text
    assert "/select" in text
