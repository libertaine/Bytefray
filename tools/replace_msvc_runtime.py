"""Ship one Microsoft-signed Visual C++ runtime in every frozen Bytefray application.

PyInstaller copies whatever runtime DLLs its inputs carry. The first
5.1.0-alpha.1 build therefore shipped CPython's 14.42 ``VCRUNTIME140.dll`` at the
root of each ``_internal`` folder and, beside PySide6 and Shiboken6, 14.44
copies that The Qt Company had re-signed with its own certificate. Windows loads
one module per name, so each Qt process ran a 14.42/14.44 mix; and the
re-signed copies are not the unmodified files the Visual Studio Distributable
Code terms allow to be redistributed.

``tools/msvc_runtime.json`` pins one runtime version, the exact files of the
licensed Visual Studio's ``VC\\redist`` folder (name, size, SHA-256) and the
locations where the frozen trees carry them. :func:`replace` checks every source
file against the pin (including its PE version resource), requires the runtime
DLLs found in the trees to be exactly the pinned locations -- no other
Microsoft C/C++ runtime file may appear -- copies the pinned bytes over each
copy, and re-hashes the result. Anything unexpected stops the build and leaves
the trees unchanged. ``tools/build_win.ps1`` verifies each source file's
Microsoft signature before calling it. Requires ``pefile`` (the
``windows-build`` extra).

    python tools/replace_msvc_runtime.py --dist dist/windows --source <VC\\redist\\...\\Microsoft.VC145.CRT> \\
        --pin tools/msvc_runtime.json --record build/windows/msvc-runtime-replacement.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

#: Microsoft C/C++ runtime and UCRT file names. Any of them in a frozen tree
#: must be one of the pinned locations.
RUNTIME_FAMILY = re.compile(
    r"^(vcruntime140(_1|_threads)?|msvcp140(_1|_2|_atomic_wait|_codecvt_ids)?|concrt140|vccorlib140|vcomp140|"
    r"vcamp140|mfc140\w*|mfcm140\w*|ucrtbase|api-ms-win-crt-[\w-]+)\.dll$",
    re.IGNORECASE,
)
#: Trees that are not PyInstaller output; the Spectator is a separately pinned build.
SKIPPED_TREES = frozenset({"bytefray-spectator", "licenses"})


class RuntimeMismatch(Exception):
    """A source file, a frozen tree or a result does not match the pin."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pe_file_version(path: Path) -> str:
    """The ``VS_FIXEDFILEINFO`` file version, e.g. ``14.51.36247.0``."""

    import pefile  # type: ignore[import-untyped]

    image = pefile.PE(str(path), fast_load=True)
    image.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
    info = image.VS_FIXEDFILEINFO[0]
    return ".".join(str(part) for part in (info.FileVersionMS >> 16, info.FileVersionMS & 0xFFFF,
                                           info.FileVersionLS >> 16, info.FileVersionLS & 0xFFFF))


def load_pin(path: Path) -> dict[str, Any]:
    pin = json.loads(path.read_text(encoding="utf-8"))
    if (pin.get("schema"), pin.get("schema_version")) != ("bytefray.msvc-runtime-pin", 1):
        raise RuntimeMismatch(f"{path} is not a bytefray.msvc-runtime-pin v1 file")
    return pin


def check_sources(source: Path, pin: dict[str, Any],
                  version_of: Callable[[Path], str] = pe_file_version) -> dict[str, Path]:
    """The pinned source files by lower-case name, each checked against the pin."""

    present = {path.name.lower(): path for path in source.iterdir() if path.is_file()}
    found = {}
    for name, expected in pin["files"].items():
        path = present.get(name.lower())
        if path is None:
            raise RuntimeMismatch(f"{source} has no {name}")
        if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise RuntimeMismatch(f"{path} is not the pinned {name} (SHA-256 {sha256(path)})")
        if version_of(path) != pin["version"]:
            raise RuntimeMismatch(f"{path} is version {version_of(path)}, not {pin['version']}")
        found[name.lower()] = path
    return found


def runtime_copies(dist: Path) -> list[str]:
    """Every Microsoft runtime file in the frozen trees, relative to ``dist`` (``/``-separated)."""

    found = []
    for tree in sorted(path for path in dist.iterdir() if path.is_dir() and path.name not in SKIPPED_TREES):
        found += [path.relative_to(dist).as_posix() for path in tree.rglob("*")
                  if path.is_file() and RUNTIME_FAMILY.match(path.name)]
    return sorted(found)


def check_locations(dist: Path, pin: dict[str, Any]) -> list[str]:
    """The runtime copies in ``dist``, which must be exactly the pinned locations."""

    found = runtime_copies(dist)
    expected = {location.lower(): location for location in pin["locations"]}
    names = {name.lower() for name in pin["files"]}
    unexpected = [path for path in found if path.lower() not in expected]
    missing = sorted(set(expected) - {path.lower() for path in found})
    unpinned = [path for path in found if PurePosixPath(path).name.lower() not in names]
    if unexpected or missing or unpinned:
        raise RuntimeMismatch(f"runtime files differ from the pin: unexpected {unexpected}, missing {missing}, "
                              f"unpinned names {unpinned}")
    return found


def replace(dist: Path, source: Path, pin: dict[str, Any],
            version_of: Callable[[Path], str] = pe_file_version) -> list[dict[str, str]]:
    """Check everything first, then copy the pinned files over every runtime copy."""

    sources = check_sources(source, pin, version_of)
    locations = check_locations(dist, pin)
    plan = []
    for location in locations:
        name = PurePosixPath(location).name.lower()
        target = dist / Path(*PurePosixPath(location).parts)
        plan.append((location, target, sources[name], sha256(target)))
    replaced = []
    for location, target, origin, before in plan:
        target.write_bytes(origin.read_bytes())
        after = sha256(target)
        if after != pin["files"][PurePosixPath(location).name.lower()]["sha256"]:
            raise RuntimeMismatch(f"{target} has SHA-256 {after} after replacement")
        replaced.append({"location": location, "sha256_before": before, "sha256_after": after})
    return replaced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pin", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pin = load_pin(args.pin)
        replaced = replace(args.dist, args.source, pin)
    except RuntimeMismatch as exc:
        print(f"ERROR: {exc}")
        return 1
    record = {
        "schema": "bytefray.msvc-runtime-replacement", "schema_version": 1,
        "version": pin["version"], "grant": pin["grant"], "source": pin["source"],
        "files": pin["files"], "replaced": replaced,
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"[msvc] Replaced {len(replaced)} runtime copies with the pinned {pin['version']} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
