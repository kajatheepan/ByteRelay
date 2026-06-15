# Tech Stack — Telegram2NextCloud (v1)

## Decisions

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.12+ | Strong async support (asyncio) fits the streaming pipeline; mature Telegram and WebDAV library ecosystem |
| Telegram library | Telethon | Pyrogram is archived/dead (Dec 2024). Telethon is independently maintained (not a fork), mature, supports large files (2GB+) via MTProto — no Bot API's 20MB cap |
| Database | SQLite | Zero setup, free, sufficient for a single-process bot; relational shape fits the state machine naturally (unlike a NoSQL store) |
| HTTP client (Nextcloud) | httpx (async) | Matches the async pipeline; handles the MKCOL/PUT/MOVE chunked upload flow. Now used per-user, targeting each user's own saved server URL, not one fixed instance |
| Credential encryption | cryptography (Fernet) | Encrypts each user's saved Nextcloud password at rest; key kept in `.env`, separate from the encrypted data — needed now that credentials are collected per-user in v1, not read from a single fixed `.env` value |
| Hosting | Oracle Cloud Always Free (Compute VM) | Genuinely free, 10TB/month outbound bandwidth (far beyond v1's realistic needs), always-on VM fits a long-running bot process — unlike serverless platforms (Firebase Functions, etc.) which aren't built for long-lived streaming connections |
| Config | python-dotenv (.env file) | Keeps the bot's own secrets (bot token, API ID/hash, encryption key) out of code/git — user Nextcloud credentials live encrypted in the database instead, not in `.env` |
| Testing | pytest | Standard, simple, async-test support via pytest-asyncio |

## Rejected options (and why)

- **Pyrogram** — archived, no longer maintained. Confirmed via GitHub (archived Dec 23, 2024).
- **Pyrofork** (Pyrogram fork) — alive but a small community fork; riskier long-term than Telethon's independent, longer track record.
- **Firebase (Functions + Firestore)** — mismatched to this system: Functions aren't designed for long-running streaming processes (they're built for short request/response), and Firestore is NoSQL, which doesn't fit the relational state-machine data model well.
- **Managed Postgres (e.g. via Supabase)** — unnecessary for v1's single-process scale; SQLite is simpler and free. Worth reconsidering only if the system grows to multiple app instances needing shared DB access.