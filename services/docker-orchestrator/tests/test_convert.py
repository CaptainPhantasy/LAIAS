from unittest.mock import MagicMock

from app.api.routes import convert as convert_routes
from app.config import settings


def test_convert_content_returns_converted_payload(client, monkeypatch):
    mock_converter = MagicMock()
    mock_converter.convert.return_value = "<h1>Converted</h1>"
    monkeypatch.setattr(convert_routes, "get_format_converter", lambda: mock_converter)

    response = client.post(
        "/api/convert",
        json={"content": "# Title", "format": "html"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["converted"] == "<h1>Converted</h1>"
    assert data["format"] == "html"
    assert data["content_length"] == len("<h1>Converted</h1>")
    mock_converter.convert.assert_called_once_with("# Title", "html")


def test_convert_content_returns_400_on_converter_error(client, monkeypatch):
    mock_converter = MagicMock()
    mock_converter.convert.side_effect = ValueError("Unsupported format")
    monkeypatch.setattr(convert_routes, "get_format_converter", lambda: mock_converter)

    response = client.post(
        "/api/convert",
        json={"content": "# Title", "format": "markdown"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Unsupported format"


def test_convert_content_validation_error_for_invalid_format(client):
    response = client.post(
        "/api/convert",
        json={"content": "# Title", "format": "pdf"},
    )
    assert response.status_code == 422


def test_convert_content_validation_error_for_missing_content(client):
    response = client.post("/api/convert", json={"format": "html"})
    assert response.status_code == 422


def test_convert_content_requires_api_key_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEYS", ["test-key"])

    response = client.post(
        "/api/convert",
        json={"content": "# Title", "format": "html"},
    )

    assert response.status_code == 401
    data = response.json()
    if "detail" in data:
        assert data["detail"]["error_code"] == "UNAUTHORIZED"
        assert data["detail"]["message"] == "Invalid or missing API key"
    else:
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Invalid or missing API key"
