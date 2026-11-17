from __future__ import annotations

JOB_TYPES = ("discover", "enrich", "index", "tmdb", "branches")
JOB_STATUSES = ("pending", "running", "completed", "failed", "cancelled")
FINAL_STATUSES = ("completed", "failed", "cancelled")
DEFAULT_BATCH_SIZE = 5000
DEFAULT_MAX_ATTEMPTS = 3

JOB_CONFLICT_PAIRS = (
    ("discover", "enrich"),
    ("enrich", "tmdb"),
    ("enrich", "index"),
    ("tmdb", "index"),
)

MIN_WORKER_CONCURRENCY = 1
MAX_WORKER_CONCURRENCY = len(JOB_TYPES)

ENRICH_STATUSES = ("pending", "enriched", "failed")
TMDB_STATUSES = ("pending", "matched", "unmatched", "error", "skipped")
