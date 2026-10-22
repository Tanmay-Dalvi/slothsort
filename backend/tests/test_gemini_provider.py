"""Tests for GeminiProvider: privacy disclosures, error handling, and mock API tests."""

import json
import pytest
import httpx

from backend.app.models.file import FileMetadata, generate_file_id
from backend.app.models.plan import OrganizationOptions
from backend.app.providers.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_unconfigured_key():
    """Verifies that Gemini reports unavailable when no API key is provided."""
    provider = GeminiProvider(api_key="")
    health = await provider.check_health()

    assert health.is_available is False
    assert health.is_cloud is True
    assert "GEMINI_API_KEY is not configured" in (health.error_message or "")


def test_gemini_no_secret_leakage():
    """Security Test: Verifies that API keys are never leaked in string representation or errors."""
    secret_key = "AIzaSySecretTestKey1234567890"
    provider = GeminiProvider(api_key=secret_key)

    repr_str = repr(provider)
    str_str = str(provider)

    assert secret_key not in repr_str
    assert secret_key not in str_str
    assert "is_configured=True" in repr_str


@pytest.mark.asyncio
async def test_gemini_health_check_success_mock():
    """Verifies successful health check against mocked Gemini model verification endpoint."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-goog-api-key") == "valid_key"
        assert "models/gemini-2.5-flash" in str(request.url)
        return httpx.Response(200, json={"name": "models/gemini-2.5-flash", "state": "ACTIVE"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.AsyncClient(transport=transport)

    provider = GeminiProvider(api_key="valid_key", client=client)
    health = await provider.check_health()

    assert health.is_available is True
    assert health.is_cloud is True
    assert "Cloud API Active" in health.privacy_notice
    await client.aclose()


@pytest.mark.asyncio
async def test_gemini_health_check_invalid_key_mock():
    """Verifies health check reports authorization failure when key is rejected."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "API key not valid"}})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.AsyncClient(transport=transport)

    provider = GeminiProvider(api_key="invalid_key", client=client)
    health = await provider.check_health()

    assert health.is_available is False
    assert "Invalid GEMINI_API_KEY" in (health.error_message or "")
    await client.aclose()


@pytest.mark.asyncio
async def test_gemini_generate_suggestions_mock():
    """Verifies candidate parsing and structured suggestion extraction from Gemini API response."""
    test_file = FileMetadata(
        id=generate_file_id("annual_report.pdf"),
        original_rel_path="annual_report.pdf",
        filename="annual_report.pdf",
        extension="pdf",
        size_bytes=102400,
        modified_at="2026-10-22T00:00:00Z",
    )

    gemini_response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "suggestions": [
                                    {
                                        "id": test_file.id,
                                        "category": "Corporate Reports",
                                        "suggested_name": "2026_annual_report.pdf",
                                        "reason": "Annual corporate summary",
                                    }
                                ]
                            })
                        }
                    ]
                }
            }
        ]
    }

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-goog-api-key") == "test_key"
        assert ":generateContent" in str(request.url)
        return httpx.Response(200, json=gemini_response_payload)

    transport = httpx.MockTransport(mock_handler)
    client = httpx.AsyncClient(transport=transport)

    provider = GeminiProvider(api_key="test_key", client=client)
    suggestions = await provider.generate_suggestions([test_file])

    assert len(suggestions) == 1
    assert suggestions[0].file_id == test_file.id
    assert suggestions[0].suggested_category == "Corporate Reports"
    assert suggestions[0].suggested_filename == "2026_annual_report.pdf"
    await client.aclose()


@pytest.mark.asyncio
async def test_gemini_rate_limit_429_mock():
    """Verifies that HTTP 429 produces an actionable rate-limit error."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Resource exhausted"}})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.AsyncClient(transport=transport)

    provider = GeminiProvider(api_key="test_key", client=client)
    test_file = FileMetadata(
        id="f1",
        original_rel_path="f.txt",
        filename="f.txt",
        extension="txt",
        size_bytes=10,
        modified_at="2026-10-22T00:00:00Z",
    )

    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        await provider.generate_suggestions([test_file])
    await client.aclose()
