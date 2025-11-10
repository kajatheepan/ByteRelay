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

All planning and design docs live in [`v1/docs/`](./v1/docs/):

| Doc | What's in it |
|---|---|
| [Architecture.md](./v1/docs/Architecture.md) | System design, adapter pattern, module structure, full long-term engineering vision |
| [Requirements.md](./v1/docs/Requirements.md) | Functional and non-functional requirements (performance, security, reliability, etc.) |
| [DataModel.md](./v1/docs/DataModel.md) | Full database schema — tables, fields, constraints, and the reasoning behind each |
| [TechStack.md](./v1/docs/TechStack.md) | Language, libraries, hosting choices, and what was rejected (and why) |

Start with **Architecture.md** for the big picture, then **Requirements.md** for what v1 actually commits to.

## Tech stack

Python 3.12+ · Telethon · SQLite (SQLAlchemy + Alembic) · httpx · Oracle Cloud (hosting) · Docker

Full reasoning in [TechStack.md](./v1/docs/TechStack.md).

## Getting started

```bash
git clone <repo-url>
cd byterelay
cp .env.example .env   # fill in your Telegram API credentials and encryption key
pip install -r requirements.txt
python bot.py
```

Or via Docker:

```bash
docker compose up -d
```

## Project structure

```
byterelay/
├── docs/v0/            # earlier planning notes (superseded)
├── v1/
│   └── docs/            # current architecture, requirements, data model, tech stack docs
├── core/                 # state machine, pipeline, retry logic, config, db
├── adapters/               # Source/Destination interfaces + Telegram/Nextcloud implementations
├── tests/                    # unit tests (state machine + pipeline with fake adapters)
├── bot.py                     # thin Telegram bot entrypoint
├── docker-compose.yml
└── .env.example
```