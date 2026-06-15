# ByteRelay

**A Telegram → Nextcloud file transfer engine, built like a real backend system — not just an upload script.**

ByteRelay moves files people already have inside Telegram into their own Nextcloud storage, using a proper state machine, chunked streaming pipeline, retry logic, and a pluggable Source/Destination adapter design.

## What makes this different from a simple script

- **State machine** — every transfer has a tracked lifecycle (queued → downloading → uploading → completed/failed/cancelled), persisted to a database, never just "hope it works."
- **Chunked streaming pipeline** — files (2GB+) are streamed in fixed-size chunks end-to-end, never fully loaded into memory.
- **Adapter pattern** — Telegram and Nextcloud are just one implementation each of generic `Source`/`Destination` interfaces, so new sources or destinations can be added without rewriting the core pipeline.
- **Retry with clean failure handling** — retryable errors (network drops, server errors) are retried automatically with a fresh upload session each time; permanent errors (out of storage, bad credentials) fail immediately with a clear reason instead of wasting time.
- **Per-user Nextcloud accounts** — each Telegram user connects their own Nextcloud server, with credentials encrypted at rest.

## Project status

Actively being built. v1 scope is intentionally narrow (Telegram → Nextcloud only)

## Documentation

All planning and design docs live in [`docs/`](./docs/):

| Doc | What's in it |
|---|---|
| [Architecture.md](./docs/Architecture.md) | System design, adapter pattern, module structure, full long-term engineering vision |
| [Requirements.md](./docs/Requirements.md) | Functional and non-functional requirements (performance, security, reliability, etc.) |
| [DataModel.md](./docs/DataModel.md) | Full database schema — tables, fields, constraints, and the reasoning behind each |
| [TechStack.md](./docs/TechStack.md) | Language, libraries, hosting choices, and what was rejected (and why) |

Start with **Architecture.md** for the big picture, then **Requirements.md** for what v1 actually commits to.

Earlier planning notes (superseded) live in [`archive/v0/`](./archive/v0/).

## Tech stack

Python 3.12+ · Telethon · SQLite (SQLAlchemy + Alembic) · httpx · Oracle Cloud (hosting) · Docker

Full reasoning in [TechStack.md](./docs/TechStack.md).

## Getting started

```bash
git clone <repo-url>
cd byterelay
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN, ENCRYPTION_KEY
```

Generate `ENCRYPTION_KEY`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Apply database migrations (creates `data/transfers.db`):
```bash
alembic upgrade head
```

Run it:
```bash
python bot.py
```

Or via Docker:

```bash
docker compose up -d
docker compose logs -f
```

## Database

After changing `core/models.py`, generate a new migration — never hand-edit the schema:
```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Inspect the DB manually:
```bash
sqlite3 data/transfers.db ".tables"
sqlite3 data/transfers.db "SELECT * FROM transfer;"
```

## Running tests

```bash
python -m pytest tests/ -v
```

Run a single test file:
```bash
python -m pytest tests/test_state_machine.py -v
```

## Project structure

```
byterelay/
├── docs/                 # architecture, requirements, data model, tech stack docs
├── archive/v0/           # earlier prototype (superseded)
├── core/                 # state machine, pipeline, retry logic, config, db
├── adapters/             # Source/Destination interfaces + Telegram/Nextcloud implementations
├── tests/                # unit tests (state machine + pipeline with fake adapters)
├── bot.py                # thin Telegram bot entrypoint
├── bot_logic.py          # event handlers (file received, button tapped)
├── onboarding.py         # credential setup + confirm-button flow
├── dispatcher.py         # wires the pipeline to real adapters, enforces concurrency limit
├── recovery.py           # marks crash-interrupted transfers as failed on startup
├── telegram_client.py    # the single shared TelegramClient instance
├── docker-compose.yml
└── .env.example
```