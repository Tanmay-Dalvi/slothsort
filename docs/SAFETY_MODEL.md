# SlothSort Safety Model & Security Invariants

> **Core Axiom:** *AI provides non-binding suggestions. Deterministic application code validates and executes. The user retains ultimate authority. Every operation is transparent and reversible.*

---

## 1. The Ten Inviolable Safety Invariants

Every release of SlothSort must satisfy the following 10 invariants, enforced by automated unit tests and runtime assertions:

### Invariant 1: Zero Autonomous File Deletion
- SlothSort contains **zero deletion primitives** (`os.remove`, `os.unlink`, `shutil.rmtree`).
- The file operation engine only supports `MOVE` and `RENAME`.
- If a user wishes to remove a file, they must do so using their operating system file manager. SlothSort will never delete or trash files.

### Invariant 2: Zero Silent Overwrites
- Before any file move or rename is initiated, the engine checks whether a file already exists at the canonical target path.
- If a target already exists:
  - The plan flags the operation with a high-visibility `COLLISION_EXISTS` conflict in the UI.
  - The engine refuses execution until the user explicitly resolves the collision (e.g., auto-renaming suffix `_1`, manual name edit, or skipping).
  - A pre-flight filesystem check is re-executed atomically immediately prior to moving each file.

### Invariant 3: Absolute Path Containment & Traversal Immunity
- Operations are strictly jailed within the user-selected folder root.
- All source and destination paths are resolved to their canonical absolute forms using `pathlib.Path.resolve()`.
- The engine enforces:
  ```python
  def assert_path_contained(target_path: Path, root_path: Path):
      resolved_target = target_path.resolve()
      resolved_root = root_path.resolve()
      if not resolved_target.is_relative_to(resolved_root):
          raise PathTraversalError(f"Target path {resolved_target} escapes root {resolved_root}")
  ```
- Any model output attempting relative directory navigation (`../`, `../../`, leading slashes `/etc`, null bytes `\0`, Windows drive letters `C:`) is immediately rejected during schema validation.

### Invariant 4: Symlink Guardrails
- Symlinks pointing outside the target root folder are flagged as `EXTERNAL_SYMLINK` and skipped by default.
- SlothSort never follows directory symlinks during recursive scanning, preventing infinite loops and unintentional traversal into external system trees.
- If an approved move targets an internal symlink, the link itself is moved, never the referenced target.

### Invariant 5: Strict Metadata-Only Privacy by Default
- The AI provider prompt receives only:
  1. File relative name (e.g., `invoice_october.pdf`)
  2. File extension (`pdf`)
  3. Size in bytes (`204850`)
  4. Modified timestamp (`2026-10-15T09:30:00Z`)
- **Zero file contents** (text, binary, EXIF images, documents) are read or transmitted to either local Ollama or hosted Gemini.
- If a future advanced feature (e.g., deep document summarization) requires inspecting file content, it must be an explicit, per-file user opt-in with unmistakable disclosure.

### Invariant 6: Pre-Execution Plan & Collision Matrix
- An operation plan is generated and presented in full before any disk changes occur.
- The validator builds an intra-batch destination collision matrix:
  - If File A and File B are both proposed to move to `Finance/Summary.pdf`, both are flagged as `INTERNAL_COLLISION`.
  - Execution of collided operations is blocked until unique paths are assigned.

### Invariant 7: Atomic Execution & Failure Isolation
- Moving files on the same filesystem is an atomic operation (`os.replace` after collision check, or safe staged rename).
- Operations are executed sequentially. If an individual file move encounters an error (e.g., permission denied, disk full, locked file):
  1. The error is captured in the execution result.
  2. The original file remains untouched at its source path.
  3. The batch halts safely or isolates the failure, reporting exact state to the user.

### Invariant 8: Transaction Manifest & 1-Click Rollback
- Every executed batch writes an immutable JSON manifest to `~/.config/slothsort/manifests/<manifest_id>.json`.
- The manifest records:
  - Source path $\to$ Destination path
  - File size and modification timestamp
  - Execution timestamp
- The Undo engine reads the manifest in reverse chronological order:
  - Verifies that moved files still reside at their destinations.
  - Moves each file back to its exact original location.
  - Cleans up empty directories created by the organization plan.
  - Marks the manifest as `ROLLED_BACK`.

### Invariant 9: Path and Filename Sanitization
- AI-generated category folder names and suggested filenames are sanitized against OS filesystem constraints:
  - Disallowed characters stripped or replaced: `< > : " / \ | ? *`
  - Control characters (ASCII 0-31) stripped.
  - Trailing periods and spaces stripped (Windows/FAT compatibility).
  - Length capped at 255 bytes per component.
  - Reserved OS filenames blocked (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).

### Invariant 10: Graceful Degradation & Network Isolation
- If Ollama is offline or uninstalled:
  - Clear user diagnosis with actionable instructions (`ollama serve` / `ollama run gemma3:1b`).
  - No application crash.
- If Gemini API fails, is rate-limited, or has an invalid key:
  - User is shown the specific provider error without leaking API credentials in logs.
  - Never automatically or silently fall back to cloud if local was chosen.
  - Never silently use cloud credentials without explicit confirmation.

---

## 2. Collision Detection Matrix

| Collision Type | Scenario | Detection Method | UI Indicator | Engine Action |
|---|---|---|---|---|
| **Intra-Batch Collision** | Model maps `doc1.txt` and `doc2.txt` to `Notes/summary.txt` | Target path grouping in validator | ⚠️ Red badge: "Duplicate destination" | Blocks batch execution until user renames or skips |
| **Filesystem Collision** | Model maps `doc1.txt` to `Notes/readme.txt`, which already exists on disk | `os.path.exists(target_path)` | ⚠️ Amber badge: "File already exists" | Suggests `readme (1).txt` or skip |
| **Self-Mapping** | Model maps `file.txt` to `file.txt` | `source == target` | ℹ️ Neutral: "No change" | Marked as `KEEP`, no disk I/O |
| **Case Collision** | `File.txt` $\to$ `file.txt` on case-insensitive filesystems | Case fold comparison | ⚠️ Warning: "Case conflict on current filesystem" | Safe temporary two-step rename |

---

## 3. Undo Manifest Structure

```json
{
  "manifest_id": "man_20261022_140500_8f9a",
  "root_path": "/home/user/Downloads",
  "executed_at": "2026-10-22T14:05:00.123456Z",
  "provider": "ollama:gemma3:1b",
  "steps": [
    {
      "step_id": 1,
      "source_abs_path": "/home/user/Downloads/october_bill.pdf",
      "target_abs_path": "/home/user/Downloads/Finance/Receipts/2026-10_october_bill.pdf",
      "file_size": 142050,
      "mtime": 1729584000.0,
      "created_directories": [
        "/home/user/Downloads/Finance",
        "/home/user/Downloads/Finance/Receipts"
      ]
    }
  ],
  "status": "APPLIED"
}
```

### Undo Rollback Procedure:
1. Verify target file exists and size matches `file_size`.
2. Move target file back to `source_abs_path`.
3. If `created_directories` are now empty, remove them in bottom-up leaf order.
4. Update manifest status to `ROLLED_BACK`.
