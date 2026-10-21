"""Remove Qt components the frozen Bytefray applications cannot use, and prove it.

PyInstaller's PySide6 hooks collect every plugin of each collected plugin type,
together with the libraries those plugins import. Two such plugins can never be
used by Bytefray, and each drags in libraries nothing else needs:

* ``platforminputcontexts/qtvirtualkeyboardplugin.dll`` -- Qt Virtual Keyboard,
  which Qt loads only when ``QT_IM_MODULE`` selects it. It is licensed only under
  the GPL-3.0 (or commercially), not the LGPL the rest of Qt for Python is used
  under, and it imports Qt Quick and its QML runtime (and Qt Quick imports Qt
  OpenGL). Bytefray uses no QML, Quick or OpenGL module.
* ``imageformats/qpdf.dll`` -- reads PDF files as images through Qt PDF (PDFium).
  Bytefray reads only its own PNG/ICO resources.

Bytefray 5.0 shipped all of these unused. :func:`omit` deletes them from each
frozen application tree, and :func:`dangling_imports` then scans the import table
of every remaining ``.exe``/``.dll``/``.pyd`` so that an omission that something
still needs fails the build instead of the application. Requires ``pefile``
(the ``windows-build`` extra).

    python tools/omit_unused_qt.py --dist dist/windows
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath

#: Paths relative to an application's ``_internal`` folder.
OMITTED = (
    "PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
    "PySide6/Qt6VirtualKeyboard.dll",
    "PySide6/Qt6Quick.dll",
    "PySide6/Qt6Qml.dll",
    "PySide6/Qt6QmlMeta.dll",
    "PySide6/Qt6QmlModels.dll",
    "PySide6/Qt6QmlWorkerScript.dll",
    "PySide6/Qt6OpenGL.dll",
    "PySide6/plugins/imageformats/qpdf.dll",
    "PySide6/Qt6Pdf.dll",
)
OMITTED_NAMES = frozenset(PurePosixPath(path).name.lower() for path in OMITTED)
BINARY_SUFFIXES = (".exe", ".dll", ".pyd")


def application_trees(dist: Path) -> list[Path]:
    return sorted(path for path in dist.iterdir() if (path / "_internal").is_dir())


def omit(tree: Path) -> list[Path]:
    """Delete the omitted files present in one application tree; return them."""

    removed = []
    for relative in OMITTED:
        target = tree / "_internal" / Path(*PurePosixPath(relative).parts)
        if target.is_file():
            target.unlink()
            removed.append(target)
    return removed


def imported_names(binary: Path) -> set[str]:
    import pefile  # type: ignore[import-untyped]

    image = pefile.PE(str(binary), fast_load=True)
    image.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    return {entry.dll.decode(errors="replace").lower() for entry in getattr(image, "DIRECTORY_ENTRY_IMPORT", ())}


def dangling_imports(tree: Path) -> list[tuple[Path, str]]:
    """Every remaining binary that still imports an omitted library."""

    found = []
    for binary in sorted(tree.rglob("*")):
        if binary.suffix.lower() in BINARY_SUFFIXES and binary.is_file():
            found += [(binary, name) for name in sorted(imported_names(binary) & OMITTED_NAMES)]
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args(argv)
    problems = []
    for tree in application_trees(args.dist):
        removed = omit(tree)
        print(f"[qt] {tree.name}: omitted {len(removed)} unused Qt files")
        problems += dangling_imports(tree)
        problems += [(path, "present") for path in tree.rglob("*") if path.name.lower() in OMITTED_NAMES]
    for binary, name in problems:
        print(f"ERROR: {binary} still needs or holds {name}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
