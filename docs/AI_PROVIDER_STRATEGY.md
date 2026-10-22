# SlothSort AI Provider Strategy

> **Design Philosophy:** Open-weight first, privacy guaranteed, modular cloud expansion, zero silent delegation.

---

## 1. Motivation & Challenge Alignment

SlothSort is engineered for the Hacktoberfest 2026 Week 3 Open-Source AI Challenge: **“Slow and Steady”**. The challenge emphasizes open-weight, locally runnable AI that respects user privacy, minimizes power consumption, and operates reliably on consumer laptops without recurring subscription fees or cloud lock-in.

At the same time, practical desktop utilities must offer flexibility for users who prefer hosted inference or who run devices with extreme resource constraints. SlothSort fulfills both requirements through a **strict dual-provider abstraction**.

---

## 2. The AI Provider Interface

Both local and hosted providers implement a unified Python protocol:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class ProviderHealth(BaseModel):
    is_available: bool
    provider_name: str
    model_name: str
    latency_ms: float
    error_message: str | None = None
    privacy_notice: str

class OrganizationOptions(BaseModel):
    max_categories: int = 6
    naming_convention: str = "preserve"  # "preserve" | "clean_kebab" | "date_prefix"
    custom_instructions: str | None = None

class AIProvider(ABC):
    """Abstract interface defining required provider behavior."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier, e.g. 'ollama' or 'gemini'."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Verify model availability and measure baseline latency."""
        pass

    @abstractmethod
    async def generate_suggestions(
        self,
        files: List[Dict[str, Any]],
        options: OrganizationOptions
    ) -> List[Dict[str, Any]]:
        """
        Analyze a batch of file metadata and propose categories and filenames.
        Must return a structured list of suggestions matching FileSuggestion schema.
        """
        pass
```

Neither the file-scanning engine, the collision validator, the execution engine, nor the React frontend has any direct coupling to Ollama or Google Gemini APIs. Changing providers is a single parameter switch in the request payload.

---

## 3. Provider A: Local Open-Weight Mode (Ollama + gemma3:1b)

### 3.1 Role & Environment
- **Default & Primary Mode**: Selected out-of-the-box.
- **Model**: `gemma3:1b` (Google Gemma 3, 1-billion parameter instruction-tuned model, Q4_K_M quantization).
- **Daemon Endpoint**: `http://localhost:11434/api/generate`
- **Memory Footprint**: ~806 MB VRAM / RAM.
- **Latency**: ~300ms–800ms per batch.
- **Privacy Assurance**: 100% offline. Zero network packets leave the machine.

### 3.2 Structured Output Optimization
Small language models (1B parameters) can hallucinate or omit closing brackets if prompts are unstructured. To guarantee deterministic output with `gemma3:1b`:
1. **Ollama JSON Mode**: Send `"format": "json"` in the API payload.
2. **Batching**: Files are chunked into batches of **15 to 20 files** per prompt. This prevents context exhaustion and keeps response latencies snappy.
3. **Defensive Parsing Pipeline**:
   ```python
   def parse_model_json(raw_text: str) -> dict:
       # Strip markdown codeblocks if model wraps output in ```json ... ```
       cleaned = raw_text.strip()
       if cleaned.startswith("```"):
           cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
           cleaned = re.sub(r"\n?```$", "", cleaned)

       # First attempt: direct json.loads
       try:
           return json.loads(cleaned)
       except json.JSONDecodeError:
           # Fallback: extract the outermost {...} or [...] using regex
           match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
           if match:
               return json.loads(match.group(1))
           raise ValueError(f"Unable to parse structured JSON from model: {raw_text[:100]}...")
   ```

### 3.3 Prompt Architecture for `gemma3:1b`
```text
System:
You are SlothSort's folder organization specialist.
Organize the provided files into at most 5 logical categories (e.g., Documents, Invoices, Code, Images, Archives).
Suggest clean, standardized filenames (snake_case or kebab-case, preserve original extension).
Return ONLY valid JSON matching this schema:
{
  "suggestions": [
    {
      "id": "file_id_string",
      "category": "CategoryName",
      "suggested_name": "clean_filename.ext",
      "reason": "Brief rationale"
    }
  ]
}

User:
Files to organize:
[
  {"id": "f1", "name": "IMG_20261010_1105.jpg", "ext": "jpg", "size_kb": 2400},
  {"id": "f2", "name": "invoice_oct_draft.pdf", "ext": "pdf", "size_kb": 120}
]
```

---

## 4. Provider B: Hosted API Mode (Google Gemini)

### 4.1 Role & Environment
- **Optional Cloud Provider**: For users wanting hosted inference or who lack local computing headroom.
- **Default Cloud Model**: `gemini-2.5-flash` or `gemini-1.5-flash`.
- **API Key Configuration**:
  - Read from `GEMINI_API_KEY` environment variable or backend configuration file (`~/.config/slothsort/config.json`).
  - **Never** hardcoded.
  - **Never** committed to version control.
  - **Never** exposed to or handled by the browser frontend.

### 4.2 Privacy & Transparency Policy
1. **Explicit Selection Only**:
   - SlothSort will **never silently fallback** from Ollama to Gemini or vice-versa.
   - Switching to Gemini requires explicit user selection in the UI.
2. **Clear UI Privacy Disclosure**:
   - The UI displays an active badge:
     > ☁️ **Hosted Gemini Active:** Filenames and file sizes will be transmitted over HTTPS to the Google Gemini API. File contents are NOT uploaded.
3. **Zero Content Transmission**:
   - Only sanitized metadata (relative name, extension, byte size, timestamp) is sent.

---

## 5. Mock AI Provider (Deterministic Testing)

### 5.1 Role
- Ships with the codebase for automated unit testing, CI pipelines, and instant local demoing without requiring a running Ollama daemon or an active Google API key.

### 5.2 Deterministic Heuristics
- Maps standard file extensions to categories:
  - `.pdf`, `.docx`, `.txt`, `.md` $\to$ `Documents`
  - `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg` $\to$ `Images`
  - `.zip`, `.tar.gz`, `.tar`, `.7z` $\to$ `Archives`
  - `.py`, `.ts`, `.tsx`, `.js`, `.json` $\to$ `Development`
  - `.mp3`, `.wav`, `.flac`, `.mp4`, `.mkv` $\to$ `Media`
- Standardizes names: replaces spaces with underscores, normalizes lowercase extensions.

---

## 6. Provider Comparison & Selection Guide

| Dimension | Local Ollama (`gemma3:1b`) | Hosted Google Gemini (`gemini-2.5-flash`) | Mock Provider |
|---|---|---|---|
| **Privacy** | 100% Offline, Zero external data | Cloud HTTPS (metadata only) | 100% Offline |
| **API Key Required** | None | Yes (`GEMINI_API_KEY`) | None |
| **Network Required** | No | Yes | No |
| **Hardware Overhead** | ~806 MB RAM/VRAM | < 1 MB local RAM | < 1 MB local RAM |
| **Batch Latency** | ~400–800 ms | ~600–1200 ms | < 5 ms |
| **Categorization Depth** | Semantic file names | Deep semantic & multi-language | Rule-based heuristics |
| **Test Suitability** | Integration tests | Opt-in integration tests | Unit tests & CI |

---

## 7. Configuration & Secret Management

Configuration is loaded from environment variables and an optional user settings file:

```text
# Environment Variables (.env / system env)
SLOTHSORT_DEFAULT_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="gemma3:1b"
GEMINI_API_KEY=""                # Optional; required only when using Gemini mode
GEMINI_MODEL="gemini-2.5-flash"
SLOTHSORT_HOST="127.0.0.1"
SLOTHSORT_PORT="8000"
```

The frontend queries `GET /api/providers` to check which providers are configured and healthy:
```json
[
  {
    "id": "ollama",
    "name": "Local Ollama (gemma3:1b)",
    "available": true,
    "is_cloud": false,
    "privacy_label": "100% Local & Private"
  },
  {
    "id": "gemini",
    "name": "Google Gemini (gemini-2.5-flash)",
    "available": false,
    "is_cloud": true,
    "privacy_label": "Cloud API (Sends filenames & metadata)"
  }
]
```
If `GEMINI_API_KEY` is absent, the Gemini option is disabled with a helpful tooltip: *"Set GEMINI_API_KEY in environment to enable."*
