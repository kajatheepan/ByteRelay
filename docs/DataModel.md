# Data Model — ByteRelay v1

## Global conventions

- **All timestamps stored in UTC**, ISO 8601 text (e.g. `2026-08-30T14:32:10Z`). Convert to local time only when displaying to a user — never store local time.
- **No hard deletes on `Transfer`.** Failed/cancelled/completed transfers are kept permanently as history. `ON DELETE CASCADE` exists only as a safety net (e.g. future GDPR-style data deletion request), not something the app calls in normal operation.
- **`state` fields use a `CHECK` constraint**, restricting values to the enum below — invalid states are rejected at the database level, not just in application code.

## State enum

```python
class TransferState(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    UPLOADING = "uploading"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

No `PENDING_CONFIRMATION` state — the `Transfer` row is only created after the user taps Confirm. Before that, file info lives briefly in memory (Telegram's `callback_data`), never touching the database.

---

## Table: `Transfer` (built in v1)

Current state of each transfer — one row per transfer, always reflects the latest truth.

```sql
CREATE TABLE Transfer (
    id                  INTEGER PRIMARY KEY,
    user_id             INTEGER NOT NULL,
    telegram_file_id    TEXT NOT NULL,
    telegram_chat_id    INTEGER NOT NULL,
    telegram_message_id INTEGER,              -- message being edited for progress updates
    original_filename   TEXT NOT NULL,
    final_filename       TEXT,                 -- set once known (may differ if auto-renamed)
    file_size_bytes      INTEGER NOT NULL,
    total_chunks          INTEGER,             -- for accurate progress %, not just byte size
    state                  TEXT NOT NULL CHECK (state IN
                            ('queued','downloading','uploading','retrying',
                             'completed','failed','cancelled')),
    upload_session_id       TEXT,               -- fresh UUID per retry attempt, never reused
    retry_count               INTEGER NOT NULL DEFAULT 0,
    failure_reason              TEXT,
    created_at                    TEXT NOT NULL,  -- UTC ISO 8601
    updated_at                     TEXT NOT NULL   -- UTC ISO 8601, used for stuck-transfer detection
);

CREATE INDEX idx_transfer_state ON Transfer(state);
CREATE INDEX idx_transfer_user  ON Transfer(user_id);
```

**Fixes applied from review:**
- `telegram_chat_id` + `telegram_message_id` added — lets the bot find and continue editing the correct progress message even after a restart.
- `total_chunks` added — progress % can be based on actual chunk completion, not just a size estimate.
- `CHECK` constraint on `state`.
- Indexes on `state` (crash-recovery scan for stuck DOWNLOADING/UPLOADING/RETRYING transfers) and `user_id` (per-user isolation queries).

---

## Table: `TransferHistory` (built in v1)

Append-only audit trail — never overwritten, never hard-deleted in normal operation.

```sql
CREATE TABLE TransferHistory (
    id            INTEGER PRIMARY KEY,
    transfer_id   INTEGER NOT NULL REFERENCES Transfer(id) ON DELETE CASCADE,
    from_state    TEXT,      -- null for the first event of a transfer
    to_state      TEXT NOT NULL CHECK (to_state IN
                    ('queued','downloading','uploading','retrying',
                     'completed','failed','cancelled')),
    timestamp     TEXT NOT NULL,  -- UTC ISO 8601
    note          TEXT            -- e.g. "retry 2/3 due to network timeout"
);

CREATE INDEX idx_history_transfer ON TransferHistory(transfer_id);
```

---

## Table: `ChunkRecord` (built in v1 — schema only, resume logic not built)

Tracks per-chunk upload status, keyed to the specific upload attempt (not just the transfer), so retries don't collide.

```sql
CREATE TABLE ChunkRecord (
    id                 INTEGER PRIMARY KEY,
    transfer_id        INTEGER NOT NULL REFERENCES Transfer(id) ON DELETE CASCADE,
    upload_session_id  TEXT NOT NULL,   -- ties chunk to a specific attempt, not just the transfer
    chunk_number       INTEGER NOT NULL,
    chunk_size_bytes   INTEGER NOT NULL,
    status             TEXT NOT NULL CHECK (status IN ('pending','uploaded','failed')),
    uploaded_at        TEXT,            -- UTC ISO 8601, null if not yet uploaded

    UNIQUE (upload_session_id, chunk_number)
);

CREATE INDEX idx_chunk_transfer ON ChunkRecord(transfer_id);
```

**Fix applied from review:** `upload_session_id` added and made part of the uniqueness constraint (`upload_session_id, chunk_number`), not just `transfer_id`. Without this, two retry attempts of the same transfer would both write `chunk_number=1`, with no way to distinguish which attempt they belong to — silently breaking the future resume-from-offset feature this table exists to support.

---

## Table: `NextcloudCredential` (built in v1 — scope updated)

**Scope change:** originally designed-for-later, now built in v1. Each user supplies their own Nextcloud server URL + username + password on first use (triggered automatically the first time they forward a file with no saved credentials) — there is no fixed shared instance in v1.

```sql
CREATE TABLE NextcloudCredential (
    id                  INTEGER PRIMARY KEY,
    user_id             INTEGER NOT NULL,
    server_url          TEXT NOT NULL,
    username            TEXT NOT NULL,
    encrypted_password  TEXT NOT NULL,   -- user's real Nextcloud password, encrypted at rest (see note below)
    key_version         INTEGER NOT NULL DEFAULT 1,  -- supports future encryption key rotation
    created_at          TEXT NOT NULL,   -- UTC ISO 8601
    updated_at          TEXT NOT NULL,   -- UTC ISO 8601, set when user redoes setup after a bad-credential failure

    UNIQUE (user_id, server_url)
);

CREATE INDEX idx_credential_user ON NextcloudCredential(user_id);
```

**Security rules:**
- **v1 accepted risk:** stores the user's real Nextcloud password (not a revocable app password) — not all users can generate app passwords on their instance, so this is a documented trade-off, not an oversight. The bot tells users plainly what it stores before asking.
- **Encrypt, don't hash** — the bot needs the real value back to authenticate on the user's behalf. Use reversible symmetric encryption (e.g. Python `cryptography`'s Fernet).
- The encryption key lives outside the database (`.env` / secrets manager), never alongside the encrypted data.
- `key_version` lets old rows stay decryptable if the encryption key is ever rotated, instead of becoming permanently unreadable.
- **Designed for later:** optional app-password support as a safer alternative input method, with a bot-side guide showing users how to generate one.
- A 401/403 from Nextcloud during a transfer should be treated as a signal the saved credentials are likely wrong — surfaced to the user as "please redo setup," not a generic failure (see `Transfer.failure_reason`).

---

## Summary of all fixes applied in this finalization

| # | Fix | Table |
|---|---|---|
| 1 | `upload_session_id` added, composite uniqueness with `chunk_number` | `ChunkRecord` |
| 2 | `telegram_chat_id` / `telegram_message_id` added | `Transfer` |
| 3 | `CHECK` constraints on all `state` columns | `Transfer`, `TransferHistory`, `ChunkRecord` |
| 4 | Indexes on `state`, `user_id`, `transfer_id` (both child tables) | `Transfer`, `TransferHistory`, `ChunkRecord` |
| 5 | `ON DELETE CASCADE` as safety net + documented no-hard-delete rule | `TransferHistory`, `ChunkRecord` |
| 6 | UTC-only timestamp convention, stated globally | All tables |
| — | `UNIQUE (user_id, server_url)` to prevent duplicate credential rows | `NextcloudCredential` |
| — | `key_version` for future encryption key rotation | `NextcloudCredential` |
| — | `total_chunks` for accurate progress % | `Transfer` |
| — | **Scope change: moved from designed-for-later to built in v1** — each user now supplies their own Nextcloud server + credentials, no fixed shared instance | `NextcloudCredential` |