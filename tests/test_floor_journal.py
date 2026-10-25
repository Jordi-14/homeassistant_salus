"""An uncertain floor command cannot be replayed after restarting HA."""

import copy
import json

import pytest

from custom_components.salus.floor_backup import (
    mark_floor_backup_confirmed,
    persist_floor_backup,
)

BASE = "720701000001050040000000000104002700100006003500050040000500010000000101800000000dfe010000000100ffffffffffffffffffffffffffffffffffffffffffffffffffffff0000"


def before():
    return {
        "status": "success",
        "data": {"UniID": "test", "Endpoint": 9, "DeviceType": 100},
        "DeviceL": {"ModelIdentifier_i": "SQ610RFNH"},
        "sZDO": {"FirmwareVersion": "00000054"},
        "sIT600TH": {
            "Schedule": BASE,
            "Status_2_d": BASE,
            "PairedTRVShortID": "F" * 24,
            "PairedWCNumber": 1,
            "SystemMode": 4,
        },
        "sIT600I": {"CommandResponse_d": "42313173" + BASE[2:120] + "00"},
    }


def record(snapshot, level):
    return {"pending": True, "requested_level": level, "before": snapshot}


def test_restart_uncertainty_blocks_second_write_and_preserves_original_backup(
    tmp_path,
):
    path = str(tmp_path / "backup.json")
    original = record(before(), 3)
    persist_floor_backup(path, original)
    with pytest.raises(OSError, match="remains unconfirmed"):
        persist_floor_backup(path, record(before(), 1))
    assert json.loads((tmp_path / "backup.json").read_text()) == original


def test_exact_fresh_read_can_resolve_prior_journal_without_replaying_it(tmp_path):
    path = str(tmp_path / "backup.json")
    original = record(before(), 3)
    persist_floor_backup(path, original)
    # Independent known hardware Off(counter 7) -> level 3(counter 8) vector.
    after = copy.deepcopy(before())
    blob = bytearray.fromhex(BASE)
    blob[1] = 8
    blob[39] = 3
    blob[40:42] = bytes.fromhex("0ffd")
    after["sIT600TH"]["Schedule"] = after["sIT600TH"]["Status_2_d"] = blob.hex()
    after["sIT600I"]["CommandResponse_d"] = "4233344c"
    new = record(after, 1)
    persist_floor_backup(path, new)
    assert json.loads((tmp_path / "backup.json").read_text()) == new
    mark_floor_backup_confirmed(path)
    result = json.loads((tmp_path / "backup.json").read_text())
    assert result["pending"] is False
    assert result["before"] == after
    assert result["confirmed_at"]
