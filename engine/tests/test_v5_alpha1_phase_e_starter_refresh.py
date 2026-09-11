"""V5 Alpha 1 Phase E0 -- existing-install starter refresh.

Before Phase E, ``ensure_starter_agents`` copied a bundled starter file only
when the catalog did not already have it. That protected user edits, but it
also meant an installation created before a bundled starter changed *never*
received the newer version: the Phase C ``v5_*`` starters installed at version
1.0.0 carried no ``parameters`` section, so Phase D's parameter schemas -- and
therefore Phase E's whole Designer parameter UX -- were invisible on every
upgraded installation, permanently.

Phase E resolves that without weakening the protection, by deciding per
starter whether the installed copy is provably an untouched copy of a bundled
release (:data:`~battle_engine.starters.SUPERSEDED_STARTER_DIGESTS`) and
refreshing only those. Absence from that allowlist is the safe answer, so
anything a user has edited -- and every starter whose history predates the
allowlist -- is preserved exactly as before.

These tests use temporary data roots exclusively and never touch the
developer's real ``BYTEFRAY_ROOT``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from battle_engine import starters
from battle_engine.agents import discover_agents
from battle_engine.starters import (
    CURRENT_STARTER_DIGESTS,
    STARTER_AGENT_NAMES,
    SUPERSEDED_STARTER_DIGESTS,
    describe_starter_refresh,
    ensure_starter_agents,
    starter_content_digest,
    starter_content_files,
)

V5_STARTERS = ("v5_region_attacker", "v5_scout_striker", "v5_core_defender", "v5_dual_team")
V4_STARTERS = (
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_defender_scout",
    "v4_local_defender",
    "v4_scout",
    "v4_quorum",
)
PHASE_C_COMMIT = "69fc958"

#: Committed byte-for-byte copy of what V5 Alpha 1 Phase C (commit
#: ``69fc958``) actually bundled for each V5 starter -- see
#: :data:`~battle_engine.starters.SUPERSEDED_STARTER_DIGESTS`'s comment for
#: that commit reference. Fixed as ordinary committed test data (Phase F3),
#: not read out of Git history at test time: a historical commit is not
#: guaranteed reachable from every checkout that runs this suite (a shallow
#: CI clone, a `git archive` export, an sdist-built source tree), so a test
#: whose correctness depended on `git ls-tree`/`git cat-file` against a fixed
#: SHA would fail in exactly those environments regardless of product
#: correctness. Each fixture's digest is asserted against the pinned
#: allowlist below (`test_phase_c_starter_digests_are_the_recorded_superseded_ones`),
#: so this file is proven -- not merely trusted -- to still be that release's
#: actual bytes.
_PHASE_C_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "phase_c_v5_starters"


def _resource_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _bundled_dir(name: str) -> Path:
    return (
        _resource_root()
        / "engine"
        / "src"
        / "battle_engine"
        / "data"
        / "starter_agents"
        / name
    )


def _seed_phase_c_starter(agents_dir: Path, name: str) -> Path:
    """Reproduce one starter exactly as V5 Alpha 1 Phase C bundled it.

    Copied from the committed fixture in ``_PHASE_C_FIXTURE_ROOT`` rather than
    read out of Git history, so "an untouched 1.0.0 install" means the bytes
    that release actually shipped -- the thing the refresh policy claims to
    recognize -- without requiring the historical commit to be reachable from
    the checkout running this test.
    """

    source_dir = _PHASE_C_FIXTURE_ROOT / name
    assert source_dir.is_dir(), f"missing Phase C fixture for {name}: {source_dir}"

    agent_dir = agents_dir / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.iterdir()):
        shutil.copy2(source, agent_dir / source.name)
    return agent_dir


def _manifest(agent_dir: Path) -> dict:
    return json.loads((agent_dir / "agent.yaml").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The digest itself
# ---------------------------------------------------------------------------


def test_digest_ignores_line_endings_but_not_content(tmp_path: Path) -> None:
    """The property the whole policy rests on.

    This repository stores ``.py`` with LF and checks it out with CRLF on
    Windows (``core.autocrlf=true``), so one bundled release genuinely has
    different bytes on different platforms. A Windows installation could never
    be recognized as pristine if the fingerprint were byte-exact.
    """

    lf, crlf, edited = tmp_path / "lf", tmp_path / "crlf", tmp_path / "edited"
    for directory in (lf, crlf, edited):
        directory.mkdir()
    lf.joinpath("agent.py").write_bytes(b"a = 1\nb = 2\n")
    crlf.joinpath("agent.py").write_bytes(b"a = 1\r\nb = 2\r\n")
    edited.joinpath("agent.py").write_bytes(b"a = 1\nb = 3\n")

    assert starter_content_digest(lf) == starter_content_digest(crlf)
    assert starter_content_digest(lf) != starter_content_digest(edited)


def test_digest_covers_the_manifest_not_only_the_implementation(tmp_path: Path) -> None:
    """Phase D changed ``agent.yaml``, so a ``.py``-only fingerprint (what
    ``agent_api.local_source_fingerprint`` computes) could not have detected
    the very upgrade this policy exists to perform."""

    first, second = tmp_path / "first", tmp_path / "second"
    for directory in (first, second):
        directory.mkdir()
        directory.joinpath("agent.py").write_text("x = 1\n", encoding="utf-8")
    first.joinpath("agent.yaml").write_text('{"name": "a"}', encoding="utf-8")
    second.joinpath("agent.yaml").write_text('{"name": "a", "version": "2"}', encoding="utf-8")

    assert starter_content_digest(first) != starter_content_digest(second)


def test_digest_ignores_bytecode_written_by_running_the_agent(tmp_path: Path) -> None:
    """Importing a starter writes ``__pycache__`` into whatever tree it lives
    in. Counting it would make a starter look modified merely because it ran,
    and would install stale bytecode into a user's catalog."""

    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    agent_dir.joinpath("agent.py").write_text("x = 1\n", encoding="utf-8")
    before = starter_content_digest(agent_dir)

    cache = agent_dir / "__pycache__"
    cache.mkdir()
    cache.joinpath("agent.cpython-311.pyc").write_bytes(b"\x00compiled")

    assert starter_content_digest(agent_dir) == before
    assert all("__pycache__" not in p.parts for p in starter_content_files(agent_dir))


def test_digest_ignores_loose_bytecode_and_case_variant_cache_dirs(tmp_path: Path) -> None:
    """FIND-04 (V5 Alpha 1 Post-Release Hardening Audit): a loose ``.pyc``/
    ``.pyo`` dropped directly in a starter's root, or a case-variant
    ``__pycache__`` directory name, must not affect the digest either --
    the original filter only rejected the exact-case directory component,
    letting either variant corrupt the digest and falsely classify an
    untouched starter as user-customized."""

    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    agent_dir.joinpath("agent.py").write_text("x = 1\n", encoding="utf-8")
    before = starter_content_digest(agent_dir)

    agent_dir.joinpath("stale.pyc").write_bytes(b"\x00compiled")
    agent_dir.joinpath("legacy.PYO").write_bytes(b"\x00compiled")
    case_variant_cache = agent_dir / "__PyCache__"
    case_variant_cache.mkdir()
    case_variant_cache.joinpath("agent.cpython-311.pyc").write_bytes(b"\x00compiled")

    assert starter_content_digest(agent_dir) == before
    files = starter_content_files(agent_dir)
    assert all(path.suffix.lower() not in (".pyc", ".pyo") for path in files)
    assert all("__pycache__" not in {part.lower() for part in path.parts} for path in files)


def test_absent_or_empty_directory_has_no_digest(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    assert starter_content_digest(tmp_path / "missing") is None
    assert starter_content_digest(empty) is None


# ---------------------------------------------------------------------------
# The pinned-digest maintenance gate
# ---------------------------------------------------------------------------


def test_current_bundled_content_matches_its_pinned_digest() -> None:
    """Changing a bundled starter must be deliberate and must carry its
    predecessor into the upgrade allowlist -- otherwise every existing
    pristine installation is silently reclassified as "customized" and frozen
    on the old version forever."""

    for name in STARTER_AGENT_NAMES:
        actual = starter_content_digest(_bundled_dir(name))
        expected = CURRENT_STARTER_DIGESTS.get(name)
        assert actual == expected, (
            f"Bundled starter {name!r} content changed.\n"
            f"  was pinned: {expected}\n"
            f"  now:        {actual}\n"
            f"Append the OLD digest to SUPERSEDED_STARTER_DIGESTS[{name!r}] so "
            f"existing pristine installs upgrade, then update "
            f"CURRENT_STARTER_DIGESTS."
        )


def test_pinned_digests_cover_every_starter_exactly() -> None:
    assert set(CURRENT_STARTER_DIGESTS) == set(STARTER_AGENT_NAMES)


def test_no_superseded_digest_is_also_a_current_one() -> None:
    """A digest cannot mean both "this is current" and "upgrade this"."""

    for name, digests in SUPERSEDED_STARTER_DIGESTS.items():
        assert name in STARTER_AGENT_NAMES
        assert CURRENT_STARTER_DIGESTS[name] not in digests
        assert len(set(digests)) == len(digests)


def test_phase_c_starter_digests_are_the_recorded_superseded_ones(tmp_path: Path) -> None:
    """The allowlist entries really are the Phase C release's content, checked
    against the committed Phase C fixture rather than against themselves."""

    for name in V5_STARTERS:
        agent_dir = _seed_phase_c_starter(tmp_path, name)
        assert _manifest(agent_dir)["version"] == "1.0.0"
        assert "parameters" not in _manifest(agent_dir)
        assert starter_content_digest(agent_dir) in SUPERSEDED_STARTER_DIGESTS[name]


# ---------------------------------------------------------------------------
# The four refresh outcomes
# ---------------------------------------------------------------------------


def test_missing_starter_installs_the_current_bundled_version(tmp_path: Path) -> None:
    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert result.errors == ()
    assert result.refreshed == ()
    assert result.customized == ()
    for name in STARTER_AGENT_NAMES:
        installed = tmp_path / "agents" / name
        assert starter_content_digest(installed) == CURRENT_STARTER_DIGESTS[name]


def test_untouched_phase_c_starter_is_upgraded_to_the_current_version(
    tmp_path: Path,
) -> None:
    """Case B, and the central Phase E0 outcome: a pristine 1.0.0 install
    receives the Phase D manifest, so the Designer can discover its
    parameters."""

    agents_dir = tmp_path / "agents"
    for name in V5_STARTERS:
        _seed_phase_c_starter(agents_dir, name)

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert {entry.name for entry in result.refreshed} == set(V5_STARTERS)
    assert result.customized == ()
    for name in V5_STARTERS:
        installed = agents_dir / name
        assert starter_content_digest(installed) == CURRENT_STARTER_DIGESTS[name]
        manifest = _manifest(installed)
        assert manifest["version"] == "1.1.0"
        assert manifest["parameters"], f"{name} did not gain its parameter schema"


def test_starter_already_at_the_current_version_is_a_no_op(tmp_path: Path) -> None:
    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    stamps = {
        path: path.stat().st_mtime_ns
        for name in STARTER_AGENT_NAMES
        for path in starter_content_files(tmp_path / "agents" / name)
    }

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert result.installed == ()
    assert result.refreshed == ()
    assert result.customized == ()
    assert {path: path.stat().st_mtime_ns for path in stamps} == stamps


def test_user_modified_old_starter_is_preserved_not_overwritten(tmp_path: Path) -> None:
    """Case D. The edit survives, the bundled version is *not* forced in, and
    the user is told why -- the alternative (overwriting because ours is
    newer) would destroy work."""

    agents_dir = tmp_path / "agents"
    edited = _seed_phase_c_starter(agents_dir, "v5_region_attacker") / "agent.py"
    edited.write_text(
        edited.read_text(encoding="utf-8") + "\n# my own notes\n", encoding="utf-8"
    )
    mine = edited.read_text(encoding="utf-8")

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert edited.read_text(encoding="utf-8") == mine
    assert _manifest(agents_dir / "v5_region_attacker")["version"] == "1.0.0"
    assert {entry.name for entry in result.customized} == {"v5_region_attacker"}
    assert "v5_region_attacker" not in {entry.name for entry in result.refreshed}


def test_customized_starter_still_has_missing_files_restored(tmp_path: Path) -> None:
    """The pre-Phase-E contract for a modified starter, kept verbatim:
    restoring a file the catalog does not have overwrites nothing, and a
    starter missing its implementation is simply broken."""

    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, "v5_dual_team")
    manifest = agent_dir / "agent.yaml"
    manifest.write_text(
        json.dumps({**_manifest(agent_dir), "display": "My Dual Team"}), encoding="utf-8"
    )
    (agent_dir / "agent.py").unlink()

    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert (agent_dir / "agent.py").is_file()
    assert _manifest(agent_dir)["display"] == "My Dual Team"


def test_a_starter_the_user_wrote_from_scratch_is_never_refreshed(tmp_path: Path) -> None:
    """Content that was never a bundled release is not in the allowlist, so it
    can only ever be preserved -- the fail-safe direction."""

    agents_dir = tmp_path / "agents"
    agent_dir = agents_dir / "v5_core_defender"
    agent_dir.mkdir(parents=True)
    agent_dir.joinpath("agent.yaml").write_text(
        json.dumps({"name": "v5_core_defender", "api_version": 2, "version": "9.9.9"}),
        encoding="utf-8",
    )
    agent_dir.joinpath("agent.py").write_text("# entirely mine\n", encoding="utf-8")

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert _manifest(agent_dir)["version"] == "9.9.9"
    assert "v5_core_defender" in {entry.name for entry in result.customized}


# ---------------------------------------------------------------------------
# Idempotence, scope and reporting
# ---------------------------------------------------------------------------


def test_refresh_is_idempotent(tmp_path: Path) -> None:
    agents_dir = tmp_path / "agents"
    for name in V5_STARTERS:
        _seed_phase_c_starter(agents_dir, name)
    edited = _seed_phase_c_starter(agents_dir, "v5_core_defender") / "agent.py"
    edited.write_text("# mine\n" + edited.read_text(encoding="utf-8"), encoding="utf-8")

    first = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    stamps = {
        path: path.stat().st_mtime_ns
        for name in STARTER_AGENT_NAMES
        for path in starter_content_files(agents_dir / name)
    }
    second = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert len(first.refreshed) == 3
    assert second.installed == ()
    assert second.refreshed == ()
    # A customized starter stays reported every run: it is a standing
    # condition, not a one-time event.
    assert {entry.name for entry in second.customized} == {"v5_core_defender"}
    assert {path: path.stat().st_mtime_ns for path in stamps} == stamps


def test_v4_historical_starters_are_never_rewritten(tmp_path: Path) -> None:
    """The ``v4_*`` starters carry research and replay identity. Nothing in the
    refresh policy may touch them -- neither an edited copy nor an untouched
    one, since their bundled content has not changed at all."""

    agents_dir = tmp_path / "agents"
    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    for name in V4_STARTERS:
        source = agents_dir / name / "agent.py"
        source.write_text(source.read_text(encoding="utf-8") + "\n# mine\n", encoding="utf-8")
    edited = {
        name: (agents_dir / name / "agent.py").read_text(encoding="utf-8")
        for name in V4_STARTERS
    }

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert {entry.name for entry in result.refreshed} == set()
    for name in V4_STARTERS:
        assert (agents_dir / name / "agent.py").read_text(encoding="utf-8") == edited[name]


def test_bytecode_in_the_resource_tree_is_never_installed(tmp_path: Path) -> None:
    """A source checkout accumulates ``__pycache__`` under the bundled starter
    tree whenever a starter runs; ``pyproject.toml`` already excludes it from
    the wheel, and the runtime copy must agree or a dev-run install and a
    wheel install of one release would differ."""

    resources = tmp_path / "resources"
    base = resources / "battle_engine" / "data" / "starter_agents"
    for name in STARTER_AGENT_NAMES:
        agent_dir = base / name
        agent_dir.mkdir(parents=True)
        agent_dir.joinpath("agent.yaml").write_text(json.dumps({"name": name}), encoding="utf-8")
        cache = agent_dir / "__pycache__"
        cache.mkdir()
        cache.joinpath("agent.cpython-311.pyc").write_bytes(b"\x00stale")

    data_root = tmp_path / "data"
    result = ensure_starter_agents(resource_root=resources, data_root=data_root)

    assert result.errors == ()
    assert not any("__pycache__" in path.parts for path in result.installed)
    assert not (data_root / "agents" / "runner" / "__pycache__").exists()


def test_refresh_summary_names_what_changed_and_what_was_kept(tmp_path: Path) -> None:
    agents_dir = tmp_path / "agents"
    _seed_phase_c_starter(agents_dir, "v5_dual_team")
    edited = _seed_phase_c_starter(agents_dir, "v5_scout_striker") / "agent.py"
    edited.write_text("# mine\n" + edited.read_text(encoding="utf-8"), encoding="utf-8")

    summary = describe_starter_refresh(
        ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    )

    assert summary is not None
    assert "v5_dual_team" in summary
    assert "v5_scout_striker" in summary
    assert "delete" in summary.lower()


def test_refresh_summary_is_silent_when_nothing_happened(tmp_path: Path) -> None:
    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert describe_starter_refresh(result) is None


# ---------------------------------------------------------------------------
# The upgraded installation, end to end
# ---------------------------------------------------------------------------


def test_upgraded_install_exposes_the_phase_d_parameter_schema(tmp_path: Path) -> None:
    """The reason E0 exists: after refresh, the discovery layer the Agent
    Designer reads reports the parameters and presets a Phase C install could
    never have shown."""

    agents_dir = tmp_path / "agents"
    for name in V5_STARTERS:
        _seed_phase_c_starter(agents_dir, name)

    before = discover_agents(tmp_path)
    assert all(before[name].parameter_schema.is_empty for name in V5_STARTERS)

    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)
    after = discover_agents(tmp_path)

    assert after["v5_region_attacker"].parameter_schema.declaration_order() == (
        "attacker_reach",
    )
    assert "far_sighted" in after["v5_region_attacker"].parameter_schema.preset_names()
    for name in V5_STARTERS:
        assert not after[name].parameter_schema.is_empty


@pytest.mark.parametrize("name", V5_STARTERS)
def test_refreshed_starter_is_byte_identical_to_the_bundled_one(
    tmp_path: Path, name: str
) -> None:
    """Refresh mirrors the bundled starter rather than merging into it, so an
    upgraded install and a fresh one are the same agent -- including any file
    a newer release removed."""

    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, name)
    agent_dir.joinpath("stale_helper.py").write_text("# from an older release\n", encoding="utf-8")
    # The extra file makes this no longer a recognized pristine copy, so it is
    # preserved; the point of the check below is the recognized case.
    assert ensure_starter_agents(
        resource_root=_resource_root(), data_root=tmp_path
    ).refreshed == ()
    agent_dir.joinpath("stale_helper.py").unlink()

    ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    bundled = _bundled_dir(name)
    installed_names = {p.relative_to(agent_dir).as_posix() for p in starter_content_files(agent_dir)}
    bundled_names = {p.relative_to(bundled).as_posix() for p in starter_content_files(bundled)}
    assert installed_names == bundled_names
    assert starter_content_digest(agent_dir) == starter_content_digest(bundled)


# ---------------------------------------------------------------------------
# FIND-03 (V5 Alpha 1 Post-Release Hardening Audit) -- interrupted-refresh
# recovery, re-opened and resolved in V5 Alpha 1 Maintenance Phase 3.
#
# The audit's own suggested fix (stage a replacement directory, atomically
# rename/replace it into place) was deferred in Phase 2 because no directory
# -level atomic replace exists on both Windows and POSIX for a non-empty
# destination. The fix implemented here instead makes the *interrupted
# state* recoverable via a small marker file (a single-file atomic rename,
# a primitive both platforms already guarantee) that lets
# ``ensure_starter_agents`` resume ``_mirror_bundled`` -- which is already
# idempotent -- instead of the resulting hybrid digest being classified as a
# user edit. These tests simulate interruption deterministically (a targeted
# monkeypatch failure, or a hand-built hybrid state) rather than depending on
# real process-kill timing, per the phase's explicit testability requirement.
# ---------------------------------------------------------------------------


def test_write_failure_mid_mirror_records_a_marker_and_resumes_on_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real interruption (crash, kill, disk error, power loss) partway
    through ``_mirror_bundled`` must not permanently trap the starter as
    ``CUSTOMIZED``. Simulated here by making exactly one file's write fail on
    its first attempt -- deterministic, not timing-dependent."""

    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, "v5_region_attacker")
    original_manifest_bytes = agent_dir.joinpath("agent.yaml").read_bytes()

    real_write_bytes = Path.write_bytes
    already_failed = False

    def flaky_write_bytes(self: Path, data: bytes) -> int:
        nonlocal already_failed
        # "agent.py" sorts before "agent.yaml" (starter_content_files orders
        # deterministically), so by the time this fires, agent.py has
        # already been rewritten to the new bundled bytes -- the exact
        # hybrid state FIND-03 describes.
        if not already_failed and self.parent == agent_dir and self.name == "agent.yaml":
            already_failed = True
            raise OSError("simulated interruption mid-mirror")
        return real_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", flaky_write_bytes)

    with pytest.raises(OSError, match="simulated interruption"):
        ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    marker = starters._refresh_marker_path(tmp_path, "v5_region_attacker")
    assert marker.is_file(), "the marker must survive the interruption for recovery to work"
    assert agent_dir.joinpath("agent.yaml").read_bytes() == original_manifest_bytes
    hybrid_digest = starter_content_digest(agent_dir)
    assert hybrid_digest not in SUPERSEDED_STARTER_DIGESTS["v5_region_attacker"]
    assert hybrid_digest != CURRENT_STARTER_DIGESTS["v5_region_attacker"]

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert {entry.name for entry in result.refreshed} == {"v5_region_attacker"}
    assert result.customized == ()
    assert not marker.exists(), "the marker must be cleared once the resumed mirror completes"
    assert starter_content_digest(agent_dir) == CURRENT_STARTER_DIGESTS["v5_region_attacker"]
    manifest = _manifest(agent_dir)
    assert manifest["version"] == "1.1.0"
    assert manifest["parameters"]


def test_interruption_before_any_file_write_still_resumes_cleanly(tmp_path: Path) -> None:
    """The marker is written before ``_mirror_bundled`` touches anything, so
    an interruption in that gap (killed after the marker write, before the
    first file write) must resume exactly like any other interruption."""

    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, "v5_dual_team")
    pristine_bytes = {
        path.name: path.read_bytes() for path in starter_content_files(agent_dir)
    }
    bundled_digest = starter_content_digest(_bundled_dir("v5_dual_team"))
    assert bundled_digest is not None

    starters._write_refresh_marker(tmp_path, "v5_dual_team", target_digest=bundled_digest)
    marker = starters._refresh_marker_path(tmp_path, "v5_dual_team")
    assert marker.is_file()
    # Nothing has actually changed on disk yet -- the true "before the first
    # write" interruption point.
    assert {p.name: p.read_bytes() for p in starter_content_files(agent_dir)} == pristine_bytes

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    assert {entry.name for entry in result.refreshed} == {"v5_dual_team"}
    assert not marker.exists()
    assert starter_content_digest(agent_dir) == CURRENT_STARTER_DIGESTS["v5_dual_team"]


def test_stale_marker_from_a_since_superseded_bundled_release_is_discarded(
    tmp_path: Path,
) -> None:
    """A marker can outlive its own relevance if the *product itself* is
    upgraded in the gap between the interruption and the next launch (the
    bundled digest it targeted is no longer "current"). Blindly resuming
    toward a target that is no longer the current bundled release would be
    wrong, so the marker must be discarded and the starter classified
    normally against whatever is actually on disk."""

    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, "v5_scout_striker")

    starters._write_refresh_marker(
        tmp_path, "v5_scout_striker", target_digest="not-the-current-bundled-digest"
    )
    marker = starters._refresh_marker_path(tmp_path, "v5_scout_striker")
    assert marker.is_file()

    result = ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    # The marker is stale, so this falls through to ordinary classification:
    # the on-disk content is still a recognized pristine Phase C copy, so it
    # is refreshed normally -- just not via marker-driven resume.
    assert {entry.name for entry in result.refreshed} == {"v5_scout_striker"}
    assert not marker.exists()
    assert starter_content_digest(agent_dir) == CURRENT_STARTER_DIGESTS["v5_scout_striker"]


def test_refresh_state_directory_is_never_visible_to_agent_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invariant 3: temporary/marker artifacts must not appear as
    user-selectable agents. The marker directory lives beside ``agents/``,
    never inside it, so this holds structurally -- verified here against a
    real interrupted-and-not-yet-recovered state, not just by inspection.

    Interrupts the *last* name in ``STARTER_AGENT_NAMES`` (``v5_dual_team``)
    specifically, so every other bundled starter has already been installed
    by the time the simulated failure fires -- the catalog-completeness
    assertion below would otherwise be confounded by starters the loop
    simply had not reached yet, which is a property of iteration order, not
    of the marker being (correctly) invisible to discovery.
    """

    assert STARTER_AGENT_NAMES[-1] == "v5_dual_team"
    agents_dir = tmp_path / "agents"
    agent_dir = _seed_phase_c_starter(agents_dir, "v5_dual_team")

    real_write_bytes = Path.write_bytes
    already_failed = False

    def flaky_write_bytes(self: Path, data: bytes) -> int:
        nonlocal already_failed
        if not already_failed and self.parent == agent_dir and self.name == "agent.yaml":
            already_failed = True
            raise OSError("simulated interruption mid-mirror")
        return real_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", flaky_write_bytes)
    with pytest.raises(OSError, match="simulated interruption"):
        ensure_starter_agents(resource_root=_resource_root(), data_root=tmp_path)

    marker = starters._refresh_marker_path(tmp_path, "v5_dual_team")
    assert marker.is_file()
    assert marker.parent != agents_dir
    assert not marker.parent.is_relative_to(agents_dir)

    catalog = discover_agents(tmp_path)
    assert set(catalog) == set(STARTER_AGENT_NAMES)
    assert starters._REFRESH_STATE_DIRNAME not in catalog
