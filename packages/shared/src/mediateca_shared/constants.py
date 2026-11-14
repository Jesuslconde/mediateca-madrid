from __future__ import annotations

JOB_TYPES = ("discover", "enrich", "index")
JOB_STATUSES = ("pending", "running", "completed", "failed", "cancelled")
FINAL_STATUSES = ("completed", "failed", "cancelled")
DEFAULT_BATCH_SIZE = 5000
DEFAULT_MAX_ATTEMPTS = 3
