import logging, json
from core.config import settings


# Turns each log record into one JSON line instead of plain text, so logs
# can be grepped/filtered by field (e.g. transfer_id) instead of just read.
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Only include these if the log call passed them via extra={...} —
        # not every log line has a transfer_id/user_id/note.
        for key in ("transfer_id", "user_id", "note"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


# Call this once at app startup (in bot.py). Configures the root logger so
# every module's logging.getLogger(__name__) call inherits these settings.
def setup_logging():
    handler = logging.StreamHandler()  # writes to stdout; the process manager handles rotation
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.addHandler(handler)
