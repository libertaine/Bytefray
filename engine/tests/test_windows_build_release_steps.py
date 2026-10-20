"""tools/build_win.ps1's 5.1 release steps stay in place.

The real Windows build is the behavioral test of these steps (it fails when
one of them fails); these source checks keep a later edit from silently
dropping one, as engine/tests/test_windows_packaging_spec.py does for the
earlier steps.
"""

from __future__ import annotations

import json
from pathlib import Path

from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "tools" / "build_win.ps1").read_text(encoding="utf-8")


def test_the_gpl_only_qt_virtual_keyboard_is_omitted_and_checked() -> None:
    assert '"PySide6\\plugins\\platforminputcontexts\\qtvirtualkeyboardplugin.dll"' in SOURCE
    assert '"PySide6\\Qt6VirtualKeyboard.dll"' in SOURCE
    assert '-Filter "*virtualkeyboard*"' in SOURCE
    # Before the payload checks and every smoke test, so those run on the shipped tree.
    assert SOURCE.index("$GplOnlyQtFiles") < SOURCE.index("# Verify no Python bytecode/cache")


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
