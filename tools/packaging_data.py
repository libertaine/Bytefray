"""Canonical, bytecode-filtered data collection for the shipped ``.spec`` files.

Every Windows PyInstaller spec in ``tools/`` bundles part of the repository's
own resource tree -- scaffold templates, starter agents, branding/assets --
and each used to do it by appending a ``(source_directory, destination)``
tuple to ``datas``. PyInstaller expands such a tuple by walking the directory
and collecting **everything** under it, with no exclusion hook, so a release
build run from a live developer checkout packaged whatever ignored debris
that tree happened to contain.

That is not hypothetical. ``tools/build_win.ps1`` builds from the live
repository root, and the engine imports agent modules out of
``battle_engine/data`` at runtime (``starter_agents/<name>/agent.py``), so
CPython writes ``__pycache__/agent.cpython-*.pyc`` next to shipped product
data as a normal consequence of running the product. Phase F1's first
remediation build bundled five such stale ``.pyc`` files from
``starter_agents/v4_*/`` into the frozen payload; that build was rebuilt by
hand after deleting the caches, which made the artifact clean but left the
build path unsafe -- correctness depended on a human remembering to sweep the
checkout first. Phase F's original executable never exposed it only because
that build came from a clean ``git archive`` export rather than a working
tree.

The wheel and sdist never had this problem: ``pyproject.toml``'s
``[tool.setuptools.exclude-package-data]`` and ``MANIFEST.in``'s
``global-exclude *.py[cod]`` both filter bytecode at the packaging boundary.
:func:`collect_data_tree` gives the frozen builds the same property, and gives
it *by construction*: the specs expand their own directories here and hand
PyInstaller per-file entries, so a bytecode file is never offered for
collection in the first place rather than being cleaned up afterwards.

Deliberately **not** excluded: ``.pyd``. Despite matching setuptools'
``*.py[cod]`` shorthand, a ``.pyd`` is a native Windows extension module --
compiled C, not CPython bytecode cache -- and stripping it would break the
frozen application. The exclusion set here is exactly ``__pycache__``
directories, ``*.pyc`` and ``*.pyo``.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

__all__ = ["BYTECODE_SUFFIXES", "CACHE_DIRECTORY_NAME", "collect_data_tree", "is_python_bytecode"]

#: Directory name CPython writes cached bytecode into.
CACHE_DIRECTORY_NAME = "__pycache__"

#: File suffixes treated as Python bytecode. Matched case-insensitively and
#: without reference to any interpreter version tag, so ``module.cpython-311.pyc``
#: and ``module.cpython-314.pyc`` are both excluded by the same rule and no
#: edit is needed when the build interpreter moves to a later Python.
BYTECODE_SUFFIXES = frozenset({".pyc", ".pyo"})


def is_python_bytecode(relative_path: str | Path) -> bool:
    """Return whether ``relative_path`` names Python bytecode or a cache entry.

    The rule holds for both ``nested/__pycache__/x.pyc`` and Windows'
    ``nested\\__pycache__\\x.pyc`` **regardless of the host platform this
    function runs on** -- not merely regardless of which style the path
    happens to use. A path is rejected when **any** component is a
    ``__pycache__`` directory (catching the whole cache subtree regardless of
    what it contains) or when the final component's suffix is one of
    :data:`BYTECODE_SUFFIXES` (catching loose ``.pyc``/``.pyo`` files dropped
    outside a cache directory, which ``-B``/legacy layouts and stray copies
    both produce).

    Component-splitting deliberately does **not** use the host's default
    :class:`pathlib.Path`: that resolves to ``PurePosixPath`` behaviour on a
    POSIX host, which does not treat ``\\`` as a separator, so a
    Windows-spelled path would be seen as one opaque filename component
    instead of a ``__pycache__`` directory plus a file -- silently defeating
    this exact check on the one platform (Linux) that lints and tests this
    repository, even though the paths it must classify come from a Windows
    release build. Both separators are normalized to ``/`` first and the
    result is always parsed with :class:`~pathlib.PurePosixPath`, so the
    answer no longer depends on which OS is running the classifier.
    """

    normalized = str(relative_path).replace("\\", "/")
    path = PurePosixPath(normalized)
    if any(part.lower() == CACHE_DIRECTORY_NAME for part in path.parts):
        return True
    return path.suffix.lower() in BYTECODE_SUFFIXES


def collect_data_tree(
    source_dir: str | Path,
    destination: str,
    *,
    required: bool = False,
) -> list[tuple[str, str]]:
    """Expand one directory into bytecode-free PyInstaller ``datas`` entries.

    Returns ``(absolute_source_file, destination_directory)`` tuples -- the
    per-file form of a ``datas`` entry -- with every :func:`is_python_bytecode`
    path omitted. Destinations use ``/`` separators, matching both PyInstaller's
    convention and the literal destinations these specs already used.

    ``required`` preserves and extends the fail-loud behaviour Phase F1
    introduced after three separate scaffold-template omissions reached shipped
    executables (each producing an application whose ``agents create`` failed
    with "Agent template resource directory not found" while source checkouts
    and wheels worked). A required tree that is missing raises, and so does one
    that exists but yields no packageable files -- an empty or bytecode-only
    template directory is the same silent defect as an absent one, and would
    otherwise pass unnoticed now that collection is per-file. Optional trees
    (branding, assets, starter agents) keep their prior "skip if absent"
    behaviour so non-Windows and partial checkouts build unchanged.
    """

    source = Path(source_dir)
    if not source.is_dir():
        if required:
            raise SystemExit(
                f"Required packaging resource directory {str(source)!r} is missing; "
                "the frozen build would ship without it."
            )
        return []

    base = PurePosixPath(destination)
    entries: list[tuple[str, str]] = []
    for candidate in sorted(source.rglob("*")):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(source)
        if is_python_bytecode(relative):
            continue
        entries.append((str(candidate), str(base / PurePosixPath(*relative.parts[:-1]))))

    if required and not entries:
        raise SystemExit(
            f"Required packaging resource directory {str(source)!r} contains no "
            "packageable files; the frozen build would ship an empty resource."
        )
    return entries
