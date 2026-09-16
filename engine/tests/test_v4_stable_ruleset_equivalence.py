"""Release-blocking Alpha2 <-> stable-v4 gameplay equivalence (v4.0.0-rc1 Phase 2).

The Phase 2 promotion's central claim is:

    For identical gameplay inputs, bytefray-rules-4 and
    bytefray-rules-4-alpha2 produce identical gameplay behavior, with
    differences only where Ruleset identity is intentionally part of
    persisted/canonical identity.

This is proven here by running the *same* MatchRequest twice -- once under
each Ruleset identity, with entrant starts independently resolved by each
run's own call into the identical production placement seam
(``placement.resolve_direct_match_starts``) -- against real bundled v4
starter agents and the two "adapted Alpha2" reference agents
(``hydra_alpha2``/``nemesis_alpha2``, copied from this repository's own
``agents/`` directory, never a hand-built stand-in), then diffing the two
runs' full replay content and canonical result. Every field compared is
real evidence read back from an actual match execution, never asserted by
construction.

Comparison discipline (task Sec 4.2/4.3): every ``TickSnapshot`` (per-tick
process/agent/score/memory-diff/event state -- covers process anchors,
process eligibility, action sequence, READ/WRITE/MOVE results, disruption
events, quota allocation/redistribution, and ownership/core state in one
shot, since all of it is recorded there) must compare byte-for-byte equal.
The terminal ``MatchResult`` and ``ReplayHeader`` must compare equal on
every field *except* the four identity-bearing ones
(``replay_id``/``match_id``/``result_id`` and the header's own
``ruleset_id``), which must legitimately *differ* -- checked explicitly, so
this corpus cannot pass vacuously by comparing two copies of the same
artifact.

Corpus size is deliberately compact, not exhaustive: each dimension (entrant
count, arena size, seed, agent archetype) is varied against a fixed
baseline rather than fully crossed, since the architecture-level evidence
(RulesetPolicy field equality, placement's fixed domain-separation
constant, process_runtime.py's complete absence of Ruleset-identity
branching -- see the commit introducing bytefray-rules-4) already narrows
what could possibly differ to "nothing, if the policy fields agree" -- this
corpus is the release-blocking behavioral proof of that claim, not a
first search for a difference.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ALPHA2_ID, BYTEFRAY_RULESET_V4_ID

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_SOURCE_DIRS = (
    REPO_ROOT / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)


def _is_usable_agent_source(path: Path) -> bool:
    """Whether ``path`` is a directory ``resolve_agent`` could actually load.

    Mirrors the real discovery/resolution check (``agent_spec_from_dir``,
    the same one ``discover_agents_in``/``resolve_agent`` use) instead of a
    bare ``is_dir()`` -- a stale, emptied local ``agents/<name>`` (e.g. only
    a leftover ``__pycache__``) satisfies ``is_dir()`` but must not shadow
    the correct bundled fallback. A directory whose manifest fails to parse
    is likewise treated as unusable rather than propagating the error here:
    this is only a source *candidate* selection, not the final load.
    """

    try:
        return agent_spec_from_dir(path) is not None
    except AgentManifestError:
        return False


def _bootstrap_agent(tmp_path: Path, name: str) -> None:
    """Copy a real, repository-tracked agent into an isolated data root.

    Never a hand-built fixture: these are the actual bundled v4 starters
    (``engine/src/battle_engine/data/starter_agents/``) and the actual
    adapted-Alpha2 reference agents this repository ships under
    ``agents/`` -- copied, not rewritten, so what runs here is exactly what
    a user's own installation would run.
    """

    dest = tmp_path / "agents" / name
    if dest.exists():
        return
    for source_root in STARTER_SOURCE_DIRS:
        source = source_root / name
        if _is_usable_agent_source(source):
            shutil.copytree(source, dest)
            return
    raise FileNotFoundError(f"no source found for agent {name!r} under {STARTER_SOURCE_DIRS}")


def _seat_label(index: int) -> str:
    return chr(ord("A") + index)


def _run_under_ruleset(
    tmp_path: Path,
    entrant_names: tuple[str, ...],
    *,
    ruleset_id: str,
    arena_size: int,
    seed: int,
    ticks: int,
    run_label: str,
) -> tuple[Path, Path]:
    """Run one match under ``ruleset_id``; return (replay_path, result_path).

    Starts are always omitted (resolved by this call, independently per
    Ruleset id, through the identical production
    ``placement.resolve_direct_match_starts`` seam ``bytefray run`` uses)
    -- never precomputed once and reused, so this exercises the real
    per-Ruleset resolution path rather than assuming its output.
    """

    specs = tuple(resolve_agent(tmp_path, name) for name in entrant_names)
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=arena_size,
        entrant_count=len(entrant_names),
        supplied_starts=[None] * len(entrant_names),
        seed=seed,
    )
    entrants = tuple(
        MatchEntrant.python(_seat_label(i), name, starts[i], spec)
        for i, (name, spec) in enumerate(zip(entrant_names, specs, strict=True))
    )
    run_dir = tmp_path / "runs" / run_label
    run_dir.mkdir(parents=True)
    replay_path = run_dir / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=arena_size, instr_per_tick=8),
        entrants=entrants,
        max_ticks=ticks,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=ruleset_id,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path, result.result_path


def _canonical_replay_records(
    replay_path: Path,
) -> tuple[ReplayHeader, tuple[TickSnapshot, ...], MatchResult]:
    """Parse one replay into (header, ticks, terminal result), each with
    every identity-bearing field nulled out for comparison purposes -- the
    raw (non-nulled) values are read separately by the caller to confirm
    they legitimately differ."""

    header: ReplayHeader | None = None
    ticks: list[TickSnapshot] = []
    result: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = replace(record, replay_id=None, match_id=None, result_id=None, ruleset_id=None)
        elif isinstance(record, TickSnapshot):
            ticks.append(record)
        elif isinstance(record, MatchResult):
            result = replace(record, replay_id=None, match_id=None, result_id=None)
    assert header is not None, f"{replay_path}: no header record"
    assert result is not None, f"{replay_path}: no terminal result record"
    return header, tuple(ticks), result


def _raw_header(replay_path: Path) -> ReplayHeader:
    return next(r for r in iter_replay(replay_path) if isinstance(r, ReplayHeader))


def _raw_result(replay_path: Path) -> MatchResult:
    return next(r for r in iter_replay(replay_path) if isinstance(r, MatchResult))


def _assert_gameplay_equivalent_and_identity_differs(
    alpha2_replay: Path, stable_replay: Path, *, ticks_expected: int | None = None
) -> None:
    alpha2_header, alpha2_ticks, alpha2_result = _canonical_replay_records(alpha2_replay)
    stable_header, stable_ticks, stable_result = _canonical_replay_records(stable_replay)

    # The forbidden case: any gameplay-observable difference. Compared as
    # whole dataclass sequences (not field-by-field) so nothing is silently
    # excluded by an incomplete manual field list.
    assert alpha2_ticks == stable_ticks, (
        "tick-by-tick gameplay diverged between alpha2 and the stable identity"
    )
    assert alpha2_result == stable_result, (
        "terminal result (winner/score/termination/processes) diverged"
    )
    assert alpha2_header == stable_header, (
        "replay header (config/agents/runtime_kind/reproducibility/entrants) diverged"
    )
    assert len(alpha2_ticks) > 0, "corpus sanity: a match that never ticked proves nothing"
    if ticks_expected is not None:
        assert alpha2_result.ticks == stable_result.ticks == ticks_expected

    # The expected case: identity-bearing fields legitimately differ. This
    # is what stops the assertions above from passing vacuously by
    # comparing an artifact against itself.
    raw_alpha2_header = _raw_header(alpha2_replay)
    raw_stable_header = _raw_header(stable_replay)
    assert raw_alpha2_header.ruleset_id == BYTEFRAY_RULESET_V4_ALPHA2_ID
    assert raw_stable_header.ruleset_id == BYTEFRAY_RULESET_V4_ID
    assert raw_alpha2_header.match_id != raw_stable_header.match_id
    assert raw_alpha2_header.result_id != raw_stable_header.result_id
    assert raw_alpha2_header.replay_id != raw_stable_header.replay_id
    raw_alpha2_result = _raw_result(alpha2_replay)
    raw_stable_result = _raw_result(stable_replay)
    assert raw_alpha2_result.match_id != raw_stable_result.match_id
    assert raw_alpha2_result.result_id != raw_stable_result.result_id


def _equivalence_pair(
    tmp_path: Path,
    entrant_names: tuple[str, ...],
    *,
    arena_size: int,
    seed: int,
    ticks: int,
    label: str,
) -> None:
    for name in entrant_names:
        _bootstrap_agent(tmp_path, name)
    alpha2_replay, _ = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V4_ALPHA2_ID,
        arena_size=arena_size,
        seed=seed,
        ticks=ticks,
        run_label=f"{label}-alpha2",
    )
    stable_replay, _ = _run_under_ruleset(
        tmp_path,
        entrant_names,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=arena_size,
        seed=seed,
        ticks=ticks,
        run_label=f"{label}-stable",
    )
    _assert_gameplay_equivalent_and_identity_differs(alpha2_replay, stable_replay)


# ---------------------------------------------------------------------------
# Arena size x seed grid (2 entrants, single-process short/medium-reach
# starters -- the baseline pairing every other dimension is varied against)
# ---------------------------------------------------------------------------

BASELINE_PAIR = ("v4_claimer", "v4_scout")


@pytest.mark.parametrize("arena_size", [256, 512, 1024])
@pytest.mark.parametrize("seed", [0, 1, 3, 7, 42])
def test_equivalence_across_arena_and_seed_grid(tmp_path: Path, arena_size: int, seed: int):
    _equivalence_pair(
        tmp_path,
        BASELINE_PAIR,
        arena_size=arena_size,
        seed=seed,
        ticks=300,
        label=f"grid-{arena_size}-{seed}",
    )


# ---------------------------------------------------------------------------
# Entrant count: 3 and 4 (2 is already covered by the grid above)
# ---------------------------------------------------------------------------


def test_equivalence_with_three_entrants(tmp_path: Path):
    _equivalence_pair(
        tmp_path,
        ("v4_claimer", "v4_scout", "v4_local_defender"),
        arena_size=512,
        seed=7,
        ticks=300,
        label="three-entrant",
    )


def test_equivalence_with_four_entrants_including_a_multi_process_agent(tmp_path: Path):
    """v4_defender_scout (multi-process: a reach-2 defender and a reach-8
    scout sharing one entrant's quota) is included specifically to exercise
    quota allocation/redistribution across multiple own processes at N=4."""

    _equivalence_pair(
        tmp_path,
        ("v4_claimer", "v4_scout", "v4_local_defender", "v4_defender_scout"),
        arena_size=512,
        seed=0,
        ticks=300,
        label="four-entrant",
    )


# ---------------------------------------------------------------------------
# Multi-process, disruption, and large-reach coverage: the adapted Alpha2
# reference agents named explicitly by the governing task.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arena_size", [512, 1024])
@pytest.mark.parametrize("seed", [0, 7])
def test_equivalence_for_hydra_vs_nemesis(tmp_path: Path, arena_size: int, seed: int):
    """hydra_alpha2 (4 processes, 3 at global/large reach) vs nemesis_alpha2
    (3 processes, including a process literally named "disruptor") --
    real, adapted-Alpha2 multi-process agents exercising large reach,
    process eligibility/selection order under real contention, and
    disruption, at two arena scales (both within the qualified band)."""

    _equivalence_pair(
        tmp_path,
        ("hydra_alpha2", "nemesis_alpha2"),
        arena_size=arena_size,
        seed=seed,
        ticks=1000,
        label=f"hydra-nemesis-{arena_size}-{seed}",
    )


def test_equivalence_with_multi_process_vs_single_process_attacker(tmp_path: Path):
    """v4_defender_scout (multi-process) vs v4_concentrated_attacker
    (single-process, reach=4) -- a second, independent multi-process
    pairing distinct from hydra/nemesis, at a generous tick budget so
    contact and likely core capture are both exercised."""

    _equivalence_pair(
        tmp_path,
        ("v4_defender_scout", "v4_concentrated_attacker"),
        arena_size=512,
        seed=3,
        ticks=1000,
        label="multiproc-vs-singleproc",
    )


# ---------------------------------------------------------------------------
# Termination-reason coverage: tick-limit specifically (the grid above and
# the hydra/nemesis pairing already produce a mix of last_agent_standing/
# all_agents_dead/tick_limit matches organically; this pins tick_limit
# deliberately so it is never left to chance).
# ---------------------------------------------------------------------------


def test_equivalence_at_tick_limit_termination(tmp_path: Path):
    """Two short-reach defenders at a tiny tick budget essentially never
    find each other -- forces TICK_LIMIT termination deterministically, so
    that termination reason/tick count are compared under this specific
    path too, not only under decisive-outcome matches."""

    _bootstrap_agent(tmp_path, "v4_local_defender")
    # Two independent copies under different discovery ids, since a match
    # cannot field the same agent id in two seats.
    twin_dir = tmp_path / "agents" / "v4_local_defender_twin"
    shutil.copytree(tmp_path / "agents" / "v4_local_defender", twin_dir)
    (twin_dir / "agent.yaml").write_text(
        (twin_dir / "agent.yaml").read_text(encoding="utf-8").replace(
            "v4_local_defender", "v4_local_defender_twin"
        ),
        encoding="utf-8",
    )

    alpha2_replay, _ = _run_under_ruleset(
        tmp_path,
        ("v4_local_defender", "v4_local_defender_twin"),
        ruleset_id=BYTEFRAY_RULESET_V4_ALPHA2_ID,
        arena_size=1024,
        seed=1,
        ticks=15,
        run_label="ticklimit-alpha2",
    )
    stable_replay, _ = _run_under_ruleset(
        tmp_path,
        ("v4_local_defender", "v4_local_defender_twin"),
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=1024,
        seed=1,
        ticks=15,
        run_label="ticklimit-stable",
    )
    _assert_gameplay_equivalent_and_identity_differs(alpha2_replay, stable_replay, ticks_expected=15)
    alpha2_result = _raw_result(alpha2_replay)
    assert alpha2_result.termination_reason == "tick_limit"


# ---------------------------------------------------------------------------
# Bytefray V6 Phase 2B.1 -- regression coverage for _bootstrap_agent()'s
# starter-source validity check (docs/research/v6/V6_PHASE1_REPOSITORY_DIET
# _AUDIT.md Sec 8.2). Every case below would have passed silently on a
# stale/emptied higher-priority source directory before this fix, exactly
# reproducing the V6 Phase 0 failure at the site Phase 1 traced it to --
# entirely against isolated tmp_path fixtures, never the developer's real
# gitignored agents/ catalog.
# ---------------------------------------------------------------------------


def test_bootstrap_agent_skips_stale_cache_only_source_and_falls_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A higher-priority source candidate that satisfies ``is_dir()`` but
    holds only a stale ``__pycache__`` (the exact Phase 0 shape) must not
    shadow a genuinely valid lower-priority fallback."""

    primary_root = tmp_path / "sources" / "primary"
    (primary_root / "v4_fake" / "__pycache__").mkdir(parents=True)
    (primary_root / "v4_fake" / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"\x00")

    secondary_root = tmp_path / "sources" / "secondary"
    (secondary_root / "v4_fake").mkdir(parents=True)
    (secondary_root / "v4_fake" / "agent.yaml").write_text('{"name": "v4_fake"}', encoding="utf-8")
    (secondary_root / "v4_fake" / "agent.py").write_text(
        "def create_agent(**_kwargs):\n    raise NotImplementedError\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        sys.modules[__name__], "STARTER_SOURCE_DIRS", (primary_root, secondary_root)
    )

    data_root = tmp_path / "data_root"
    _bootstrap_agent(data_root, "v4_fake")

    installed = data_root / "agents" / "v4_fake"
    assert (installed / "agent.yaml").is_file()
    assert (installed / "agent.py").is_file()


def test_bootstrap_agent_prefers_a_valid_first_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The ordinary case is unaffected by the fix: a genuinely valid
    higher-priority source is still preferred over a valid fallback."""

    primary_root = tmp_path / "sources" / "primary"
    (primary_root / "v4_fake").mkdir(parents=True)
    (primary_root / "v4_fake" / "agent.yaml").write_text(
        '{"name": "v4_fake", "note": "primary"}', encoding="utf-8"
    )

    secondary_root = tmp_path / "sources" / "secondary"
    (secondary_root / "v4_fake").mkdir(parents=True)
    (secondary_root / "v4_fake" / "agent.yaml").write_text(
        '{"name": "v4_fake", "note": "secondary"}', encoding="utf-8"
    )

    monkeypatch.setattr(
        sys.modules[__name__], "STARTER_SOURCE_DIRS", (primary_root, secondary_root)
    )

    data_root = tmp_path / "data_root"
    _bootstrap_agent(data_root, "v4_fake")

    installed_manifest = (data_root / "agents" / "v4_fake" / "agent.yaml").read_text(
        encoding="utf-8"
    )
    assert "primary" in installed_manifest


def test_bootstrap_agent_raises_when_no_candidate_is_usable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Every candidate invalid (one empty, one entirely absent) must still
    fail loudly rather than silently copying unusable content."""

    primary_root = tmp_path / "sources" / "primary"
    (primary_root / "v4_fake").mkdir(parents=True)
    secondary_root = tmp_path / "sources" / "secondary"  # never created

    monkeypatch.setattr(
        sys.modules[__name__], "STARTER_SOURCE_DIRS", (primary_root, secondary_root)
    )

    with pytest.raises(FileNotFoundError):
        _bootstrap_agent(tmp_path / "data_root", "v4_fake")


def test_bootstrap_agent_never_touches_an_existing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A destination that already has content -- whatever its origin -- is
    never inspected or overwritten; only a wholly missing destination
    triggers a source copy. This is the pre-existing safety property the
    fix must not weaken."""

    primary_root = tmp_path / "sources" / "primary"
    (primary_root / "v4_fake").mkdir(parents=True)
    (primary_root / "v4_fake" / "agent.yaml").write_text('{"name": "v4_fake"}', encoding="utf-8")

    monkeypatch.setattr(sys.modules[__name__], "STARTER_SOURCE_DIRS", (primary_root,))

    data_root = tmp_path / "data_root"
    dest = data_root / "agents" / "v4_fake"
    dest.mkdir(parents=True)
    (dest / "agent.yaml").write_text('{"name": "v4_fake", "user_edited": true}', encoding="utf-8")

    _bootstrap_agent(data_root, "v4_fake")

    assert "user_edited" in (dest / "agent.yaml").read_text(encoding="utf-8")
