# ByteRelay (v1)

Moves files from Telegram to Nextcloud. See `docs/` for architecture, data model, tech stack, and requirements.

## Setup

```bash
cd v1
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

## Database

Apply migrations (creates `data/transfers.db`):
```bash
source .venv/bin/activate
alembic upgrade head
```

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
source .venv/bin/activate
python -m pytest tests/ -v
```

Run a single test file:
```bash
python -m pytest tests/test_state_machine.py -v
```