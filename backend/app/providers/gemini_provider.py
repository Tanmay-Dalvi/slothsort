"""Hosted Google Gemini AI provider with strict privacy boundaries and secret management."""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.app.config import settings
from backend.app.models.file import FileMetadata
from backend.app.models.plan import FileSuggestion, OrganizationOptions
from backend.app.providers.base import AIProvider, ProviderHealth
from backend.app.providers.ollama_provider import parse_structured_json

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(AIProvider):
    """
    Hosted Google Gemini AI provider.

    Guarantees:
    - API keys are read strictly from backend environment configuration.
    - API keys are NEVER returned in API responses, logs, or exceptions.
    - Zero file contents are sent; only minimal metadata (name, ext, size).
    - Clearly discloses cloud transmission in health and privacy reports.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 30.0,
        batch_size: int = 15,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds
        self.batch_size = max(1, min(batch_size, settings.MAX_BATCH_SIZE))
        self._external_client = client

    def __repr__(self) -> str:
        # Prevent key leakage in logs or representations
        has_key = bool(self._api_key and self._api_key.strip())
        return f"<GeminiProvider(model='{self.model}', is_configured={has_key})>"

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self.model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        return httpx.AsyncClient(timeout=self.timeout_seconds)

    async def check_health(self) -> ProviderHealth:
        """
        Verifies API key presence and model availability against the Gemini API.
        """
        if not self.is_configured:
            return ProviderHealth(
                is_available=False,
                provider_name="Google Gemini",
                model_name=self.model,
                latency_ms=0.0,
                error_message=(
                    "GEMINI_API_KEY is not configured in backend environment. "
                    "Set GEMINI_API_KEY to enable Hosted Gemini mode."
                ),
                is_cloud=True,
                privacy_notice=(
                    "☁️ Cloud API: When enabled, file metadata (names, sizes, types) is sent "
                    "securely over HTTPS to Google Gemini. File contents are NEVER sent."
                ),
            )

        start_time = time.perf_counter()
        # Verify model status via models/{model} endpoint using header authentication
        model_url = f"{GEMINI_BASE_URL}/models/{self.model}"
        headers = {"x-goog-api-key": self._api_key.strip()}

        client = self._get_client()
        should_close = self._external_client is None

        try:
            response = await client.get(model_url, headers=headers)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if response.status_code == 200:
                return ProviderHealth(
                    is_available=True,
                    provider_name="Google Gemini",
                    model_name=self.model,
                    latency_ms=round(latency_ms, 1),
                    is_cloud=True,
                    privacy_notice=(
                        "☁️ Cloud API Active: File metadata (names, sizes, extensions) is transmitted "
                        "over HTTPS to Google Gemini. File contents are NEVER uploaded."
                    ),
                )
            elif response.status_code in (401, 403):
                return ProviderHealth(
                    is_available=False,
                    provider_name="Google Gemini",
                    model_name=self.model,
                    latency_ms=round(latency_ms, 1),
                    error_message="Invalid GEMINI_API_KEY or unauthorized access.",
                    is_cloud=True,
                    privacy_notice="☁️ Cloud API: Authorization failure.",
                )
            elif response.status_code == 404:
                return ProviderHealth(
                    is_available=False,
                    provider_name="Google Gemini",
                    model_name=self.model,
                    latency_ms=round(latency_ms, 1),
                    error_message=f"Configured Gemini model '{self.model}' was not found in user account or API.",
                    is_cloud=True,
                    privacy_notice="☁️ Cloud API: Model not found.",
                )
            elif response.status_code == 429:
                return ProviderHealth(
                    is_available=False,
                    provider_name="Google Gemini",
                    model_name=self.model,
                    latency_ms=round(latency_ms, 1),
                    error_message="Google Gemini API rate limit exceeded.",
                    is_cloud=True,
                    privacy_notice="☁️ Cloud API: Rate limited.",
                )
            else:
                return ProviderHealth(
                    is_available=False,
                    provider_name="Google Gemini",
                    model_name=self.model,
                    latency_ms=round(latency_ms, 1),
                    error_message=f"Gemini API returned unexpected status {response.status_code}.",
                    is_cloud=True,
                    privacy_notice="☁️ Cloud API: Unexpected status.",
                )

        except (httpx.ConnectError, httpx.ConnectTimeout):
            return ProviderHealth(
                is_available=False,
                provider_name="Google Gemini",
                model_name=self.model,
                latency_ms=0.0,
                error_message="Network error: Unable to connect to Google Gemini API servers.",
                is_cloud=True,
                privacy_notice="☁️ Cloud API: Connection error.",
            )
        except Exception as e:
            return ProviderHealth(
                is_available=False,
                provider_name="Google Gemini",
                model_name=self.model,
                latency_ms=0.0,
                error_message=f"Gemini health check failed: {str(e)}",
                is_cloud=True,
                privacy_notice="☁️ Cloud API: Health check failed.",
            )
        finally:
            if should_close:
                await client.aclose()

    def _build_prompt(
        self,
        files_batch: List[FileMetadata],
        options: OrganizationOptions,
    ) -> str:
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
            naming_instruction = "Normalize filename to clean snake_case (e.g. 'report_2026.pdf')."
        elif options.naming_convention == "clean_kebab":
            naming_instruction = "Normalize filename to clean kebab-case (e.g. 'report-2026.pdf')."

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
        if not self.is_configured:
            raise ValueError(
                "GEMINI_API_KEY is not configured in backend environment. "
                "Set GEMINI_API_KEY to use Hosted Gemini mode."
            )

        prompt = self._build_prompt(batch, options)
        endpoint = f"{GEMINI_BASE_URL}/models/{self.model}:generateContent"
        headers = {
            "x-goog-api-key": self._api_key.strip(),
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }

        client = self._get_client()
        should_close = self._external_client is None

        try:
            response = await client.post(endpoint, headers=headers, json=payload)
        except httpx.ConnectError:
            raise RuntimeError("Network error connecting to Google Gemini API servers.")
        except httpx.TimeoutException:
            raise RuntimeError(f"Gemini API request timed out after {self.timeout_seconds}s.")
        except Exception as e:
            raise RuntimeError(f"Gemini request error: {str(e)}")
        finally:
            if should_close:
                await client.aclose()

        if response.status_code == 429:
            raise RuntimeError(
                "Google Gemini API rate limit exceeded. Please wait a moment or switch to Local Ollama."
            )
        elif response.status_code in (401, 403):
            raise RuntimeError("Google Gemini API authentication failed. Verify your GEMINI_API_KEY.")
        elif response.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {response.status_code}: {response.text[:120]}")

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini API returned no candidates or response was blocked by safety filters.")

        candidate = candidates[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        if not content_parts:
            raise RuntimeError("Gemini candidate contains empty content parts.")

        raw_text = content_parts[0].get("text", "")
        parsed = parse_structured_json(raw_text)

        suggestions_list: List[Dict[str, Any]] = []
        if isinstance(parsed, dict):
            for key in ("suggestions", "files", "items", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    suggestions_list = parsed[key]
                    break
            if not suggestions_list and "id" in parsed:
                suggestions_list = [parsed]
        elif isinstance(parsed, list):
            suggestions_list = parsed

        suggestions_by_id: Dict[str, Dict[str, Any]] = {}
        for item in suggestions_list:
            if isinstance(item, dict):
                f_id = str(item.get("id") or item.get("file_id") or "")
                if f_id:
                    suggestions_by_id[f_id] = item

        batch_results: List[FileSuggestion] = []
        for f in batch:
            item = suggestions_by_id.get(f.id)
            if item:
                cat = str(item.get("category") or item.get("suggested_category") or "Miscellaneous").strip()
                name = str(item.get("suggested_name") or item.get("suggested_filename") or f.filename).strip()
                reason = str(item.get("reason") or item.get("reasoning") or "").strip()
            else:
                cat = "Miscellaneous"
                name = f.filename
                reason = "Fallback: File omitted from cloud model response"

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
        if not files:
            return []

        opts = options or OrganizationOptions()
        all_suggestions: List[FileSuggestion] = []

        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            batch_suggestions = await self._generate_batch(batch, opts)
            all_suggestions.extend(batch_suggestions)

        return all_suggestions
