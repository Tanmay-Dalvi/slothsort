# SlothSort Implementation Plan

> **Hacktoberfest 2026 Challenge:** Week 3 Open-Source AI Challenge — *"Slow and Steady"*
> **Development Target:** A demonstrable, robust local-first desktop organizer.

---

## 1. Smallest Credible MVP (Minimum Viable Product)

To deliver a compelling, high-quality solution without overengineering, the MVP scope is strictly defined:

```
[Target Folder Input]
       │
       ▼
[Directory Scan & File Counter]
       │
       ▼
[Local Ollama (gemma3:1b) Categorization]
       │
       ▼
[Interactive Diff Table & Collision Warning]
       │
       ▼
[User Approval ("Apply Changes")]
       │
       ▼
[Atomic Execution + 1-Click Rollback ("Undo")]
```

### Core MVP Deliverables:
1. **Directory Scanner**: Scans a user-supplied directory path on Ubuntu/Linux. Skips hidden files (`.git`, `node_modules`).
2. **Deterministic Safety Engine**: Path containment enforcement, collision detection, and zero auto-deletions.
3. **Local AI Integration**: Connects to existing local Ollama daemon (`gemma3:1b`) with JSON mode, batching files in groups of 15.
4. **Mock Provider**: Instant out-of-the-box fallback for headless test runners.
5. **Interactive Web UI**: Modern, calming forest-green UI with:
   - Folder selector input
   - Discovered files summary (count, types, size)
   - Proposed target folders and cleaned filenames
   - Checkbox toggles to approve/reject individual files
   - Clear warning badges on destination collisions
   - "Apply Changes" button with progress indicator
   - "Undo Last Batch" button that restores original file locations
6. **Gemini Integration Ready**: Provider scaffolding and configuration in place with clear privacy badges.

---

## 2. Phased Roadmap

### Phase 1: Architecture, Safety, & Provider Strategy *(Current Phase — Complete)*
- [x] Environment inspection: Python 3.14, Node v24, Ollama 0.34.0, `gemma3:1b` model verified.
- [x] Document architecture (`docs/ARCHITECTURE.md`).
- [x] Document safety model & 10 invariants (`docs/SAFETY_MODEL.md`).
- [x] Document dual AI provider strategy (`docs/AI_PROVIDER_STRATEGY.md`).
- [x] Define phased implementation roadmap (`docs/IMPLEMENTATION_PLAN.md`).
- [x] Author comprehensive `README.md`.

---

### Phase 2: Core Backend Engine & Safety Subsystem
**Goal:** Build the rock-solid, fully tested deterministic engine that guarantees data safety before any AI touches it.
- **Tasks**:
  1. Initialize Python project (`pyproject.toml`, virtual environment, dependencies: `fastapi`, `uvicorn`, `pydantic`, `httpx`, `pytest`).
  2. Implement `FileMetadata` and `ScanResult` models.
  3. Implement `FolderScanner`:
     - Safe recursive traversal with depth limits.
     - Exclusion of dotfiles, `.git`, `node_modules`, symlink loop detection.
  4. Implement `PlanValidator`:
     - Canonical path resolution.
     - Containment assertion (`is_relative_to(root)`).
     - Intra-batch duplicate destination detection.
     - Pre-existing file collision detection.
  5. Implement `PlanExecutor`:
     - Atomic file moves.
     - Directory creation with rollback tracking.
     - Structured JSON Undo manifest generation.
  6. Implement `UndoEngine`:
     - Manifest reading and inverse-order rollback.
     - Clean deletion of newly created empty directories.
  7. Write comprehensive unit test suite:
     - `test_scanner.py`: Normal files, empty folders, symlinks.
     - `test_validator.py`: Path traversal attempts (`../`), destination collisions, existing file collisions.
     - `test_executor.py`: Successful moves, transactional rollback, undo execution.

---

### Phase 3: AI Provider Subsystem
**Goal:** Implement the interchangeable AI layer with Ollama and Gemini connectors.
- **Tasks**:
  1. Define `AIProvider` base class and standard `FileSuggestion` schema.
  2. Implement `MockAIProvider` with heuristic categorization for CI testing.
  3. Implement `OllamaProvider`:
     - Async client using `httpx`.
     - Connection to `http://localhost:11434/api/generate`.
     - Parameterization: model `gemma3:1b`, `format: "json"`, chunked batches (15 files).
     - Structured output parsing with regex code-fence stripping.
  4. Implement `GeminiProvider`:
     - Async client connecting to Google Gemini REST / SDK.
     - Model: `gemini-2.5-flash`.
     - Key loading from `GEMINI_API_KEY`.
     - Graceful handling when key is missing or invalid.
  5. Implement `ProviderManager`:
     - Health checks for both providers (`GET /api/providers`).
     - Explicit provider dispatch without auto-fallback.
  6. Write automated tests:
     - `test_mock_provider.py`
     - `test_ollama_provider.py` (live test against local Ollama + mock test).
     - `test_gemini_provider.py` (mocked HTTP response test).

---

### Phase 4: REST API & Service Layer
**Goal:** Expose clean, typed endpoints connecting the engine and providers to the frontend.
- **Tasks**:
  1. Create FastAPI application (`backend/app/main.py`) with CORS middleware.
  2. Implement routers:
     - `/api/scan`: Run scanner on provided directory path.
     - `/api/providers`: Check health and status of Ollama & Gemini.
     - `/api/plan/generate`: Generate proposals using selected provider.
     - `/api/plan/validate`: Validate user-edited changes.
     - `/api/plan/execute`: Apply approved operations and write manifest.
     - `/api/undo`: Roll back operations using manifest ID.
     - `/api/history`: List previous undo manifests.
  3. Implement integration tests using `httpx.AsyncClient` + `pytest`.

---

### Phase 5: Modern Responsive Web UI
**Goal:** Build a calming, high-polish interface reflecting the SlothSort aesthetic.
- **Design Tokens & Palette**:
  - Primary Background: Warm cream (`#F9F8F5`, `#F3EFE6`)
  - Primary Brand: Calm forest green (`#1B4332`, `#2D6A4F`, `#40916C`)
  - Accents: Soft moss/lime (`#74C69D`, `#52B788`)
  - Dark/Text: Deep slate (`#1E293B`, `#334155`)
  - Warnings/Collisions: Warm amber (`#D97706`) and soft coral (`#DC2626`)
- **Key UI Components**:
  1. **Header & Provider Pill**:
     - Sloth logo/icon.
     - Provider switcher (Ollama 🟢 Local vs Gemini ☁️ Cloud).
     - Privacy disclosure badge.
  2. **Folder Selection Panel**:
     - Path input with quick presets (`~/Downloads`, test folders).
     - "Scan Folder" trigger.
  3. **Folder Overview & Statistics**:
     - File count, total size, file type distribution badges.
  4. **Organization Diff Table**:
     - Original filename and location $\to$ Proposed Category & Clean Filename.
     - Inline editable input for category and filename.
     - Collision alert badges (`⚠️ Destination exists`).
     - Per-file include/exclude checkbox.
     - Select all / deselect all.
  5. **Action Bar & Safety Controls**:
     - Count of approved files to move.
     - Prominent "Apply Changes" button (disabled if collisions unresolved).
     - Execution progress indicator.
  6. **Undo & History Drawer**:
     - Notification after completion with immediate "Undo" button.
     - History view showing previous batches and rollback status.

---

### Phase 6: End-to-End Verification, Benchmarking, & Polish
**Goal:** Verify complete workflows on real directories, test error boundaries, and produce presentation-ready documentation.
- **Tasks**:
  1. Generate realistic test directory (`test_data/messy_desktop`) with mixed downloads, screenshots, invoices, and source files.
  2. Run end-to-end organize cycle with local Ollama (`gemma3:1b`).
  3. Verify execution and check filesystem state.
  4. Run Undo and verify 100% byte-for-byte restoration.
  5. Test edge cases:
     - Disconnecting Ollama server mid-scan.
     - Special characters in filenames (`spaces`, `#`, `&`, `[brackets]`).
     - Overwrite collision resolution.
     - Read-only files.
  6. Polish README with screenshots, quickstart, and demo guide.

---

## 3. Risk Matrix & Mitigations

| Identified Risk | Severity | Probability | Mitigation Strategy |
|---|---|---|---|
| **JSON malformation from 1B model** | High | Medium | Enforce Ollama `"format": "json"`, batch in chunks of 15 files, and use multi-stage regex JSON extraction fallback. |
| **Silent data loss or accidental overwrite** | Critical | Low | Hardcode `assert not target.exists()` immediately before every move; zero delete primitives in engine; undo manifest. |
| **Path traversal via malicious/hallucinated relative paths** | Critical | Low | Strict `is_relative_to` containment checks on canonicalized paths. Any `..` path is stripped and rejected. |
| **Ollama unavailable on user machine** | Medium | Medium | Clear UI error banner explaining how to start Ollama; mock provider enables app testing even without Ollama. |
| **High latency on low-end hardware** | Medium | Low | `gemma3:1b` is optimized for speed (< 500ms per batch on local hardware); UI shows progressive batch completion. |
| **Node.js PATH resolution in non-standard environments** | Low | Low | Document explicit PATH export and include simple Makefile / start scripts. |
