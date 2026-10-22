# Contributing to SlothSort 🦥

Thank you for your interest in contributing to **SlothSort**! Built for the **Hacktoberfest 2026 Week 3 Open-Source AI Challenge: "Slow and Steady"**, SlothSort welcomes community contributions that uphold our core values: **local-first AI, deterministic filesystem safety, and respectful user privacy**.

---

## 📜 Code of Conduct

We are committed to providing a friendly, welcoming, and inclusive environment for all contributors, regardless of background or experience level. Please treat everyone with empathy and respect.

---

## 🛡️ The Non-Negotiable Safety Invariants

Before writing code for SlothSort, please review [`docs/SECURITY.md`](docs/SECURITY.md) and [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md). **Every Pull Request that interacts with file paths or disk operations must uphold these invariants**:

1. **Advisory AI Only:** Generative AI models must NEVER have filesystem write, move, or shell privileges. AI only suggests relative paths; deterministic Python code verifies and moves.
2. **Metadata Only:** Never read file contents or calculate content hashes. Only filename, extension, file size, and modification time may be inspected.
3. **Strict Path Containment:** Every operation must be strictly jailed within the user-approved root directory. Path traversal (`..`) and symlink escapes must be rejected.
4. **Zero Silent Overwrites:** Destination collisions and existing files must be detected pre-flight. Never overwrite an existing file.
5. **No File Deletions:** SlothSort has no deletion primitives. It only creates directories and moves files.
6. **Zero Silent Cloud Fallback:** Never automatically fall back to cloud providers (e.g. Gemini) when local models (Ollama) fail.
7. **Reversible Execution:** Every executed batch must produce an undo manifest allowing 1-click atomic rollback.

---

## 🛠️ Development Setup

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/slothsort.git
cd slothsort
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

Run backend tests:
```bash
pytest -v
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm test -- --run
npm run build
```

---

## 🧪 Testing Guidelines

- Any new engine feature or safety rule must include automated pytest tests in `backend/tests/`.
- Any frontend component change should include Vitest tests in `frontend/src/tests/`.
- You can test safe folder operations using the demo seeding tool:
  ```bash
  python -m backend.app.cli.seed_demo /tmp/slothsort_test
  ```

---

## 🔀 Submitting a Pull Request

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-improvement
   ```
2. Keep your changes focused. Small, single-purpose PRs are reviewed and merged much faster.
3. Verify that all tests pass:
   ```bash
   # In backend
   pytest
   # In frontend
   npm test -- --run && npm run build
   ```
4. Write clear commit messages.
5. Open a Pull Request referencing any relevant Hacktoberfest issues.

Happy hacking! 🌿🦥
