"""PyInstaller runtime hook: an installed Bytefray uses the data root its installer recorded.

Every Windows spec in ``tools/`` lists this file in ``runtime_hooks``, so it runs
inside each frozen executable before the application's own code. It does
nothing unless an installation record sits beside the onedir application
folders -- ``<install>/bin/bytefray-install.json``, written by
``tools/installer.iss`` -- so source checkouts, wheel installs and portable
``dist/`` trees keep their existing data-root rules (``battle_engine.paths``).

When the record exists, ``BYTEFRAY_ROOT`` is set to its ``data_root`` even if
the variable was already set. Bytefray 5.0's per-machine installer sets
``BYTEFRAY_ROOT`` machine-wide; a side-by-side 5.1 Alpha that honored the
inherited value would read and write the stable release's agents, runs and
caches. Designer passes its own data root to every child process, and each
child reads the same record, so the whole application agrees on one root.

A record that exists but cannot be used stops the application with an
explanation instead of silently falling back to another data root. So does an
installed layout without its record -- Inno Setup's ``unins*.exe`` beside
``bin``, which a portable tree never has -- and a data root that resolves inside
the program folder (or contains it): that folder belongs to the installer, whose
upgrades replace its files and whose uninstaller removes them. Paths are
compared fully resolved, so an 8.3 short
name or a junction cannot disguise one folder as another.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import MutableMapping
from pathlib import Path

INSTALLATION_FILE = "bytefray-install.json"
INSTALLATION_SCHEMA = "bytefray.installation"
INSTALLATION_SCHEMA_VERSION = 1


def installation_record_path(executable: str | os.PathLike[str]) -> Path:
    """``<install>/bin/<app>/<app>.exe`` -> ``<install>/bin/bytefray-install.json``."""

    return Path(executable).resolve().parent.parent / INSTALLATION_FILE


def _is_inside(path: Path, folder: Path) -> bool:
    return path == folder or folder in path.parents


def recorded_data_root(executable: str | os.PathLike[str]) -> Path | None:
    """The data root the installation recorded, or ``None`` when not installed."""

    record_path = installation_record_path(executable)
    install_root = record_path.parent.parent
    if not record_path.is_file():
        if any(install_root.glob("unins*.exe")):
            raise RuntimeError(
                f"The Bytefray installation in {install_root} is missing its installation record "
                f"{record_path}. Reinstall Bytefray to repair it."
            )
        return None
    try:
        # The installer writes UTF-8 with a byte-order mark.
        record = json.loads(record_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"The Bytefray installation record {record_path} cannot be read ({exc}). "
            "Reinstall Bytefray to repair it."
        ) from exc
    if not isinstance(record, dict) or (record.get("schema"), record.get("schema_version")) != (
        INSTALLATION_SCHEMA,
        INSTALLATION_SCHEMA_VERSION,
    ):
        raise RuntimeError(
            f"The Bytefray installation record {record_path} is not a "
            f"{INSTALLATION_SCHEMA} v{INSTALLATION_SCHEMA_VERSION} record. Reinstall Bytefray to repair it."
        )
    data_root = record.get("data_root")
    if not isinstance(data_root, str) or not data_root.strip() or not Path(data_root).is_absolute():
        raise RuntimeError(
            f"The Bytefray installation record {record_path} has no absolute data_root. "
            "Reinstall Bytefray to repair it."
        )
    resolved_data, resolved_install = Path(data_root).resolve(), install_root.resolve()
    if _is_inside(resolved_data, resolved_install) or _is_inside(resolved_install, resolved_data):
        raise RuntimeError(
            f"The Bytefray data folder {data_root} and the installation folder {install_root} overlap. "
            "Reinstall Bytefray with separate folders (/BYTEFRAYDATAROOT=<folder>)."
        )
    return Path(data_root)


def apply(executable: str | os.PathLike[str], environ: MutableMapping[str, str]) -> Path | None:
    """Point ``BYTEFRAY_ROOT`` at the recorded data root; return it (or ``None``)."""

    data_root = recorded_data_root(executable)
    if data_root is not None:
        environ["BYTEFRAY_ROOT"] = str(data_root)
    return data_root


if getattr(sys, "frozen", False):
    apply(sys.executable, os.environ)
