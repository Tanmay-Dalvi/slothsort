# 🦥 SlothSort

> *"Let your laptop clean up after you."*

SlothSort is an open-source, privacy-conscious AI file organizer built for the **Hacktoberfest 2026 Week 3 Open-Source AI Challenge: "Slow and Steady"**.

Designed specifically for standard laptops (16 GB RAM, integrated graphics), SlothSort uses open-weight local AI (`gemma3:1b` via Ollama) to categorize messy folders and tidy file names without uploading your personal files to the cloud.

---

## 💡 The Problem & The SlothSort Solution

### The Problem
- **Desktop & Downloads Clutter:** Folders quickly turn into digital junk drawers filled with cryptically named receipts, loose screenshots, raw datasets, code snippets, and forgotten archives.
- **Organization Fatigue:** Manually triaging hundreds of files is tedious and overwhelming.
- **The Cloud AI Dilemma:** Existing cloud-based AI tools require uploading private documents, financial receipts, and proprietary source files to third-party servers, posing serious privacy and security risks.
- **Autonomous Agent Danger:** Giving autonomous AI agents unrestricted filesystem write or shell access often leads to accidental file deletions, overwrites, or broken paths.

### The SlothSort Solution
SlothSort adopts the **"Slow and Steady"** philosophy:
1. **Advisory AI, Deterministic Engine:** The AI proposes; deterministic Python verifies; the human approves; the engine executes reversibly. The AI never has direct write or delete permissions.
2. **Metadata-Only Processing:** Zero file contents or bytes are ever read. Only file names, extensions, sizes, and timestamps are analyzed.
3. **100% Local-First & Free:** Powered by Ollama and Google's lightweight `gemma3:1b` running locally on your laptop CPU/GPU. No subscriptions, no cloud lock-in.
4. **1-Click Instant Undo:** Every batch produces an atomic JSON transaction manifest that can be rolled back with one click, restoring files to their exact previous state.

---

## ✨ Key Highlights

- 🔒 **100% Privacy by Default:** Never reads file contents, and keeps all processing on your device.
- 🦥 **Local-First Open-Weight Intelligence:** Powered by Ollama and `gemma3:1b` locally. Works offline on airplanes or without an internet connection.
- ☁️ **Dual-Provider Architecture:** Optional Google Gemini API integration when cloud acceleration is desired. Transparent privacy disclosures prevent silent cloud fallbacks.
- 🛡️ **Ironclad Deterministic Safety:**
  - **Zero Auto-Deletion:** SlothSort has no deletion primitives. It only moves or renames.
  - **Zero Silent Overwrites:** Destination collisions are caught before any changes are applied.
  - **Path Traversal Immune:** Operations are strictly jailed within your selected target directory.
  - **Symlink Protection:** Symlink sources and roots are skipped and never followed.
- ↩️ **1-Click Instant Undo:** Regret an organization plan? Undo it with one click.
- 🌿 **Calm & Polished Experience:** Designed with a soothing forest-green palette, responsive desktop layout, and zero gimmicks.

---

## 🏗️ Architecture at a Glance

SlothSort operates on a strict **advisory AI, deterministic engine** model:

```
+-------------------------------------------------------------+
|                        Web Frontend                         |
|             (React 19 + TypeScript + Vite)                  |
+------------------------------+------------------------------+
                               | REST (localhost:8000)
+------------------------------v------------------------------+
|                    FastAPI Backend Server                   |
|                   (Python 3.14 + Pydantic)                  |
+-------------------+--------------------+--------------------+
                    |                    |
         +----------v----------+  +------v--------------------+
         |   Deterministic     |  |       AI Subsystem        |
         |   Core Engine       |  |   (Pluggable Interface)   |
         | - Folder Scanner    |  |                           |
         | - Path Containment  |  | 🟢 Ollama (gemma3:1b)     |
         | - Collision Matrix  |  | ☁️ Google Gemini (Opt-in) |
         | - Atomic Executor   |  | 🧪 Mock Provider (CI)     |
         | - Undo Manifest     |  +---------------------------+
         +----------+----------+
                    |
+-------------------v-----------------------------------------+
|                  Your Local File System                     |
|           (Directory Restructuring & Manifest Log)          |
+-------------------------------------------------------------+
```

---

## 🚀 Quickstart Guide

### Prerequisites

- **OS:** Linux (Ubuntu 22.04+ recommended), macOS, or Windows (WSL2)
- **Python:** 3.10+ (tested on Python 3.14)
- **Node.js:** 18+ (tested on Node 24)
- **Ollama:** Installed and running locally
  ```bash
  # In a separate terminal, pull and start Gemma 3 1B:
  ollama pull gemma3:1b
  ollama serve
  ```
  *(Note: If you don't have Ollama installed, you can use the built-in **Mock Provider** to test the entire application without any dependencies).*

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy example environment configuration
cp ../.env.example .env

# Run FastAPI backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at `http://127.0.0.1:8000` with interactive OpenAPI docs at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

### 3. Try the Safe Demo Seeder

SlothSort includes a safe CLI utility that populates a disposable directory with 12 harmless sample files (invoices, code, media stubs, archives) to test the app without touching personal files:

```bash
# Preview files without writing to disk:
python -m backend.app.cli.seed_demo --dry-run /tmp/slothsort_demo

# Seed harmless demo files:
python -m backend.app.cli.seed_demo /tmp/slothsort_demo
```

Now enter `/tmp/slothsort_demo` into the SlothSort web UI and click **Scan Folder**!

---

## 🧪 Running the Automated Test Suites

SlothSort features an extensive test suite verifying path safety, anti-replay persistence, and UI components:

```bash
# Run backend pytest suite (86 automated tests)
cd backend
pytest -v

# Run frontend test suite (11 Vitest tests)
cd ../frontend
npm test -- --run

# Verify production frontend build
npm run build
```

---

## 🧭 Core Workflow

1. **Select Folder:** Enter the path to any cluttered directory (e.g. `/tmp/slothsort_demo` or `~/Downloads`).
2. **Scan & Inspect:** Review discovered files, formats, and total disk space.
3. **Choose Provider:** Select **Local Ollama (`gemma3:1b`)** for complete offline privacy, or **Hosted Gemini** if configured.
4. **Generate Plan:** SlothSort batches metadata and suggests intuitive subfolders (`Finance/`, `Notes/`, `Development/`, `Images/`, `Archives/`) and clean file names.
5. **Review & Edit:** Check proposed changes, resolve any collision alerts, or tweak suggested names.
6. **Apply Changes:** Deterministic engine safely creates folders and atomically moves approved files.
7. **Instant Undo:** Click **"Undo Last Batch"** anytime to restore files to their exact previous state.

---

## 📚 Project Documentation

- [**Reproducible Demo Guide**](docs/DEMO.md): Step-by-step walkthrough from clean install to execution and undo.
- [**Security & Privacy Model**](docs/SECURITY.md): Threat mitigation, metadata-only policy, collision protection, and undo boundaries.
- [**System Architecture**](docs/ARCHITECTURE.md): Component diagrams, data contracts, and Pydantic schemas.
- [**Safety Model & Invariants**](docs/SAFETY_MODEL.md): The 10 safety invariants, path containment, and collision detection rules.
- [**AI Provider Strategy**](docs/AI_PROVIDER_STRATEGY.md): Dual-provider design, prompt engineering for small models, and privacy disclosures.
- [**Implementation Roadmap**](docs/IMPLEMENTATION_PLAN.md): Phased delivery roadmap and verification milestones.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome! Please read our [**Contributing Guide**](CONTRIBUTING.md) to get started.

---

## 📄 License

SlothSort is licensed under the [Apache 2.0 Open Source License](LICENSE).
