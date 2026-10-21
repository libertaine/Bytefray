"""Assemble the license notices shipped with the frozen Windows distribution.

Run with the build environment's own interpreter after the PyInstaller builds,
so the versions and license files read here are the ones that were frozen:

    python tools/collect_third_party_notices.py --dist dist/windows --spectator-license <Spectator LICENSE>

Writes ``<dist>/licenses/``: one folder per shipped component holding its
license texts, and ``THIRD_PARTY_NOTICES.md`` indexing them. A component is
listed when its code is in a frozen application tree (or, for Spectator, its
staged folder), so the notices follow what actually ships. Texts that no
build input provides are kept in ``tools/third_party_notices/`` (see its
SOURCES.md). Any expected text that is missing stops the build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from importlib.metadata import distribution
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTICES = REPO_ROOT / "tools" / "third_party_notices"
COMPANION = REPO_ROOT / "tools" / "spectator_companion.json"
APPLICATION_TREES = ("bytefray", "bytefray-cli", "bytefray-agent-designer", "bytefray-replay-viewer")


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _frozen(dist: Path, package: str) -> bool:
    return any((dist / tree / "_internal" / package).is_dir() for tree in APPLICATION_TREES)


def _dist_license_files(name: str) -> list[Path]:
    found = distribution(name)
    files = [
        Path(str(found.locate_file(entry)))
        for entry in found.files or ()
        if any(word in entry.name.lower() for word in ("license", "copying", "notice"))
    ]
    if not files:
        raise SystemExit(f"{name} {found.version} ships no license file in its metadata")
    return files


class Notices:
    def __init__(self, out: Path) -> None:
        self.out = out
        self.rows: list[tuple[str, str, str, str, list[str]]] = []

    def add(
        self, folder: str, component: str, version: str, license_name: str, source: str,
        files: list[Path], *, trees: tuple[Path, ...] = (),
    ) -> None:
        """Copy ``files`` into ``folder`` and every file under each of ``trees``
        into ``folder/<tree name>/``, keeping its relative path (several
        upstream packages each call their text ``LICENSE.txt``)."""

        target = self.out / folder
        target.mkdir(parents=True, exist_ok=True)
        copies = [(path, Path(path.name)) for path in files]
        for tree in trees:
            if not tree.is_dir():
                raise SystemExit(f"Missing license texts for {component}: {tree}")
            copies += [(path, Path(tree.name) / path.relative_to(tree)) for path in sorted(tree.rglob("*")) if path.is_file()]
        names = []
        for path, relative in copies:
            if not path.is_file():
                raise SystemExit(f"Missing license text for {component}: {path}")
            (target / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target / relative)
            names.append(f"{folder}/{relative.as_posix()}")
        self.rows.append((component, version, license_name, source, names))

    def write_index(self, extra: str) -> None:
        lines = [
            "# Third-party notices",
            "",
            "Bytefray for Windows bundles the components below. Each folder in this",
            "directory holds the license texts for one component.",
            "",
            "| Component | Version | License | Source | License texts |",
            "| --- | --- | --- | --- | --- |",
        ]
        for component, version, license_name, source, names in self.rows:
            lines.append(f"| {component} | {version} | {license_name} | {source} | {', '.join(f'`{n}`' for n in names)} |")
        (self.out / "THIRD_PARTY_NOTICES.md").write_text("\n".join(lines) + "\n\n" + extra, encoding="utf-8")


def collect(dist: Path, spectator_license: Path | None) -> Path:
    out = dist / "licenses"
    if out.exists():
        shutil.rmtree(out)
    notices = Notices(out)

    project = distribution("bytefray")
    notices.add("bytefray", "Bytefray", project.version, "MIT", "https://github.com/libertaine/Bytefray",
                [REPO_ROOT / "LICENSE"])
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    notices.add("python", "Python runtime (with the third-party components its license lists)",
                sys.version.split()[0], "PSF-2.0", "https://www.python.org/", [python_license])
    notices.add("pyinstaller", "PyInstaller bootloader", distribution("pyinstaller").version,
                "GPL-2.0-or-later WITH Bootloader-exception", "https://pyinstaller.org/",
                _dist_license_files("pyinstaller"))
    sources: list[str] = []
    if _frozen(dist, "PySide6"):
        version = distribution("PySide6").version
        qt_texts = NOTICES / f"qt-{version}"
        if not qt_texts.is_dir():
            raise SystemExit(f"tools/third_party_notices has no texts for Qt {version}")
        notices.add("qt-pyside6", "Qt for Python (PySide6, Shiboken6), the Qt libraries it bundles and their "
                    "third-party components (including Mesa llvmpipe, opengl32sw.dll)", version,
                    "LGPL-3.0-only (used unmodified, as replaceable DLLs); components as listed",
                    "https://www.qt.io/",
                    # The wheels' only license file is Qt's commercial-licensee notice, which
                    # does not apply: Bytefray uses Qt under the LGPL.
                    [NOTICES / "gnu" / "lgpl-3.0.txt", NOTICES / "gnu" / "gpl-3.0.txt",
                     qt_texts / "QT_THIRD_PARTY_NOTICES.txt"])
        minor = ".".join(version.split(".")[:2])
        sources += [
            (
                f"- Qt {version} (Qt Core, GUI, Widgets, Network and SVG in `qtbase` and `qtsvg`; image formats in "
                f"`qtimageformats`): https://download.qt.io/official_releases/qt/{minor}/{version}/submodules/ "
                f"(`qtbase-everywhere-src-{version}.tar.xz`, `qtsvg-everywhere-src-{version}.tar.xz`, "
                f"`qtimageformats-everywhere-src-{version}.tar.xz`)"
            ),
            (
                f"- PySide6 and Shiboken6 {version}: https://download.qt.io/official_releases/QtForPython/pyside6/"
                f"PySide6-{version}-src/pyside-setup-everywhere-src-{version}.tar.xz"
            ),
        ]
    if _frozen(dist, "pygame"):
        found = distribution("pygame-ce")
        bundled_texts = NOTICES / f"pygame-ce-{found.version}"
        prebuilts = NOTICES / "sdl-windows-prebuilts"
        if not bundled_texts.is_dir():
            raise SystemExit(f"tools/third_party_notices has no texts for pygame-ce {found.version}")
        lgpl = Path(str(found.locate_file("pygame/docs/generated/LGPL.txt")))
        notices.add("pygame-ce", "pygame-ce and the SDL2, image, audio-codec and font libraries it bundles",
                    found.version, "LGPL-2.1-or-later; bundled libraries under their own licenses",
                    f"https://github.com/pygame-community/pygame-ce/tree/{found.version}",
                    [lgpl, *sorted(bundled_texts.glob("LICENSE.*.txt"))],
                    trees=tuple(sorted(path for path in prebuilts.iterdir() if path.is_dir())))
        sources.append(
            f"- pygame-ce {found.version}: https://github.com/pygame-community/pygame-ce/archive/refs/tags/"
            f"{found.version}.tar.gz (also the `pygame_ce-{found.version}` source distribution on PyPI)"
        )
    if _frozen(dist, "yaml"):
        notices.add("pyyaml", "PyYAML", distribution("PyYAML").version, "MIT", "https://pyyaml.org/",
                    _dist_license_files("PyYAML"))

    spectator_dir = dist / "bytefray-spectator"
    if spectator_dir.is_dir():
        companion = json.loads(COMPANION.read_text(encoding="utf-8"))
        if spectator_license is None or _lf_sha256(spectator_license) != companion["license"]["sha256_lf"]:
            raise SystemExit("--spectator-license must be the pinned Bytefray Spectator LICENSE")
        notices.add("bytefray-spectator", companion["name"], companion["version"], companion["license"]["spdx"],
                    "https://github.com/libertaine/Bytefray-Spectator", [spectator_license])
        godot = NOTICES / "godot-4.7.2-stable"
        if "Godot 4.7.2" not in companion["build"]["engine"]:
            raise SystemExit("tools/third_party_notices has no texts for the pinned Godot version")
        notices.add("godot", "Godot Engine (Spectator's runtime) and the third-party code COPYRIGHT.txt lists",
                    "4.7.2-stable", "MIT; components as listed in COPYRIGHT.txt", "https://godotengine.org/",
                    [godot / "LICENSE.txt", godot / "COPYRIGHT.txt"])

    notices.write_index(
        "## Bundled binaries\n"
        "\n"
        "pygame-ce's SDL2, SDL2_image, SDL2_mixer and SDL2_ttf libraries and their optional\n"
        "codec libraries are the unmodified binaries of the upstream SDL release packages\n"
        "(SDL2 2.32.10, SDL2_image 2.8.12-pgce, SDL2_mixer 2.8.2, SDL2_ttf 2.24.0); the license\n"
        "texts in `pygame-ce/` are the ones those packages ship, including WavPack and libxmp,\n"
        "and FreeType and HarfBuzz, which SDL2_ttf links statically. `qt-pyside6/` holds the\n"
        "copyright statements and license texts of the third-party code in the shipped Qt\n"
        "modules, from Qt's own documentation for this Qt version.\n"
        "\n"
        "## Corresponding source for the LGPL-licensed libraries\n"
        "\n"
        "Qt, PySide6/Shiboken6 and pygame-ce are used unmodified, as separate DLLs and\n"
        "extension modules that can be replaced in an application's `_internal` folder. Their\n"
        "complete corresponding source for the versions shipped here:\n"
        "\n" + "\n".join(sources) + "\n"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--spectator-license", type=Path)
    args = parser.parse_args(argv)
    out = collect(args.dist.resolve(), args.spectator_license)
    print(f"[notices] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
