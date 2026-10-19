"""Keep the published HACS archive and project license consistent."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hacs_archive_preserves_mit_license_and_notices(tmp_path):
    output = tmp_path / "salus.zip"
    subprocess.run(
        [sys.executable, "scripts/package_hacs_release.py", "--output", str(output)],
        cwd=ROOT,
        check=True,
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["license"] == "MIT"
    assert set(project["license-files"]) == {"LICENSE", "NOTICE"}
    assert not (ROOT / "LICENSE-APACHE").exists()

    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert archive.read("LICENSE") == (ROOT / "LICENSE").read_bytes()
        assert archive.read("NOTICE") == (ROOT / "NOTICE").read_bytes()
        assert "Copyright (c) 2020 Konrad Banachowicz" in archive.read("LICENSE").decode()
        assert json.loads(archive.read("manifest.json"))["version"] == project["version"]
