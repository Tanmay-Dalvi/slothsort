"""Local Ollama AI provider using open-weight models."""

import json
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.app.config import settings
from backend.app.models.file import FileMetadata
from backend.app.models.plan import FileSuggestion, OrganizationOptions
from backend.app.providers.base import AIProvider, ProviderHealth


def parse_structured_json(raw_text: str) -> Any:
    """
    Defensively extracts and parses JSON from raw LLM output.
    Handles markdown codeblocks, preamble/postamble chatter, and nested structures.
    """
    text = raw_text.strip()
    if not text:
        raise ValueError("Model returned empty response text")

    # Strip markdown code fencing if present (e.g. ```json ... ``` or ``` ...)
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    # Attempt 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find outermost JSON object { ... } or array [ ... ]
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Unable to parse structured JSON from model response: {raw_text[:120]}...")


class OllamaProvider(AIProvider):
    """
    Local AI provider communicating with an Ollama daemon.

    Default configuration:
    - Base URL: http://localhost:11434
    - Default Model: gemma3:1b
    - Privacy: 100% offline, zero data transmitted over external networks.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 45.0,
        batch_size: int = 15,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds
        self.batch_size = max(1, min(batch_size, settings.MAX_BATCH_SIZE))
        self._external_client = client

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self.model

    def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        return httpx.AsyncClient(timeout=self.timeout_seconds)

    async def check_health(self) -> ProviderHealth:
        """
        Queries Ollama's /api/tags endpoint to verify daemon connectivity
        and check whether the configured model is installed locally.
        """
        start_time = time.perf_counter()
        tags_url = f"{self.base_url}/api/tags"

        try:
            client = self._get_client()
            should_close = self._external_client is None
            try:
                response = await client.get(tags_url)
            finally:
                if should_close:
                    await client.aclose()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if response.status_code != 200:
                return ProviderHealth(
                    is_available=False,
                    provider_name="Local Ollama",
                    model_name=self.model,
                    latency_ms=latency_ms,
                    error_message=f"Ollama returned HTTP {response.status_code}: {response.text[:100]}",
                    is_cloud=False,
                    privacy_notice="100% Local (Zero network requests leave this machine)",
                )

            data = response.json()
            models_list = data.get("models", [])

            # Check if self.model is in the installed models list
            # Handles 'gemma3:1b', 'gemma3:1b-latest', or bare names
            model_found = False
            for m in models_list:
                name = m.get("name", "")
                model_attr = m.get("model", "")
                if (
                    name == self.model
                    or name.startswith(f"{self.model}:")
                    or model_attr == self.model
                    or self.model in name
                ):
                    model_found = True
                    break

            if not model_found:
                installed_names = [m.get("name", "") for m in models_list[:5]]
                return ProviderHealth(
                    is_available=False,
                    provider_name="Local Ollama",
                    model_name=self.model,
                    latency_ms=latency_ms,
                    error_message=(
                        f"Model '{self.model}' is not installed in local Ollama. "
                        f"Run 'ollama run {self.model}' in your terminal to install it. "
                        f"(Found: {', '.join(installed_names) or 'none'})"
                    ),
                    is_cloud=False,
                    privacy_notice="100% Local (Zero network requests leave this machine)",
                )

            return ProviderHealth(
                is_available=True,
                provider_name="Local Ollama",
                model_name=self.model,
                latency_ms=round(latency_ms, 1),
                is_cloud=False,
                privacy_notice="100% Local (Zero network requests leave this machine)",
            )

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            return ProviderHealth(
                is_available=False,
                provider_name="Local Ollama",
                model_name=self.model,
                latency_ms=0.0,
                error_message=(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Ensure Ollama is running ('ollama serve')."
                ),
                is_cloud=False,
                privacy_notice="100% Local (Zero network requests leave this machine)",
            )
        except Exception as e:
            return ProviderHealth(
                is_available=False,
                provider_name="Local Ollama",
                model_name=self.model,
                latency_ms=0.0,
                error_message=f"Ollama health check failed: {str(e)}",
                is_cloud=False,
                privacy_notice="100% Local (Zero network requests leave this machine)",
            )

    def _build_prompt(
        self,
        files_batch: List[FileMetadata],
        options: OrganizationOptions,
    ) -> str:
        """
        Constructs a structured prompt containing only file metadata.
        Explicitly asks for a JSON object with a 'suggestions' array.
        """
        metadata_payload = [
            {
                "id": f.id,
                "name": f.filename,
                "ext": f.extension,
                "size_bytes": f.size_bytes,
            }
            for f in files_batch
        ]

        naming_instruction = "Preserve the original filename."
        if options.naming_convention == "clean_snake":
            naming_instruction = "Normalize filename to clean snake_case (e.g. 'my_receipt_2026.pdf')."
        elif options.naming_convention == "clean_kebab":
            naming_instruction = "Normalize filename to clean kebab-case (e.g. 'my-receipt-2026.pdf')."

        custom_part = f"Custom guidance: {options.custom_instructions}\n" if options.custom_instructions else ""

        return (
            f"You are SlothSort's folder organization specialist.\n"
            f"Organize the following files into at most {options.max_categories} logical categories "
            f"(e.g., Documents, Images, Code, Invoices, Archives, Media, Miscellaneous).\n"
            f"Naming rule: {naming_instruction}\n"
            f"{custom_part}"
            f"Return ONLY valid JSON matching this schema:\n"
            f'{{\n'
            f'  "suggestions": [\n'
            f'    {{\n'
            f'      "id": "file_id",\n'
            f'      "category": "CategoryName",\n'
            f'      "suggested_name": "clean_filename.ext",\n'
            f'      "reason": "Brief reason"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n\n'
            f"Files to organize:\n{json.dumps(metadata_payload, indent=2)}"
        )

    async def _generate_batch(
        self,
        batch: List[FileMetadata],
        options: OrganizationOptions,
    ) -> List[FileSuggestion]:
        """Runs inference for a single batch of file metadata."""
        prompt = self._build_prompt(batch, options)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        endpoint = f"{self.base_url}/api/generate"
        client = self._get_client()
        should_close = self._external_client is None

        try:
            response = await client.post(endpoint, json=payload)
        except httpx.ConnectError:
            raise RuntimeError(
                f"Failed to connect to local Ollama at {self.base_url}. "
                "Please make sure the Ollama service is running ('ollama serve')."
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama inference timed out after {self.timeout_seconds}s for batch of {len(batch)} files."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama request error: {str(e)}")
        finally:
            if should_close:
                await client.aclose()

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama returned HTTP error {response.status_code}: {response.text[:150]}"
            )

        data = response.json()
        raw_response = data.get("response", "")

        parsed = parse_structured_json(raw_response)
        suggestions_list: List[Dict[str, Any]] = []

        if isinstance(parsed, dict):
            # Model returned {"suggestions": [...]} or {"files": [...]}
            for key in ("suggestions", "files", "items", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    suggestions_list = parsed[key]
                    break
            if not suggestions_list and "id" in parsed:
                suggestions_list = [parsed]
        elif isinstance(parsed, list):
            suggestions_list = parsed

        # Index suggestions by file id
        suggestions_by_id: Dict[str, Dict[str, Any]] = {}
        for item in suggestions_list:
            if isinstance(item, dict):
                f_id = str(item.get("id") or item.get("file_id") or "")
                if f_id:
                    suggestions_by_id[f_id] = item

        # Build validated FileSuggestion objects for each file in this batch
        batch_results: List[FileSuggestion] = []
        for f in batch:
            item = suggestions_by_id.get(f.id)
            if item:
                cat = str(item.get("category") or item.get("suggested_category") or "Miscellaneous").strip()
                name = str(item.get("suggested_name") or item.get("suggested_filename") or f.filename).strip()
                reason = str(item.get("reason") or item.get("reasoning") or "").strip()
            else:
                # Fallback if model missed this specific file in the JSON
                cat = "Miscellaneous"
                name = f.filename
                reason = "Fallback: File omitted from model response"

            # Retain original extension if model stripped it
            if f.extension and not name.lower().endswith(f".{f.extension.lower()}"):
                name = f"{name}.{f.extension}"

            batch_results.append(
                FileSuggestion(
                    file_id=f.id,
                    suggested_category=cat or "Miscellaneous",
                    suggested_filename=name or f.filename,
                    reasoning=reason,
                )
            )

        return batch_results

    async def generate_suggestions(
        self,
        files: List[FileMetadata],
        options: Optional[OrganizationOptions] = None,
    ) -> List[FileSuggestion]:
        """
        Batches files into chunks of 15-20 files and queries Ollama sequentially.
        Guarantees that only file metadata is sent, never file contents.
        """
        if not files:
            return []

        opts = options or OrganizationOptions()
        all_suggestions: List[FileSuggestion] = []

        # Process in chunks of self.batch_size
        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            batch_suggestions = await self._generate_batch(batch, opts)
            all_suggestions.extend(batch_suggestions)

        return all_suggestions
