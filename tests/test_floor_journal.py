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


@pytest.mark.parametrize("old_encoder", [False, True])
def test_pending_journal_resolves_device_owned_metadata_and_legacy_echo(tmp_path, old_encoder):
    path = str(tmp_path / "backup.json")
    original = record(before(), 3)
    persist_floor_backup(path, original)
    after = copy.deepcopy(before())
    blob = bytearray.fromhex(BASE)
    echo_body = bytearray(blob[:60])
    echo_body[0], echo_body[39] = 0x73, 3
    if old_encoder:
        echo_body[1], echo_body[40:42] = 8, bytes.fromhex('0ffd')
    blob[1], blob[39], blob[40:42] = 8, 3, bytes.fromhex('0ffd')
    after['sIT600TH']['Schedule'] = after['sIT600TH']['Status_2_d'] = blob.hex()
    after['sIT600I']['CommandResponse_d'] = '423131' + echo_body.hex() + '00'
    new = record(after, 1)
    persist_floor_backup(path, new)
    assert json.loads((tmp_path / 'backup.json').read_text()) == new


@pytest.mark.parametrize("change", ['language', 'setpoint', 'identity', 'echo', 'wrong_level'])
def test_journal_never_resolves_unrelated_changes_or_wrong_echo(tmp_path, change):
    path = str(tmp_path / 'backup.json')
    original = record(before(), 3)
    persist_floor_backup(path, original)
    after = copy.deepcopy(before())
    blob = bytearray.fromhex(BASE)
    blob[39] = 3
    after['sIT600I']['CommandResponse_d'] = '42313173' + blob[1:60].hex() + '00'
    if change == 'language':
        blob[42] = 2
    elif change == 'setpoint':
        after['sIT600TH']['HeatingSetpoint_x100'] = 2500
    elif change == 'identity':
        after['data']['UniID'] = 'other'
    elif change == 'echo':
        after['sIT600I']['CommandResponse_d'] = '42313173' + BASE[2:120] + '00'
    else:
        blob[39] = 2
    after['sIT600TH']['Schedule'] = after['sIT600TH']['Status_2_d'] = blob.hex()
    with pytest.raises(OSError, match='unconfirmed'):
        persist_floor_backup(path, record(after, 1))
    assert json.loads((tmp_path / 'backup.json').read_text()) == original
