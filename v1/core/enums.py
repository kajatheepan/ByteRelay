from enum import Enum


# Every transfer's status must be one of these values. Using an Enum
# instead of raw strings stops typos like "comleted" from slipping in.
class TransferState(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    UPLOADING = "uploading"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"