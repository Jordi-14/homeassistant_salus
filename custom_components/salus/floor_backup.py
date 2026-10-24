"""Durable private backup, completed before a floor-comfort command."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.util.file import write_utf8_file_atomic


def persist_floor_backup(path: str, record: dict) -> None:
    """Run in an executor: atomically write, fsync, then verify from disk.

    Store.async_save logs some write errors without raising them. A mandatory
    pre-command backup must propagate those failures, so use the atomic writer
    directly and check the actual file rather than an in-memory Store cache.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_utf8_file_atomic(path, json.dumps(record, ensure_ascii=True), private=True)
    if json.loads(target.read_text(encoding="utf-8")) != record:
        raise OSError("Saved floor-comfort backup did not match the snapshot")
