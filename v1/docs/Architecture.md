# ByteRelay — Architecture & Plan

## 1. What this project is

A tool that moves files from **Telegram** to **Nextcloud**, built like a real transfer engine — not just a simple upload script.

The goal is not to build the fastest way to move files. The goal is to build the pipeline the *right way*, using patterns that real backend systems use: a state machine, streaming, retries, and a pluggable adapter design.

## 2. Why this project

Many tools already move files between clouds (rclone, MultCloud, Air Explorer, etc.). This project is not trying to beat them or replace them. The value here is:

- Practicing real backend engineering patterns (state management, queues, streaming, retries, integrity checks, concurrency, observability).
- Building a portfolio project that shows system design thinking, not just "I called an API."
- Solving one narrow, real use case well: **files people already store inside Telegram channels, moved into their own storage.**

## 3. Scope

**In scope (v1):**
- One source: Telegram
- One destination: Nextcloud — but **user-configurable per user**, not a fixed instance. Each user supplies their own server URL, username, and password on first use.
- A working pipeline: Telegram file → downloaded → uploaded to that user's Nextcloud → confirmed complete

**Out of scope (v1, but designed for later):**
- Other sources (Google Drive, Dropbox, S3, etc.)
- Other destinations (only Nextcloud, just multi-instance of it)
- Custom folder selection within Nextcloud (v1 always uses root)
- App-password-based auth (v1 stores the user's real password, encrypted — see security notes)
- Web UI
- Access control / allow-list (bot is open to any Telegram user in v1)

The scope is intentionally small. The design (not the amount of code) is what should look "big."

## 4. The core idea: Adapter Pattern

Even though v1 only supports Telegram → Nextcloud, the code is written so that:

- Telegram is just one implementation of a generic **Source**
- Nextcloud is just one implementation of a generic **Destination**

This means adding a new source or destination later would mean writing a new adapter class, not rewriting the pipeline.

```
Source (interface)          Destination (interface)
  get_metadata()               upload_chunk()
  stream()                     finish()

TelegramSource               NextcloudDestination
(implements Source)          (implements Destination)
```

## 5. The full engineering vision (long-term, not all built in v1)

This is the complete list of engineering problems this kind of system needs to solve. Not everything is built right away — see IMPLEMENTATION_STATUS.md for what's actually done.

1. **State Machine** — every file transfer has a life cycle (queued, downloading, uploading, done, failed, etc.), and the system should always know exactly what state a file is in.
2. **Queue Scheduling** — deciding what gets processed next, and making sure one user can't hog all the resources.
3. **Streaming Pipeline** — moving files in small chunks instead of loading the whole file into memory.
4. **Retry & Failure Recovery** — if a transfer fails partway, decide whether to retry, resume, or roll back.
5. **Data Integrity** — checking that the uploaded file is actually correct (size check, checksum, etc.).
6. **Storage Management** — checking there's enough space at the destination before uploading.
7. **Multi-Tenant Support** — handling many users safely (limits, isolation, abuse prevention).
8. **Adapter Architecture** — the Source/Destination pattern described above.
9. **Observability** — logs, metrics, and history so failures can actually be understood and debugged.

## 6. High-level flow (v1)

```
User forwards a file to the Telegram bot
        ↓
Bot checks: does this user have saved Nextcloud credentials?
        ↓ (no)                              ↓ (yes)
  Bot asks for server URL,                  ↓
  username, password                        ↓
        ↓                                   ↓
  Saved encrypted, keyed to user_id ---------┘
        ↓
Bot shows file info + Confirm/Cancel button
        ↓ (confirm)
System creates a "Transfer" record (state: QUEUED)
        ↓
Worker picks it up (state: DOWNLOADING)
        ↓
File streamed in chunks from Telegram
        ↓
Chunks streamed to that user's Nextcloud (state: UPLOADING)
        ↓
Basic check that the file arrived correctly
        ↓
State: COMPLETED (or FAILED, with reason logged — e.g. bad saved credentials, no space)
```

## 7. Project structure

```
telegram2nextcloud/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_STATUS.md
│   ├── DATA_MODEL.md
│   └── TECH_STACK.md
├── .env.example
├── .gitignore
├── requirements.txt
│
├── bot.py                       # Telethon entrypoint — handlers only, no business logic
│
├── core/
│   ├── models.py                  # Transfer, TransferHistory, ChunkRecord, NextcloudCredential
│   ├── enums.py                    # TransferState
│   ├── state_machine.py             # legal transitions + persistence
│   ├── pipeline.py                   # producer/consumer streaming orchestration
│   ├── retry.py                       # retry-with-backoff, fresh unique-id per attempt
│   ├── credentials.py                  # encrypt/decrypt user Nextcloud credentials
│   ├── db.py                            # DB engine/session setup
│   └── logging_setup.py                  # structured logging config
│
├── adapters/
│   ├── base.py                    # Source / Destination interfaces
│   ├── telegram_source.py
│   ├── nextcloud_destination.py     # now takes per-user credentials, not fixed .env values
│   └── fake_adapters.py              # for tests
│
├── tests/
│   ├── test_state_machine.py
│   └── test_pipeline_with_fakes.py
│
└── data/                          # SQLite file (gitignored)
```

## 8. Guiding principle

Keep the entrypoint (the bot) "dumb." All the real logic (state changes, streaming, retries) lives in `core/`. This keeps the code testable and easy to explain — the interface layer just triggers the pipeline, it doesn't contain the pipeline's logic.