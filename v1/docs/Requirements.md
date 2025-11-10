# Requirements — ByteRelay (v1)

## Functional Requirements

1. User forwards/sends a file to the Telegram bot (files up to 2GB+, via Telethon/MTProto — Bot API's ~20MB cap is insufficient).
2. **If the user has no saved Nextcloud credentials yet, the bot triggers a setup flow automatically on this first file forward** — asking for server URL, username, and password, before proceeding. Credentials are saved (encrypted) so this only happens once per user.
3. Once credentials exist (just saved, or already on file), the bot responds with file info (name, size) and a Confirm/Cancel button.
4. If user cancels or ignores → nothing is stored, no transfer record created.
5. If user confirms → a Transfer record is created and the upload process starts.
6. File is downloaded from Telegram in chunks (not fully loaded into memory).
7. File is uploaded to Nextcloud using the chunked upload API (MKCOL → PUT chunks → MOVE), using that user's own server URL and credentials, into the root folder. Custom folder selection is a future feature, not v1.
8. If a filename already exists at the destination, it is auto-renamed by appending a timestamp (e.g. `report_20260829_1432.pdf`) — never overwritten, never rejected.
9. Bot reports upload progress at fixed percentage milestones (10/25/50/75/100%), not on every chunk — avoids Telegram message-edit rate limits.
10. On a retryable failure (network timeout, connection drop, Nextcloud 5xx), the system retries automatically up to a limited number of attempts (e.g. 3), each retry using a fresh upload session (new unique-id). User sees "Retrying... (attempt 2/3)".
11. On a non-retryable failure (507 insufficient storage, 401/403 auth error, 400 bad request), the system fails immediately without wasting time on retries. A 401/403 likely means bad saved credentials — the user is told this specifically and can redo setup.
12. On any final failure (retries exhausted or non-retryable), the temporary upload folder on Nextcloud is cleaned up (abort), and the user is told the specific reason for failure — not a generic error.
13. If the bot restarts and a user taps a Confirm/Cancel button for a file the bot no longer recognizes (stale in-memory state), the bot tells the user the session expired and asks them to resend the file.
14. System keeps a record of every transfer's state history (for debugging, not necessarily shown to user).

## Non-Functional Requirements

Grouped by category. Each item says what v1 actually commits to — not just the ideal.

### Performance
- Memory usage stays flat regardless of file size — achieved by streaming in fixed-size chunks (e.g. 8MB), never loading a whole file into memory.
- A single large file (multi-GB) should not freeze the bot from responding to other messages (handled by running the transfer as a background async task, not blocking the main bot loop).

### Scalability (how many users / files it can handle)
- v1 target: a handful of users using it casually, not hundreds simultaneously.
- Multiple users are supported, but with no fairness — v1 processes transfers with a small fixed worker limit (e.g. 2-3 concurrent), first-come-first-served.
- Design must not block adding fair scheduling later (every Transfer record carries `user_id` from day one).

### Reliability
- A failed transfer must retry automatically a limited number of times (e.g. 3) before giving up.
- A transfer that fails permanently must leave no orphaned data on Nextcloud (cleanup/abort step).
- If the bot process crashes and restarts, transfers "stuck" mid-way should be detectable (state says DOWNLOADING/UPLOADING but nothing is actually running) — v1 can just mark these FAILED on startup rather than auto-resuming.

### Security
- Bot's own config (bot token, API ID/hash) stored outside code, in a `.env` file, never hardcoded or committed to git.
- **User-supplied Nextcloud credentials (server URL, username, password) are encrypted at rest** in the database — never stored in plain text. Encryption key lives outside the database (`.env`), never alongside the encrypted data.
- **Known accepted risk (v1):** users provide their real Nextcloud username/password (not a revocable app password), since not all users can generate app passwords on their Nextcloud instance. This is a conscious trade-off, not an oversight — the bot should tell users plainly what it stores. App-password support is a designed-for-later security upgrade.
- One user must never be able to access or trigger actions on another user's transfer or credentials (isolation is mandatory, not deferred).
- No secrets or credentials ever appear in logs.
- **Known accepted risk (v1):** the bot is open — any Telegram user who finds it can use it (no allow-list/access control). Each user now supplies their own Nextcloud destination, which somewhat reduces the earlier "shared account" risk, but an open bot is still worth flagging as a deliberate v1 scope decision.

### Maintainability / Extensibility
- Code structured so Source/Destination adapters could be swapped or added later without rewriting the core pipeline.
- Every state transition logged with a timestamp and transfer ID, so behavior can be traced after the fact.
- Config values (chunk size, retry count, etc.) are constants/env values, not magic numbers scattered in code.

### Observability (v1-level)
- Structured logs are the only observability tool in v1 (no metrics dashboard, no tracing system).
- Logs must be enough to answer "what happened to transfer X" after the fact, just by reading them.

### Testing
- Unit tests for the state machine (every legal/illegal transition).
- Unit tests for the pipeline logic using fake Source/Destination adapters (in-memory, no real network calls) — proves the pipeline and adapter interface are sound independent of real Telegram/Nextcloud behavior.
- Real adapters (TelegramSource, NextcloudDestination) are tested manually via the working demo, not automated in v1 (true integration tests are a designed-for-later item).

## Out of scope for v1 (explicitly)

- Multiple concurrent users being scheduled fairly
- Per-user quotas / abuse prevention
- Resume-from-byte-offset (only whole-transfer retry)
- Hash-based integrity check (size check only, or skipped if time-constrained)
- Any source/destination other than Telegram → Nextcloud
- Web UI or any interface other than the Telegram bot