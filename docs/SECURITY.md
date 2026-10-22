# SlothSort Security & Privacy Model

> **Tagline:** *"Let your laptop clean up after you."*
> **Philosophy:** Advisory AI, Deterministic Engine, Human Control, Zero Leaks.

SlothSort is designed from the ground up to operate safely in sensitive local user environments (such as user `Downloads`, `Documents`, and project workspaces). This document details SlothSort's security boundaries, threat mitigation strategies, privacy model, and operational limitations.

---

## 1. Threat Model & Architectural Security

SlothSort fundamentally rejects the pattern of giving generative AI models autonomous write or shell access to a user's filesystem.

```text
+-------------------------------------------------------------+
|                     Generative AI Layer                     |
|            (Ollama / Gemma 3 1B or Hosted Gemini)           |
+------------------------------+------------------------------+
                               | Read-Only Metadata (Input)
                               | Proposed Rel Paths (Output)
                               v
+-------------------------------------------------------------+
|                Deterministic Safety Subsystem               |
|      (Path Containment, Collision Checks, Permissions)      |
+------------------------------+------------------------------+
                               | Verified, Non-Conflicting Plan
                               v
+-------------------------------------------------------------+
|                    Human-in-the-Loop Gate                   |
|               (Mandatory Selective Approval)                |
+------------------------------+------------------------------+
                               | Explicitly Approved Op IDs
                               v
+-------------------------------------------------------------+
|                   Atomic Execution & Undo                   |
|          (Single File Moves + Manifest Transaction)         |
+-------------------------------------------------------------+
```

### The Advisory AI Principle
1. The AI model has **no execution capabilities**. It cannot create directories, delete files, move files, or run system commands.
2. The model receives **only metadata** (file names, extensions, file sizes, and timestamps).
3. The model outputs structured JSON containing proposed categories and renamed filenames.
4. All model outputs are treated as **untrusted, hostile user input** and subjected to strict deterministic validation before entering the execution queue.

---

## 2. Folder Access Boundaries & Containment

SlothSort strictly regulates which directories may be scanned or modified through [`backend/app/security.py`](../backend/app/security.py):

### 2.1 Authorized Root Whitelist
- The backend evaluates every targeted directory against `SLOTHSORT_ALLOWED_ROOTS` (defaults to the user's home directory and `/tmp`).
- Attempts to scan or organize directories outside configured roots result in immediate `403 Forbidden` responses.

### 2.2 System-Critical Path Protection
The following paths (and all subpaths within them) are hard-blocked from ever being targeted or traversed:
- `/`, `/bin`, `/sbin`, `/usr`, `/usr/bin`, `/usr/sbin`
- `/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`
- `/run`, `/var/run`, `/var/log`

### 2.3 User Credential Directory Protection
To protect user keys and credentials, folders matching sensitive authentication names are rejected:
- `.ssh`, `.gnupg`, `.aws`, `.azure`, `.kube`, `.docker`

### 2.4 Internal Storage Isolation
SlothSort prevents users or AI suggestions from targeting its own manifest storage directory (`~/.config/slothsort/manifests`).

### 2.5 Path Traversal & Normalization
- All raw paths are sanitized: traversal tokens (`..`), redundant slashes (`//`), and null bytes are rejected pre-flight.
- Paths are canonicalized using strict resolution (`Path.resolve()`).
- The canonical path of every planned target must satisfy `target_path.is_relative_to(root_path)`. Any attempt to escape the root directory is flagged as a critical collision/security conflict.

### 2.6 Symbolic Link Defenses
- Target root directories cannot be symbolic links.
- Files encountered during scanning that are symbolic links (`is_symlink() == True`) are recorded as skipped files and are **never moved, renamed, or followed**. This mitigates symlink race conditions, circular link exhaustion, and symlink-based directory escapes.

---

## 3. Metadata-Only Processing & Zero Content Snooping

SlothSort strictly protects user file contents:

| Data Attribute | Collected & Processed? | Sent to Local Ollama? | Sent to Hosted Gemini? |
| :--- | :---: | :---: | :---: |
| **Filename** (e.g. `invoice_march.pdf`) | ✅ Yes | ✅ Yes | ✅ Yes (if opt-in) |
| **Extension** (e.g. `pdf`) | ✅ Yes | ✅ Yes | ✅ Yes (if opt-in) |
| **File Size in Bytes** | ✅ Yes | ✅ Yes | ✅ Yes (if opt-in) |
| **Modification Timestamp** | ✅ Yes | ✅ Yes | ✅ Yes (if opt-in) |
| **File Content / Text / Bytes** | ❌ **NEVER** | ❌ **NEVER** | ❌ **NEVER** |
| **File Hashes of Contents** | ❌ **NEVER** | ❌ **NEVER** | ❌ **NEVER** |
| **MIME / Content Sniffing** | ❌ **NEVER** | ❌ **NEVER** | ❌ **NEVER** |

SlothSort never calls `open(file, 'rb')` or `read()`. Files remain completely unread. Only filesystem directory entries (`os.scandir`) are inspected.

---

## 4. Mandatory Human Approval & Plan Previews

SlothSort enforces a strict two-phase commit pattern:
1. **Preview Only (`POST /api/plan/generate`):**
   - Discovers files and computes proposed target destinations.
   - Computes diffs and collision statuses.
   - **Zero filesystem mutations occur.** No folders are created, and no files are moved.
2. **Interactive User Inspection:**
   - The user reviews the proposed changes in the web UI.
   - Users can rename proposed categories, edit proposed filenames, or uncheck individual files.
3. **Explicit Execution (`POST /api/plan/execute`):**
   - The frontend transmits a list of `approved_op_ids`.
   - The backend matches IDs against the validated plan and **only processes files explicitly approved**.
   - Unapproved files remain untouched in their exact original locations.

---

## 5. Collision Protection & Atomic Moves

SlothSort guarantees that **no file is ever silently overwritten or destroyed**:

### 5.1 Intra-Batch Destination Collisions
If two distinct files (e.g. `notes.txt` and `old/notes.txt`) are both mapped by the AI to the same destination (`Notes/notes.txt`), the validator flags both operations with `COLLISION_INTRA_BATCH` before execution. The plan cannot be executed until the user resolves the destination name collision.

### 5.2 Filesystem Existing-File Collisions
If a proposed destination file already exists on disk, the validator marks the operation with `COLLISION_EXISTING_FILE`. Execution will refuse to overwrite the existing file.

### 5.3 Time-of-Check to Time-of-Use (TOCTOU) Defenses
Immediately prior to invoking `os.replace` or `shutil.move`, the execution engine re-checks `target.exists()`. If a new file appeared at the target location between plan generation and execution, the operation is aborted and marked as failed.

### 5.4 No Deletion Primitives
SlothSort contains **no code that deletes user files**. The only disk operations supported are directory creation (`os.makedirs`) and atomic file moves (`os.replace` / `shutil.move`).

---

## 6. Manifest Integrity, Undo & Known Limitations

### 6.1 Transaction Manifests
Every executed batch creates a structured JSON manifest in `~/.config/slothsort/manifests/`. Manifests log:
- Plan ID and Manifest ID (e.g. `man_YYYYMMDD_HHMMSS_<hex>`)
- Canonical root path
- Timestamp of execution
- Ordered list of executed steps with original absolute paths and destination absolute paths

> [!NOTE]
> Manifests are ordinary, formatted JSON files (not cryptographically signed with asymmetric keys). Integrity is enforced via Pydantic model validation on load and strict runtime path containment checks (`assert_path_contained`) before executing any rollback operations.

### 6.2 Undo Security & Containment
During an undo rollback (`POST /api/undo`):
- The manifest is loaded from the protected manifest directory.
- `UndoEngine` validates that all source paths, target paths, and created directory paths in the manifest resolve strictly within `manifest.root_path` (`assert_path_contained`). Forged or tampered manifests attempting out-of-root writes are blocked.
- Moves are reversed in reverse order.
- Empty directories created by SlothSort during the forward batch are cleaned up; non-empty directories are left untouched.

### 6.3 Anti-Replay Protection
Executed plan IDs are registered in both an in-memory registry and disk-persisted manifest store. Re-submitting an already executed `plan_id` returns `409 Conflict`, even across full server restarts.

### 6.4 Undo Limitations & Edge Cases
- **External Modification:** If a user or background process modifies or deletes a file after SlothSort moved it, an undo request will safely halt without overwriting existing data.
- **Cross-Mount Moves:** On POSIX systems, moving a file across different filesystem mount points (e.g., from `/mnt/storage` to `/home`) cannot be performed atomically via `os.rename`. SlothSort uses Python's `shutil.move`, which falls back to copy-and-unlink across filesystem boundaries. For maximum atomicity and speed, organize folders located on the same disk partition.
- **Localhost Scope:** SlothSort is architected as a local desktop tool. The FastAPI server binds to `127.0.0.1` by default and does not implement multi-user session authentication. It should never be exposed directly to the public internet without an authenticating reverse proxy.

---

## 7. AI Provider Privacy & Cloud Disclosures

SlothSort offers two interchangeable AI operating modes:

### Mode A: Local Ollama (Default & Recommended)
- **Model:** `gemma3:1b` (or other open-weight Ollama model).
- **Network Traffic:** 100% localhost (`http://127.0.0.1:11434`).
- **Privacy:** Zero data leaves your computer. Fully operational offline (airplane mode).
- **Cost:** Free, open-source.

### Mode B: Hosted Google Gemini (Optional Cloud Opt-in)
- **Model:** `gemini-2.5-flash` (or user-configured model).
- **Data Transmitted:** File names, relative paths, file sizes, and timestamps.
- **Data NOT Transmitted:** File contents, text, code, or binary data.
- **Key Storage:** Stored exclusively in the backend environment (`GEMINI_API_KEY`). Never transmitted to the browser, logged, or returned in API responses.
- **Zero Silent Fallback:** SlothSort **never silently switches** from Local mode to Cloud mode. If Ollama is offline or encounters an error, SlothSort reports the error directly and halts. Cloud mode requires explicit, voluntary user selection.

---

## 8. Reporting Security Vulnerabilities

If you discover a security vulnerability or containment escape in SlothSort, please do not open a public issue. Instead, report it responsibly to the project maintainers via email or private repository advisory.
