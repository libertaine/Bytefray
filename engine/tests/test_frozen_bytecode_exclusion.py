"""Coverage for Python bytecode exclusion from the frozen Windows payloads.

Phase F1 fixed the Agent API v2 scaffold omission and, in doing so, exposed a
second, independent packaging defect: its **first** remediation build bundled
five stale ``__pycache__/agent.cpython-311.pyc`` files out of
``engine/src/battle_engine/data/starter_agents/v4_*/`` into the frozen
payload. That build was made clean by deleting the caches and rebuilding by
hand, which fixed the artifact but not the build path -- release correctness
still depended on a human remembering to sweep an ignored-file class out of
the checkout first. Phase F's original executable never showed the problem
only because it was built from a clean ``git archive`` export rather than
from a working tree, and ``tools/build_win.ps1`` builds from the live
repository root.

The mechanism is ordinary and recurring rather than exotic: the engine
imports agent modules out of ``battle_engine/data`` at runtime, so CPython
writes ``__pycache__`` directories next to shipped product data as a normal
consequence of running the product, and the specs handed those directories to
PyInstaller as ``(directory, destination)`` tuples, which it expands by
collecting everything beneath them with no exclusion hook.

These tests pin the invariant that closes it:

    a checkout containing ignored bytecode -> a frozen payload containing none

They deliberately do not assert that any particular line of text appears in a
``.spec`` file. The unit tests exercise
``tools.packaging_data``'s real filtering function, the dirty-checkout test
plants genuine sentinel debris in the real collected trees and executes the
real spec files over it, and the payload test inspects an actual built
distribution when one is supplied.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

# engine/tests is not a package (no __init__.py), so pytest's default
# "prepend" import mode puts this directory on sys.path and the sibling
# module is importable by bare name. The spec-execution harness lives there
# because that module owns spec-file coverage; re-implementing it here would
# create a second copy of the fake-PyInstaller scaffolding to keep in step.
from test_windows_packaging_spec import ALL_SPECS, ROOT, _exec_spec_datas

from tools.packaging_data import collect_data_tree, is_python_bytecode

# --------------------------------------------------------------------------
# Filtering rule (unit)
# --------------------------------------------------------------------------

ALLOWED_PATHS = (
    "agent.yaml",
    "agent.py",
    "README.md",
    "data.json",
    "nested/config.yaml",
    "nested/deeper/manifest.yaml",
    # A .pyd is a native Windows extension module, not a bytecode cache.
    # setuptools' `*.py[cod]` shorthand sweeps it up, but excluding it from a
    # frozen payload would remove a real, loadable binary, so the rule here
    # is deliberately narrower than the wheel's.
    "extension.pyd",
    "pkg/native.pyd",
    # Bytecode is identified by path role, not by substring: a file merely
    # *named* like a cache is ordinary content.
    "pycache_notes.md",
    "__pycache__.txt",
    # Phase F3: explicit Windows-spelled (backslash) legitimate paths, tested
    # directly against an expected value -- not only checked for agreement
    # with their forward-slash sibling (see
    # test_filter_agrees_across_windows_and_posix_separators below), which
    # would pass just as easily if both spellings were wrong the same way.
    "pkg\\data.bin",
)

REJECTED_PATHS = (
    "__pycache__/agent.cpython-311.pyc",
    "nested/__pycache__/thing.cpython-314.pyc",
    "agent.pyc",
    "nested/agent.pyo",
    "deeply/nested/path/__pycache__/x.pyc",
    # A cache directory is excluded wholesale, whatever it happens to hold.
    "__pycache__/stray.txt",
    # Case-insensitive on the suffix, for a checkout that came through a
    # case-preserving copy or archive.
    "agent.PYC",
    # Phase F3: explicit Windows-spelled (backslash) rejected paths, tested
    # directly against an expected value for the same reason as the
    # ALLOWED_PATHS addition above. These specifically reproduce the Phase F3
    # regression: on a POSIX host, the pre-fix classifier built a
    # host-default ``pathlib.Path`` (``PurePosixPath`` behaviour there, which
    # does not split on ``\\``), so ``pkg\\__pycache__\\x.cpython-313.pyc``
    # was seen as one opaque filename component ending in ``.pyc`` -- still
    # correctly rejected only because the *suffix* check happened to also
    # match. ``pkg\\__pycache__\\readme.txt`` has no bytecode suffix, so only
    # the directory-component check can reject it, which is exactly the case
    # that silently passed as "allowed" before the fix.
    "pkg\\__pycache__\\x.cpython-313.pyc",
    "pkg\\__pycache__\\readme.txt",
    "pkg\\x.pyc",
    "pkg\\x.pyo",
)


@pytest.mark.parametrize("relative", ALLOWED_PATHS)
def test_legitimate_resources_are_not_treated_as_bytecode(relative: str) -> None:
    assert not is_python_bytecode(relative)


@pytest.mark.parametrize("relative", REJECTED_PATHS)
def test_bytecode_and_cache_paths_are_rejected(relative: str) -> None:
    assert is_python_bytecode(relative)


@pytest.mark.parametrize("relative", REJECTED_PATHS + ALLOWED_PATHS)
def test_filter_agrees_across_windows_and_posix_separators(relative: str) -> None:
    """The rule is path-aware, not string-substring, so both spellings agree.

    ``tools/build_win.ps1`` runs on Windows, where a collected relative path
    arrives with backslashes; the same repository is linted and tested on
    Linux. A filter written as ``"/__pycache__/" in text`` would silently
    stop excluding anything on Windows, shipping exactly the debris this
    module exists to prevent, so both spellings are asserted to agree.
    """

    assert is_python_bytecode(relative) == is_python_bytecode(relative.replace("/", "\\"))


def test_bytecode_rule_is_not_tied_to_one_interpreter_version() -> None:
    """A future CPython's tag must be excluded by the same unchanged rule.

    Pinning ``cpython-313`` (the interpreter this release builds with) would
    quietly stop filtering the moment the build moved to a later Python --
    a regression that reappears only at the next release, in an artifact.
    """

    for tag in ("cpython-38", "cpython-311", "cpython-313", "cpython-314", "cpython-450"):
        assert is_python_bytecode(f"__pycache__/module.{tag}.pyc")
        assert is_python_bytecode(f"module.{tag}.pyc")


# --------------------------------------------------------------------------
# collect_data_tree over a synthetic tree
# --------------------------------------------------------------------------


def _make_dirty_tree(root: Path) -> None:
    """A miniature product data tree carrying the debris a real checkout has."""

    (root / "agent_template_v2").mkdir(parents=True)
    (root / "agent_template_v2" / "agent.py").write_text("# template\n", encoding="utf-8")
    (root / "agent_template_v2" / "agent.yaml").write_text("name: t\n", encoding="utf-8")
    (root / "agent_template_v2" / "__pycache__").mkdir()
    (root / "agent_template_v2" / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"X")
    (root / "starters").mkdir()
    (root / "starters" / "hunter").mkdir()
    (root / "starters" / "hunter" / "agent.yaml").write_text("name: h\n", encoding="utf-8")
    (root / "starters" / "hunter" / "stale.pyc").write_bytes(b"X")
    (root / "starters" / "hunter" / "legacy.pyo").write_bytes(b"X")
    (root / "notes.md").write_text("# notes\n", encoding="utf-8")


def test_collect_data_tree_excludes_bytecode_and_keeps_neighbours(tmp_path: Path) -> None:
    """The invariant in miniature: dirty tree in, clean per-file entries out."""

    _make_dirty_tree(tmp_path)
    entries = collect_data_tree(tmp_path, "battle_engine/data")
    produced = {f"{destination}/{Path(source).name}" for source, destination in entries}

    assert produced == {
        "battle_engine/data/notes.md",
        "battle_engine/data/agent_template_v2/agent.py",
        "battle_engine/data/agent_template_v2/agent.yaml",
        "battle_engine/data/starters/hunter/agent.yaml",
    }
    assert not any(is_python_bytecode(Path(source).name) for source, _ in entries)


def test_collect_data_tree_sources_are_real_files_under_the_source_root(tmp_path: Path) -> None:
    _make_dirty_tree(tmp_path)
    for source, _destination in collect_data_tree(tmp_path, "dest"):
        assert Path(source).is_file()
        assert Path(source).is_relative_to(tmp_path)


def test_collect_data_tree_destinations_use_posix_separators(tmp_path: Path) -> None:
    """PyInstaller destinations are ``/``-separated even when built on Windows."""

    _make_dirty_tree(tmp_path)
    for _source, destination in collect_data_tree(tmp_path, "dest"):
        assert "\\" not in destination


def test_collect_data_tree_places_root_files_at_the_destination_root(tmp_path: Path) -> None:
    (tmp_path / "icon.png").write_bytes(b"P")
    assert collect_data_tree(tmp_path, "assets/branding") == [
        (str(tmp_path / "icon.png"), "assets/branding")
    ]


def test_optional_missing_directory_is_skipped(tmp_path: Path) -> None:
    """Absent optional trees keep their prior "skip quietly" behaviour.

    ``assets/`` and the branding directory are not guaranteed in every
    checkout, and the pre-F2 specs guarded them with ``os.path.isdir``;
    turning that into a hard failure would break builds F2 has no business
    changing.
    """

    assert collect_data_tree(tmp_path / "absent", "assets") == []


def test_required_missing_directory_fails_the_build_loudly(tmp_path: Path) -> None:
    """Phase F1's fail-loud contract for required resources is preserved."""

    with pytest.raises(SystemExit, match="is missing"):
        collect_data_tree(tmp_path / "absent", "battle_engine/data/x", required=True)


def test_required_directory_holding_only_bytecode_fails_the_build(tmp_path: Path) -> None:
    """Filtering must not turn a broken resource into a silently empty one.

    This is the failure mode per-file collection newly makes possible: a
    required template directory that exists but contributes nothing after
    filtering would package as "present but empty", reproducing the exact
    user-visible Phase F1 defect (a frozen ``agents create`` that cannot find
    its template) while every directory-existence check still passed.
    """

    cache = tmp_path / "agent_template_v2" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "agent.cpython-313.pyc").write_bytes(b"X")
    with pytest.raises(SystemExit, match="no packageable files"):
        collect_data_tree(
            tmp_path / "agent_template_v2", "battle_engine/data/agent_template_v2", required=True
        )


# --------------------------------------------------------------------------
# Synthetic dirty checkout, real spec files
# --------------------------------------------------------------------------

# Trees the shipped specs collect, chosen to cover every distinct collection
# path: the scaffold templates Phase F1 fixed, the starter agents whose stale
# caches Phase F1 actually leaked, and both branding/asset roots.
DIRTY_CHECKOUT_TARGETS = (
    Path("engine/src/battle_engine/data/starter_agents/hunter"),
    Path("engine/src/battle_engine/data/agent_template_v2"),
    Path("engine/src/battle_engine/data/agent_template_v2_annotated"),
    Path("app/assets/branding"),
    Path("assets/branding"),
)


@pytest.fixture
def dirty_checkout() -> Iterator[list[Path]]:
    """Plant ignored bytecode debris in the real collected trees, then remove it.

    Deliberately mutates the working checkout rather than a copy, because the
    defect is a property of building *from a checkout*: the specs resolve
    their sources from the repository root, so a temporary directory would
    exercise a path no release build takes. Every planted file is ignored by
    ``.gitignore`` (``__pycache__/``, ``*.py[cod]``, ``*.pyo``), carries a
    unique name that cannot collide with real bytecode, and is removed in
    teardown along with any directory this fixture created.
    """

    token = uuid.uuid4().hex[:8]
    planted: list[Path] = []
    created_dirs: list[Path] = []
    for relative in DIRTY_CHECKOUT_TARGETS:
        directory = ROOT / relative
        if not directory.is_dir():
            continue
        cache = directory / "__pycache__"
        if not cache.exists():
            cache.mkdir()
            created_dirs.append(cache)
        for candidate in (
            cache / f"dirty_{token}.cpython-313.pyc",
            directory / f"dirty_{token}.pyc",
            directory / f"dirty_{token}.pyo",
        ):
            candidate.write_bytes(b"NOT-REAL-BYTECODE")
            planted.append(candidate)
    assert planted, "no collected tree was available to make dirty"
    try:
        yield planted
    finally:
        for candidate in planted:
            candidate.unlink(missing_ok=True)
        for directory in created_dirs:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()


@pytest.mark.parametrize("spec_path", ALL_SPECS, ids=lambda path: path.stem)
def test_dirty_checkout_produces_a_clean_data_list(
    spec_path: Path, dirty_checkout: list[Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The core Phase F2 invariant, exercised against the real spec files.

    Every shipped spec is covered, not only the two that bundle scaffold
    templates: ``bytefray-cli`` collects the same starter-agent tree whose
    stale caches Phase F1 leaked, and the replay viewer collects ``assets/``.
    """

    datas = _exec_spec_datas(spec_path, monkeypatch)
    planted_names = {path.name for path in dirty_checkout}

    leaked = [source for source, _ in datas if Path(source).name in planted_names]
    assert not leaked, f"{spec_path.name} collected planted bytecode sentinels: {leaked}"

    bytecode = [
        (source, destination)
        for source, destination in datas
        if is_python_bytecode(source) or is_python_bytecode(destination)
    ]
    assert not bytecode, f"{spec_path.name} collected Python bytecode: {bytecode}"


def test_dirty_checkout_still_packages_the_neighbouring_resources(
    dirty_checkout: list[Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filtering must remove the debris and nothing standing next to it.

    Asserted from the same deliberately dirty state as the test above, so a
    filter that over-matched -- dropping a whole directory that contained a
    cache, say -- fails here rather than passing as "clean".
    """

    datas = _exec_spec_datas(ROOT / "tools" / "bytefray.spec", monkeypatch)
    produced = {f"{destination}/{Path(source).name}" for source, destination in datas}

    required = {
        "battle_engine/data/agent_template/agent.py",
        "battle_engine/data/agent_template/agent.yaml",
        "battle_engine/data/agent_template_annotated/agent.py",
        "battle_engine/data/agent_template_annotated/agent.yaml",
        "battle_engine/data/agent_template_v2/agent.py",
        "battle_engine/data/agent_template_v2/agent.yaml",
        "battle_engine/data/agent_template_v2_annotated/agent.py",
        "battle_engine/data/agent_template_v2_annotated/agent.yaml",
        "battle_engine/data/starter_agents/hunter/agent.yaml",
        "assets/branding/bytefray-icon.png",
    }
    assert required <= produced, (
        f"filtering removed legitimate resources: {sorted(required - produced)}"
    )


# --------------------------------------------------------------------------
# Built artifact
# --------------------------------------------------------------------------

FROZEN_DIST_ENV_VAR = "BYTEFRAY_FROZEN_EXE"


def _frozen_distribution() -> Path:
    """The onedir distribution tree to inspect, or skip if none was supplied.

    Shares ``BYTEFRAY_FROZEN_EXE`` with
    ``engine/tests/test_frozen_scaffold_resources.py`` so a single release
    build satisfies both artifact-level gates. The executable's own directory
    is the PyInstaller onedir root (``dist/windows/bytefray/bytefray.exe``),
    so the whole distribution -- ``_internal`` included -- is walked from
    there; no archive parsing is needed because a onedir build keeps its
    collected data as loose files.
    """

    configured = os.environ.get(FROZEN_DIST_ENV_VAR, "").strip()
    if not configured:
        pytest.skip(f"set {FROZEN_DIST_ENV_VAR} to a built executable to inspect its payload")
    executable = Path(configured).expanduser()
    if not executable.is_file():
        pytest.fail(f"{FROZEN_DIST_ENV_VAR}={configured!r} is not an existing file")
    return executable.resolve().parent


def test_frozen_payload_contains_no_python_bytecode() -> None:
    """Artifact-level proof, which no source-level check can substitute for.

    Phase F1's leak was found by inspecting a built payload after every
    source-level test passed, so the final gate deliberately reads the
    distribution rather than the inputs that produced it.
    """

    distribution = _frozen_distribution()
    offenders = sorted(
        str(path.relative_to(distribution))
        for path in distribution.rglob("*")
        if path.is_file() and is_python_bytecode(path.relative_to(distribution))
    )
    caches = sorted(
        str(path.relative_to(distribution))
        for path in distribution.rglob("__pycache__")
        if path.is_dir()
    )
    assert not caches, f"frozen payload contains __pycache__ directories: {caches}"
    assert not offenders, f"frozen payload contains Python bytecode: {offenders}"
