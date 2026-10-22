"""Tests for OllamaProvider: request construction, batching, parsing, and error handling."""

import json
from pathlib import Path
import pytest
import httpx

from backend.app.models.file import FileMetadata, generate_file_id
from backend.app.models.plan import OrganizationOptions
from backend.app.providers.ollama_provider import OllamaProvider, parse_structured_json


def test_parse_structured_json():
    """Tests defensive JSON parsing across clean, code-fenced, and noisy model outputs."""
    # 1. Clean JSON
    assert parse_structured_json('{"key": "value"}') == {"key": "value"}

    # 2. Markdown fenced JSON
    fenced = '```json\n{"suggestions": [{"id": "1", "category": "Docs"}]}\n```'
    parsed_fenced = parse_structured_json(fenced)
    assert "suggestions" in parsed_fenced

    # 3. Model commentary with embedded JSON
    noisy = 'Here is the plan:\n{"suggestions": []}\nHope that helps!'
    parsed_noisy = parse_structured_json(noisy)
    assert "suggestions" in parsed_noisy

    # 4. Invalid JSON raises ValueError
    with pytest.raises(ValueError, match="Unable to parse structured JSON"):
        parse_structured_json("I am sorry, but I cannot categorize these files.")


def test_ollama_build_prompt_metadata_only():
    """Verifies that prompt construction includes only file metadata and never file contents."""
    provider = OllamaProvider(batch_size=15)
    files = [
        FileMetadata(
            id=generate_file_id("taxes.pdf"),
            original_rel_path="taxes.pdf",
            filename="taxes.pdf",
            extension="pdf",
            size_bytes=45000,
            modified_at="2026-10-22T00:00:00Z",
        )
    ]
    prompt = provider._build_prompt(files, OrganizationOptions())

    assert "taxes.pdf" in prompt
    assert "45000" in prompt
    assert "suggestions" in prompt
    # Guarantee no binary or file contents
    assert "content" not in prompt.lower() or "custom guidance" in prompt.lower()


@pytest.mark.asyncio
async def test_ollama_batching():
    """Verifies that files are chunked according to batch_size."""
    batch_records = []

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        # Parse prompt to count items in batch
        prompt = data["prompt"]
        batch_records.append(prompt)
        return httpx.Response(
            200,
            json={
                "response": json.dumps({
                    "suggestions": [
                        {"id": f"f_{i}", "category": "BatchCat", "suggested_name": f"f_{i}.txt"}
                        for i in range(len(batch_records))
                    ]
                })
            },
        )

    transport = httpx.MockTransport(mock_handler)
    mock_client = httpx.AsyncClient(transport=transport)

    provider = OllamaProvider(batch_size=2, client=mock_client)

    # 5 files with batch size 2 should produce 3 batches (2 + 2 + 1)
    files = [
        FileMetadata(
            id=f"f_{i}",
            original_rel_path=f"file_{i}.txt",
            filename=f"file_{i}.txt",
            extension="txt",
            size_bytes=100,
            modified_at="2026-10-22T00:00:00Z",
        )
        for i in range(5)
    ]

    suggestions = await provider.generate_suggestions(files)
    assert len(batch_records) == 3
    assert len(suggestions) == 5
    await mock_client.aclose()


@pytest.mark.asyncio
async def test_ollama_timeout_handling():
    """Verifies graceful handling and descriptive error when Ollama times out."""
    def mock_timeout(request: httpx.Request):
        raise httpx.ReadTimeout("Read timed out")

    transport = httpx.MockTransport(mock_timeout)
    client = httpx.AsyncClient(transport=transport)
    provider = OllamaProvider(timeout_seconds=5.0, client=client)

    files = [
        FileMetadata(
            id="f1",
            original_rel_path="doc.pdf",
            filename="doc.pdf",
            extension="pdf",
            size_bytes=100,
            modified_at="2026-10-22T00:00:00Z",
        )
    ]

    with pytest.raises(RuntimeError, match="timed out"):
        await provider.generate_suggestions(files)
    await client.aclose()


@pytest.mark.asyncio
async def test_ollama_health_missing_model():
    """Verifies health check reports unavailable when configured model is not in /api/tags."""
    async def mock_tags(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]},
        )

    transport = httpx.MockTransport(mock_tags)
    client = httpx.AsyncClient(transport=transport)
    provider = OllamaProvider(model="gemma3:1b", client=client)

    health = await provider.check_health()
    assert health.is_available is False
    assert "not installed in local Ollama" in (health.error_message or "")
    await client.aclose()


@pytest.mark.asyncio
async def test_ollama_live_integration():
    """
    Live test against local Ollama if reachable and gemma3:1b is installed.
    Gracefully skips if Ollama daemon is offline.
    """
    provider = OllamaProvider(model="gemma3:1b", timeout_seconds=30.0)
    health = await provider.check_health()

    if not health.is_available:
        pytest.skip(f"Local Ollama (gemma3:1b) is not available: {health.error_message}")

    # Test small live batch
    files = [
        FileMetadata(
            id=generate_file_id("tax_statement_2026.pdf"),
            original_rel_path="tax_statement_2026.pdf",
            filename="tax_statement_2026.pdf",
            extension="pdf",
            size_bytes=52000,
            modified_at="2026-10-22T00:00:00Z",
        )
    ]

    suggestions = await provider.generate_suggestions(files)
    assert len(suggestions) == 1
    assert suggestions[0].file_id == files[0].id
    assert len(suggestions[0].suggested_category) > 0
    assert len(suggestions[0].suggested_filename) > 0
