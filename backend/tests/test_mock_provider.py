"""Tests for MockAIProvider and schema validation."""

import pytest

from backend.app.models.file import FileMetadata, generate_file_id
from backend.app.models.plan import OrganizationOptions
from backend.app.providers.mock_provider import MockAIProvider


@pytest.mark.asyncio
async def test_mock_provider_health():
    """Verifies mock provider health check."""
    provider = MockAIProvider()
    health = await provider.check_health()

    assert health.is_available is True
    assert health.is_cloud is False
    assert health.model_name == "deterministic-rules-v1"
    assert health.latency_ms > 0


@pytest.mark.asyncio
async def test_mock_provider_categorization():
    """Verifies that diverse extensions map to correct categories."""
    provider = MockAIProvider()

    files = [
        FileMetadata(
            id=generate_file_id("tax_2025.pdf"),
            original_rel_path="tax_2025.pdf",
            filename="tax_2025.pdf",
            extension="pdf",
            size_bytes=1000,
            modified_at="2026-10-22T00:00:00Z",
        ),
        FileMetadata(
            id=generate_file_id("sunset.png"),
            original_rel_path="sunset.png",
            filename="sunset.png",
            extension="png",
            size_bytes=2000,
            modified_at="2026-10-22T00:00:00Z",
        ),
        FileMetadata(
            id=generate_file_id("backup.zip"),
            original_rel_path="backup.zip",
            filename="backup.zip",
            extension="zip",
            size_bytes=3000,
            modified_at="2026-10-22T00:00:00Z",
        ),
        FileMetadata(
            id=generate_file_id("app.py"),
            original_rel_path="app.py",
            filename="app.py",
            extension="py",
            size_bytes=400,
            modified_at="2026-10-22T00:00:00Z",
        ),
        FileMetadata(
            id=generate_file_id("song.mp3"),
            original_rel_path="song.mp3",
            filename="song.mp3",
            extension="mp3",
            size_bytes=5000,
            modified_at="2026-10-22T00:00:00Z",
        ),
    ]

    suggestions = await provider.generate_suggestions(files)
    assert len(suggestions) == 5

    cat_map = {s.file_id: s.suggested_category for s in suggestions}
    assert cat_map[files[0].id] == "Documents"
    assert cat_map[files[1].id] == "Images"
    assert cat_map[files[2].id] == "Archives"
    assert cat_map[files[3].id] == "Development"
    assert cat_map[files[4].id] == "Media"


@pytest.mark.asyncio
async def test_mock_provider_naming_conventions():
    """Verifies that naming conventions (preserve, clean_snake, clean_kebab) work as expected."""
    provider = MockAIProvider()

    file_meta = FileMetadata(
        id=generate_file_id("My Rough Draft 2026.docx"),
        original_rel_path="My Rough Draft 2026.docx",
        filename="My Rough Draft 2026.docx",
        extension="docx",
        size_bytes=1500,
        modified_at="2026-10-22T00:00:00Z",
    )

    # 1. Preserve
    s_preserve = await provider.generate_suggestions([file_meta], OrganizationOptions(naming_convention="preserve"))
    assert s_preserve[0].suggested_filename == "My Rough Draft 2026.docx"

    # 2. Clean snake
    s_snake = await provider.generate_suggestions([file_meta], OrganizationOptions(naming_convention="clean_snake"))
    assert s_snake[0].suggested_filename == "my_rough_draft_2026.docx"

    # 3. Clean kebab
    s_kebab = await provider.generate_suggestions([file_meta], OrganizationOptions(naming_convention="clean_kebab"))
    assert s_kebab[0].suggested_filename == "my-rough-draft-2026.docx"
