"""Windows version resources for the frozen Bytefray executables.

Each ``tools/*.spec`` passes ``executable_version_info(...)`` to ``EXE(version=...)``
so Explorer's Details tab, installers and support tooling can identify a
binary. The version comes from ``pyproject.toml``, the one place the
application version is defined, so a spec can never stamp a stale number.

Windows stores a binary version as four 16-bit numbers and has no prerelease
syntax, so the fourth field encodes the release stage the way CPython's own
Windows builds do: ``100 * level + serial`` with alpha = 1, beta = 2, rc = 3
and final = 9. ``5.1.0a1`` is therefore ``5.1.0.101`` and the final ``5.1.0``
would be ``5.1.0.900``, which keeps every later build numerically greater.
The string fields carry the public SemVer spelling (``5.1.0-alpha.1``).

PyInstaller is imported only inside :func:`executable_version_info`, which
returns ``None`` where PyInstaller's Windows version-resource support is not
importable (non-Windows hosts and the stubbed spec tests).
``tools/build_win.ps1`` checks every built executable's version resource, so
a real build cannot silently ship without one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PUBLISHER = "Bytefray Project"
PRODUCT_NAME = "Bytefray"
COPYRIGHT = "Copyright (c) 2025 Rod Satterfield. MIT License."

_PEP440 = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$")
_LEVELS = {"a": 1, "b": 2, "rc": 3, None: 9}
_SEMVER_STAGES = {"a": "alpha", "b": "beta", "rc": "rc"}
_VS_FF_PRERELEASE = 0x2


def project_version(project_root: str | Path) -> str:
    """The ``[project] version`` declared in ``pyproject.toml`` (PEP 440 form)."""

    text = (Path(project_root) / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
    if match is None:
        raise SystemExit("pyproject.toml declares no [project] version")
    return match.group(1)


def _parse(version: str) -> tuple[int, int, int, str | None, int]:
    match = _PEP440.match(version)
    if match is None:
        raise SystemExit(f"Cannot stamp a Windows version resource for version {version!r}")
    major, minor, patch, stage, serial = match.groups()
    return int(major), int(minor), int(patch), stage, int(serial or 0)


def windows_file_version(version: str) -> tuple[int, int, int, int]:
    """``5.1.0a1`` -> ``(5, 1, 0, 101)``; see the module docstring for the encoding."""

    major, minor, patch, stage, serial = _parse(version)
    if serial > 99:
        raise SystemExit(f"Prerelease serial {serial} does not fit the Windows build field")
    return major, minor, patch, 100 * _LEVELS[stage] + serial


def public_version(version: str) -> str:
    """``5.1.0a1`` -> ``5.1.0-alpha.1`` (docs/COMPONENT_VERSIONING.md §4.1)."""

    major, minor, patch, stage, serial = _parse(version)
    suffix = "" if stage is None else f"-{_SEMVER_STAGES[stage]}.{serial}"
    return f"{major}.{minor}.{patch}{suffix}"


def executable_version_info(project_root: str | Path, name: str, description: str) -> Any:
    """A PyInstaller ``VSVersionInfo`` for ``<name>.exe``, or ``None`` (see module docstring)."""

    try:
        from PyInstaller.utils.win32 import versioninfo as vi  # type: ignore[import-untyped]
    except ImportError:
        return None
    version = project_version(project_root)
    numeric = windows_file_version(version)
    public = public_version(version)
    strings = [
        vi.StringStruct("CompanyName", PUBLISHER),
        vi.StringStruct("FileDescription", description),
        vi.StringStruct("FileVersion", public),
        vi.StringStruct("InternalName", name),
        vi.StringStruct("LegalCopyright", COPYRIGHT),
        vi.StringStruct("OriginalFilename", f"{name}.exe"),
        vi.StringStruct("ProductName", PRODUCT_NAME),
        vi.StringStruct("ProductVersion", public),
    ]
    return vi.VSVersionInfo(
        ffi=vi.FixedFileInfo(
            filevers=numeric,
            prodvers=numeric,
            mask=0x3F,
            flags=0 if numeric[3] >= 900 else _VS_FF_PRERELEASE,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            vi.StringFileInfo([vi.StringTable("040904B0", strings)]),
            vi.VarFileInfo([vi.VarStruct("Translation", [0x0409, 1200])]),
        ],
    )


if __name__ == "__main__":
    # tools/build_win.ps1 checks the built executables against these values.
    root = Path(__file__).resolve().parents[1]
    package = project_version(root)
    print(json.dumps({
        "package": package,
        "public": public_version(package),
        "file_version": ".".join(str(part) for part in windows_file_version(package)),
    }))
