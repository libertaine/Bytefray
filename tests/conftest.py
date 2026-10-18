"""Isolation shared by the display-backed Designer tests in this directory."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_installed_spectator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never launch a Bytefray Spectator that happens to be installed on this machine.

    Designer prefers Spectator for supported V6 matches when one is found
    (app/services/spectator_viewer.py). Tests that exercise that path configure
    BYTEFRAY_SPECTATOR themselves; every other test sees it turned off.
    """
    monkeypatch.setenv("BYTEFRAY_SPECTATOR", "off")
