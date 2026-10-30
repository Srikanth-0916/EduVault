"""Private upload storage and checksums.

Uploaded CSVs are stored outside the public web root with a random-UUID batch
key. The prototype keeps files locally; production should use object storage
with encryption, retention, and malware scanning.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
STORAGE_ROOT = Path("var/storage")


def save_upload(content: bytes, batch_id: str) -> tuple[str, str, int]:
    """Persist bytes and return ``(storage_key, sha256, size)``."""
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    key = f"submissions/{batch_id}.csv"
    path = STORAGE_ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    return key, digest, len(content)
