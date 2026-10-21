"""tools/build_win.ps1's 5.1 release steps stay in place.

The real Windows build is the behavioral test of these steps (it fails when
one of them fails); these source checks keep a later edit from silently
dropping one, as engine/tests/test_windows_packaging_spec.py does for the
earlier steps.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "tools" / "build_win.ps1").read_text(encoding="utf-8")


def test_unused_qt_components_are_omitted_before_the_payload_checks() -> None:
    from tools import omit_unused_qt

    assert 'tools\\omit_unused_qt.py") --dist $DistDir' in SOURCE
    # Before the payload checks and every smoke test, so those run on the shipped tree.
    assert SOURCE.index("omit_unused_qt.py") < SOURCE.index("# Verify no Python bytecode/cache")
    assert {"qtvirtualkeyboardplugin.dll", "qt6virtualkeyboard.dll", "qpdf.dll", "qt6pdf.dll", "qt6quick.dll",
            "qt6qml.dll", "qt6opengl.dll"} <= omit_unused_qt.OMITTED_NAMES
    # Libraries Bytefray needs are never on the list.
    assert not {"qt6core.dll", "qt6gui.dll", "qt6widgets.dll", "qt6network.dll", "qt6svg.dll", "qwindows.dll",
                "opengl32sw.dll"} & omit_unused_qt.OMITTED_NAMES


def test_omitting_deletes_only_the_listed_files(tmp_path: Path) -> None:
    from tools import omit_unused_qt

    tree = tmp_path / "bytefray-agent-designer"
    kept = tree / "_internal" / "PySide6" / "Qt6Widgets.dll"
    listed = [tree / "_internal" / Path(*relative.split("/")) for relative in omit_unused_qt.OMITTED]
    for path in [kept, *listed]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    assert sorted(omit_unused_qt.omit(tree)) == sorted(listed)
    assert kept.is_file() and not any(path.exists() for path in listed)


def test_a_binary_that_still_imports_an_omitted_library_is_reported(tmp_path: Path) -> None:
    """The real qpdf plugin imports Qt6Pdf.dll: renamed so it survives omission, it
    must be reported as dangling -- the check that fails the build."""

    pytest.importorskip("pefile")
    pyside = pytest.importorskip("PySide6")
    plugin = Path(pyside.__file__).parent / "plugins" / "imageformats" / "qpdf.dll"
    if not plugin.is_file():
        pytest.skip("this PySide6 build has no qpdf plugin")
    from tools import omit_unused_qt

    tree = tmp_path / "app"
    (tree / "_internal").mkdir(parents=True)
    shutil.copyfile(plugin, tree / "_internal" / "renamed-plugin.dll")
    dangling = omit_unused_qt.dangling_imports(tree)
    assert [(path.name, name) for path, name in dangling] == [("renamed-plugin.dll", "qt6pdf.dll")]


def test_release_builds_can_pin_every_dependency() -> None:
    assert "[string]$Constraints" in SOURCE
    assert '$ConstraintArgs = @("-c", (Resolve-Path -LiteralPath $Constraints).Path)' in SOURCE
    pins = (ROOT / "tools" / "windows-build-constraints.txt").read_text(encoding="utf-8")
    for pin in ("pyinstaller==6.22.2", "PySide6==6.11.2", "pygame-ce==2.5.8", "PyYAML==6.0.3"):
        assert pin in pins


def test_only_the_pinned_spectator_build_is_staged_and_self_checked() -> None:
    companion = json.loads((ROOT / "tools" / "spectator_companion.json").read_text(encoding="utf-8"))
    assert companion["version"] == "0.1.0-alpha.1"
    assert len(companion["windows"]["sha256"]) == 64
    assert "if ($SpectatorHash -ne $Companion.windows.sha256)" in SOURCE
    assert '"--fixture=sample", "--check"' in SOURCE
    assert 'Join-Path $SpectatorDir "SPECTATOR_BUILD.json"' in SOURCE


def test_every_scaffold_template_is_smoke_tested_from_the_frozen_cli() -> None:
    for template in TEMPLATE_DIRECTORIES:
        if template != "blank":  # the blank template is the default (no --template)
            assert f"'--template', '{template}'" in SOURCE, template
    assert "under Classic exited $LASTEXITCODE; expected the capability refusal (2)" in SOURCE


def test_frozen_spectator_commands_run_redirected_under_a_non_ansi_path() -> None:
    block = SOURCE[SOURCE.index("# Exercise 'bytefray spectator'") : SOURCE.index("# Final proof")]
    for command in ('"spectator", "export"', '"spectator", "verify"', "spectator prepare"):
        assert command in block
    assert "[char]0x03A9" in block
    assert "*>> $SmokeLog" in block
    assert "$Status.reused -ne $Expected" in block


def test_version_resources_and_notices_are_produced() -> None:
    assert 'tools\\windows_version_info.py' in SOURCE
    assert "$Info.ProductVersion -ne $Versions.public" in SOURCE
    assert 'tools\\collect_third_party_notices.py' in SOURCE
