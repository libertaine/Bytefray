"""tools/collect_third_party_notices.py ships a license text for each bundled component."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytest.importorskip("PyInstaller")
pytest.importorskip("PySide6")
pytest.importorskip("pygame")

from tools import collect_third_party_notices as notices


def _dist(tmp_path: Path, *, spectator: bool) -> Path:
    dist = tmp_path / "dist windows"
    for package in ("PySide6", "pygame", "yaml"):
        (dist / "bytefray" / "_internal" / package).mkdir(parents=True)
    if spectator:
        (dist / "bytefray-spectator").mkdir(parents=True)
    return dist


def _spectator_license(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "LICENSE"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_notices_cover_every_bundled_component(tmp_path: Path) -> None:
    dist = _dist(tmp_path, spectator=False)
    out = notices.collect(dist, None)
    index = (out / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for expected in ("bytefray/LICENSE", "python/LICENSE.txt", "pyinstaller/COPYING.txt",
                     "qt-pyside6/lgpl-3.0.txt", "qt-pyside6/gpl-3.0.txt", "qt-pyside6/QT_THIRD_PARTY_NOTICES.txt",
                     "pygame-ce/LGPL.txt", "pygame-ce/LICENSE.sdl2.txt",
                     # The texts for the shipped DLLs, from the SDL packages pygame-ce builds with.
                     "pygame-ce/SDL2_mixer-2.8.2/LICENSE.wavpack.txt", "pygame-ce/SDL2_mixer-2.8.2/LICENSE.xmp.txt",
                     "pygame-ce/SDL2_ttf-2.24.0/LICENSE.txt",
                     "pygame-ce/SDL2_ttf-2.24.0/vendored/harfbuzz-COPYING.txt",
                     "pygame-ce/SDL2_image-2.8.12/LICENSE.libjpegturbo.md", "pyyaml/LICENSE"):
        assert (out / expected).is_file(), expected
        assert f"`{expected}`" in index
    qt = (out / "qt-pyside6" / "QT_THIRD_PARTY_NOTICES.txt").read_text(encoding="utf-8")
    assert "Mesa llvmpipe" in qt and "PCRE2" in qt and "HarfBuzz" in qt
    # Qt's commercial-licensee notice does not describe how Bytefray uses Qt.
    assert not (out / "qt-pyside6" / "LicenseRef-Qt-Commercial.txt").exists()
    assert "bytefray-spectator" not in index  # not staged, not listed
    # Exact corresponding source for each LGPL component, for the shipped versions.
    sources = index[index.index("## Corresponding source") :]
    qt_version = notices.distribution("PySide6").version
    for expected in (f"qtbase-everywhere-src-{qt_version}.tar.xz", f"pyside-setup-everywhere-src-{qt_version}.tar.xz",
                     f"pygame-ce/archive/refs/tags/{notices.distribution('pygame-ce').version}.tar.gz"):
        assert expected in sources, expected


def test_spectator_and_godot_notices_need_the_pinned_license(tmp_path: Path, monkeypatch) -> None:
    pinned_text = "MIT License\n\nCopyright (c) 2026 Example\n"
    companion = json.loads((ROOT / "tools" / "spectator_companion.json").read_text(encoding="utf-8"))
    companion["license"]["sha256_lf"] = notices.hashlib.sha256(pinned_text.encode("utf-8")).hexdigest()
    pin = tmp_path / "spectator_companion.json"
    pin.write_text(json.dumps(companion), encoding="utf-8")
    monkeypatch.setattr(notices, "COMPANION", pin)
    dist = _dist(tmp_path, spectator=True)
    with pytest.raises(SystemExit):
        notices.collect(dist, None)
    with pytest.raises(SystemExit):
        notices.collect(dist, _spectator_license(tmp_path, "MIT License\n\nsomething else\n"))
    # The pinned text is accepted whatever its line endings (a Windows checkout has CRLF).
    out = notices.collect(dist, _spectator_license(tmp_path, pinned_text.replace("\n", "\r\n")))
    for expected in ("bytefray-spectator/LICENSE", "godot/LICENSE.txt", "godot/COPYRIGHT.txt"):
        assert (out / expected).is_file(), expected
    assert f"{companion['name']} | {companion['version']}" in (out / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
