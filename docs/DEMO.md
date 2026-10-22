# SlothSort Reproducible End-to-End Demo Guide

> **Hacktoberfest 2026 Week 3 Challenge:** *"Slow and Steady"*
> **Tagline:** *"Let your laptop clean up after you."*

This guide walks you through a complete, reproducible demonstration of SlothSort from scratch. It uses the built-in safe demo seeding utility to create realistic, harmless files in a disposable directory, sorts them using local AI (`gemma3:1b`), and demonstrates 1-click instant undo.

---

## 📋 Prerequisites

Before starting, ensure you have:
1. **Python 3.10+** (tested up to Python 3.14).
2. **Node.js 18+** and **npm** (tested on Node 24).
3. **Ollama** installed and running locally with the `gemma3:1b` model:
   ```bash
   # In a separate terminal, pull and start Gemma 3 1B:
   ollama pull gemma3:1b
   ollama serve
   ```
   *(Note: If Ollama is not installed, you can still test the entire workflow using SlothSort's built-in **Mock Provider**).*

---

## 🚀 Step 1: Setup Backend & Frontend

### 1.1 Backend Setup
```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend test suite (86 automated tests)
pytest
```

### 1.2 Frontend Setup
```bash
cd ../frontend

# Install dependencies and verify build
npm install
npm test -- --run
npm run build
```

---

## 🦥 Step 2: Seed a Disposable Demo Directory

Use SlothSort's safe demo seed utility to create a realistic messy folder in `/tmp/slothsort_demo`.

```bash
# From the project root, activate the virtual environment:
source backend/.venv/bin/activate

# Optional: Test dry-run mode first (does not touch disk)
python -m backend.app.cli.seed_demo --dry-run /tmp/slothsort_demo

# Seed the actual harmless demo files:
python -m backend.app.cli.seed_demo /tmp/slothsort_demo

# (Optional) Seed with a pre-existing destination collision to test collision warnings:
python -m backend.app.cli.seed_demo --with-collision /tmp/slothsort_demo
```

You will see 12 realistic sample files created:
- **Documents:** `invoice_2026_q3_draft.pdf`, `q3_tax_receipt_office_supplies.pdf`, `meeting_notes_hacktoberfest_launch.txt`, `quarterly_priorities_draft.txt`
- **Development:** `backup_runner_nightly.py`, `styles_forest_palette.css`, `docker-compose.staging.yml`
- **Media:** `sunset_beach_trip_2026.jpg`, `screenshot_terminal_log_error.png`
- **Archives & System:** `client_assets_archive_2026.zip`, `raw_telemetry_dump_october.tar.gz`, `device_firmware_driver_v4.bin`

Inspect the folder in your terminal:
```bash
ls -la /tmp/slothsort_demo
```

---

## 🖥️ Step 3: Launch SlothSort

### Terminal 1: Start Backend Server
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs will be active at `http://127.0.0.1:8000/docs`.

### Terminal 2: Start Frontend Development Server
```bash
cd frontend
npm run dev
```
Open your browser at: **`http://localhost:5173`**

---

## 🧭 Step 4: Step-by-Step UI Walkthrough

### 1. Provider Status & Selection
- In the top header bar, observe the **Provider Selector**.
- If Ollama is running, it will show a green badge: `🟢 Local Ollama (gemma3:1b) - Ready`.
- Notice the privacy indicator: `🔒 100% Offline & Private — Zero data leaves your device`.

### 2. Scan the Folder
- In the **Target Folder** input box, paste:
  ```text
  /tmp/slothsort_demo
  ```
- Click **"Scan Folder"**.
- SlothSort scans the directory in under 20ms and displays the summary card:
  - **12 Files Discovered**
  - Breakdown by file extension (`.pdf`, `.txt`, `.py`, `.css`, `.yml`, `.jpg`, `.png`, `.zip`, `.gz`, `.bin`).
  - Total directory size.

### 3. Generate the AI Organization Plan
- With **Local Ollama** (or **Mock Provider**) selected, click **"Generate Plan"**.
- SlothSort batches file metadata into safe chunks and queries the model.
- Notice the calm loading state with the friendly Sloth icon.
- Within 1–3 seconds, the **Organization Plan Preview** appears:
  - Intelligently grouped categories: `Finance/`, `Notes/`, `Development/`, `Images/`, `Archives/`.
  - Cleaned, normalized file names.
  - Zero filesystem modifications have occurred yet!

### 4. Interactive Review & Customization
- **Edit a Destination:** Click on any suggested category or filename in the table (e.g. change `Finance` to `Accounting` or customize a filename).
- **Test Selective Approval:** Uncheck one file (e.g., `device_firmware_driver_v4.bin`).
  - The banner will update to reflect that only approved files will be moved.
- Notice the collision banner: All green with `0 Conflicts Detected`.

### 5. Execute the Plan
- Click **"Execute Approved Plan (11 Files)"**.
- SlothSort creates the necessary subfolders and atomically moves only the approved files.
- A success toast appears with the generated **Manifest ID**.

### 6. Verify Files on Disk
In your terminal, check the folder structure:
```bash
tree /tmp/slothsort_demo || ls -R /tmp/slothsort_demo
```
You will observe:
```text
/tmp/slothsort_demo/
├── Archives/
│   ├── client_assets_archive_2026.zip
│   └── raw_telemetry_dump_october.tar.gz
├── Development/
│   ├── backup_runner_nightly.py
│   ├── docker-compose.staging.yml
│   └── styles_forest_palette.css
├── Finance/
│   ├── invoice_2026_q3_draft.pdf
│   └── q3_tax_receipt_office_supplies.pdf
├── Images/
│   ├── screenshot_terminal_log_error.png
│   └── sunset_beach_trip_2026.jpg
├── Notes/
│   ├── meeting_notes_hacktoberfest_launch.txt
│   └── quarterly_priorities_draft.txt
└── device_firmware_driver_v4.bin  <-- (Left untouched in root as unapproved!)
```

### 7. Instant 1-Click Rollback (Undo)
- Back in the browser UI, click the **"Undo Last Batch"** button in the Execution Summary or History panel.
- The backend reads the transaction manifest, verifies path containment, and reverses all moves.
- Check `/tmp/slothsort_demo` in your terminal again:
```bash
ls -la /tmp/slothsort_demo
```
All 12 files are back in their original flat arrangement, and the temporary category subfolders have been cleanly pruned!

---

## 🧹 Step 5: Cleanup

When you have finished the demo, run the cleanup command printed by the seed utility:

```bash
rm -rf "/tmp/slothsort_demo"
```

---

## ❓ Troubleshooting

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **"Ollama unreachable"** | Ollama daemon not running | Run `ollama serve` in a terminal or switch provider to `Mock Provider` in the UI. |
| **"Model gemma3:1b not found"** | Gemma model not yet pulled | Run `ollama pull gemma3:1b`. |
| **"Folder outside authorized roots"** | Path is not in user home or `/tmp` | Specify paths within your `$HOME` or `/tmp`, or set `SLOTHSORT_ALLOWED_ROOTS` in `.env`. |
| **"Port 8000 already in use"** | Another process is on 8000 | Run `uvicorn app.main:app --port 8001` and set `VITE_BACKEND_URL=http://127.0.0.1:8001`. |
