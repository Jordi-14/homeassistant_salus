"""Durable private backup, completed before a floor-comfort command."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from homeassistant.util.file import write_utf8_file_atomic
from salus_it600.comfort_warm_floor import build_comfort_warm_floor_command


def persist_floor_backup(path: str, record: dict) -> None:
    """Run in an executor: atomically write, fsync, then verify from disk.

    Store.async_save logs some write errors without raising them. A mandatory
    pre-command backup must propagate those failures, so use the atomic writer
    directly and check the actual file rather than an in-memory Store cache.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if record.get("pending") and target.exists():
        previous = json.loads(target.read_text(encoding="utf-8"))
        if previous.get("pending"):
            # This journal survives HA restarts, unlike a client's async lock.
            # Resolve an uncertain command from exact fresh read-back; never
            # replay it or overwrite its only backup while still uncertain.
            command = build_comfort_warm_floor_command(previous["before"], previous["requested_level"])
            if command is None:
                raise OSError("Previous floor-comfort journal is not a valid actual change")
            old = previous["before"]["sIT600TH"]["Schedule"]
            expected = "72" + command[8:] + old[120:]
            fresh = record["before"]["sIT600TH"]
            if any(str(fresh.get(alias, "")).lower() != expected.lower() for alias in ("Schedule", "Status_2_d")):
                raise OSError("Previous floor-comfort command remains unconfirmed; backup retained")
    write_utf8_file_atomic(path, json.dumps(record, ensure_ascii=True), private=True)
    if json.loads(target.read_text(encoding="utf-8")) != record:
        raise OSError("Saved floor-comfort backup did not match the snapshot")


def mark_floor_backup_confirmed(path: str) -> None:
    """Mark completion only after the client's exact read-back succeeds."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    record["pending"] = False
    record["confirmed_at"] = datetime.now(UTC).isoformat()
    persist_floor_backup(path, record)
