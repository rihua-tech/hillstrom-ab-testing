# Development setup

Phase 1.0 uses CPython 3.12.10. Runtime, test, and lint dependencies are pinned
in `requirements.txt`.

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m pytest
```

## macOS or Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
```

These setup commands install tooling only. They do not download or inspect the
Hillstrom dataset. Read and follow `AGENTS.md` before any later data work.
