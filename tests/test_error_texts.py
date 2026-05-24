from soundtouchbose.core.error_texts import error_details, is_valid_source, source_display_text, user_error_text


def test_invalid_source_is_translated() -> None:
    assert source_display_text("invalid_source") == "Keine gültige Quelle verfügbar"
    assert not is_valid_source("invalid_source")


def test_user_error_text_for_connection_failures() -> None:
    text = user_error_text(RuntimeError("SoundTouch request failed for http://1.2.3.4:8090"))
    assert "Verbindung" in text


class FakeRequestError(Exception):
    def __init__(self, message: str, *, kind: str, operation_name: str = "select", status_code: int | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.operation = operation_name
        self.status_code = status_code
        self.endpoint = "/select"


def test_user_error_text_for_http_api_rejection() -> None:
    text = user_error_text(FakeRequestError("SoundTouch HTTP 500", kind="http_status", status_code=500))
    assert "Gerät ist erreichbar" in text
    assert "HTTP 500" in text


def test_error_details_extracts_operation_and_endpoint() -> None:
    details = error_details(FakeRequestError("SoundTouch HTTP 500", kind="http_status", operation_name="preset_write", status_code=500))
    assert details["operation"] == "preset_write"
    assert details["endpoint"] == "/select"
    assert details["http_status"] == 500
