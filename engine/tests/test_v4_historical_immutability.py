"""bytefray-rules-4-alpha1/alpha2 identity and isolation guarantees, kept
correct across V6 Phase 2B.10 Scope B's retirement of both from executable
registration.

**History.** From v4.0.0-rc1 Phase 2 through V6 Phase 2B.9, this file
proved two live concerns not covered by
``test_v4_alpha2_placement.py``/the round-robin process-selection suites:
that each alpha's own canonical match/result identity stayed unchanged now
that a third Ruleset (stable ``bytefray-rules-4``) shared their exact
policy field values, and that running a stable-v4 match between two alpha
matches never mutated state that would change either alpha's result.

**Phase 2B.10 conversion.** ``bytefray-rules-4-alpha1`` and
``bytefray-rules-4-alpha2`` were retired from executable registration by
V6 Phase 2B.10 Scope B, so neither can be dispatched to produce a new live
comparison value any more (per
docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md Sec E.3,
this file is one of the tests that "must survive every cleanup" -- it just
cannot keep doing so by literally re-executing the retired identities).
Both concerns are preserved, adapted to what remains genuinely testable
post-retirement (task Sec 10: "prefer converting it to a frozen
persisted-artifact or golden characterization; do not retain an
executable policy solely to keep the test convenient"):

1. **Canonical-identity pinning** is now a frozen-persisted-artifact
   check: the exact replay files alpha1 and alpha2 produced for this
   file's pinned scenario (seed=5) immediately before retirement are
   committed fixtures
   (``engine/tests/fixtures/v4_historical_immutability/``); this file
   loads them and asserts their headers still carry exactly the literal
   ids this suite has pinned since before the stable identity existed.
   This is legitimate historical-artifact-replayability coverage --
   distinct from, and unaffected by, live re-execution.

2. **Cross-execution state isolation** for the *live, currently-
   executable* control is preserved as a live regression test, but
   necessarily generalized: the original test proved "no shared
   module-level state leaks from a stable-v4 execution into a
   *subsequent alpha1* execution reading it." With alpha1 retired, there
   is no second live process-Ruleset left to interleave with (after this
   phase, ``PROCESS_RULESET_IDS`` has exactly one member --
   ``bytefray-rules-4`` itself). The live claim is therefore restated as
   "no state leaks from an interceding execution under any other
   *currently executable* Ruleset into a subsequent stable-v4 execution,"
   using ``bytefray-rules-2`` (a different runtime controller entirely --
   ``PythonEntrantController``, not ``ProcessMatchController``) as the
   interceding execution. This is an honestly narrower guarantee than the
   original in one respect (it no longer specifically proves isolation
   between two *process*-Ruleset executions, since only one exists), but
   the strongest remaining evidence for that specific narrower claim is
   structural, not behavioral, and unchanged by this phase:
   ``process_runtime.py`` still contains zero Ruleset-identity branching
   at all (docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md
   Sec E.1), so there is no Ruleset-conditional code path for a second
   process-Ruleset to have exercised differently in the first place.

   In addition, this file retains a frozen check that the *last live
   confirmation* of the original claim (two fixture replays, captured
   immediately before retirement: alpha1 run, then stable-v4 run, then
   alpha1 rerun with identical inputs) did in fact match byte-for-byte --
   the exact evidence this suite relied on for every release up to and
   including the one that retired alpha1.

**Provenance.** All four fixture replays in
``engine/tests/fixtures/v4_historical_immutability/`` were captured at
commit ``8244e6b588397206d482ddaf2245201f5f09d80d`` (the ``v6-research``
HEAD immediately before Phase 2B.10 Scope B's registry edit landed), using
this file's own pre-conversion ``_run`` helper against
``bytefray-rules-4-alpha1``/``bytefray-rules-4-alpha2`` while both were
still fully registered. See the Phase 2B.10 completion report
(docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md, Sec C) for
the full capture transcript.

The 2 starter-source-validity regression tests at the bottom of this file
are unaffected by this conversion -- they never touch ruleset execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import ReplayHeader, iter_replay
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V2_ID, BYTEFRAY_RULESET_V4_ID
from battle_engine.starters import ensure_starter_agents

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_SOURCE_DIRS = (
    REPO_ROOT / "agents",
    REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "v4_historical_immutability"


def _is_usable_agent_source(path: Path) -> bool:
    try:
        return agent_spec_from_dir(path) is not None
    except AgentManifestError:
        return False


def _bootstrap_agent(tmp_path: Path, name: str) -> None:
    dest = tmp_path / "agents" / name
    if dest.exists():
        return
    for source_root in STARTER_SOURCE_DIRS:
        source = source_root / name
        if _is_usable_agent_source(source):
            import shutil

            shutil.copytree(source, dest)
            return
    raise FileNotFoundError(f"no source found for agent {name!r}")


def _run_control(tmp_path: Path, seed: int, label: str) -> ReplayHeader:
    names = ("v4_claimer", "v4_scout")
    for name in names:
        _bootstrap_agent(tmp_path, name)
    specs = tuple(resolve_agent(tmp_path, name) for name in names)
    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=512,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    entrants = tuple(
        MatchEntrant.python(chr(ord("A") + i), name, starts[i], spec)
        for i, (name, spec) in enumerate(zip(names, specs, strict=True))
    )
    run_dir = tmp_path / "runs" / label
    run_dir.mkdir(parents=True)
    replay_path = run_dir / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=512, instr_per_tick=8),
        entrants=entrants,
        max_ticks=50,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    NativeMatchService().run(request)
    return next(r for r in iter_replay(replay_path) if isinstance(r, ReplayHeader))


def _run_interceding_ruleset2(tmp_path: Path, seed: int, label: str) -> None:
    """Run one throwaway match under the still-executable
    ``bytefray-rules-2`` -- a different runtime controller entirely
    (``PythonEntrantController``, Agent API v1) -- purely to occupy the
    shared engine machinery between two control runs."""

    ensure_starter_agents(data_root=tmp_path)
    names = ("claimer", "hunter")
    specs = tuple(resolve_agent(tmp_path, name) for name in names)
    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V2_ID,
        arena_size=1024,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    entrants = tuple(
        MatchEntrant.python(chr(ord("A") + i), name, starts[i], spec)
        for i, (name, spec) in enumerate(zip(names, specs, strict=True))
    )
    run_dir = tmp_path / "runs" / label
    run_dir.mkdir(parents=True)
    replay_path = run_dir / "replay.jsonl"
    request = MatchRequest(
        config=Config(seed=seed, arena_size=1024, instr_per_tick=8),
        entrants=entrants,
        max_ticks=50,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V2_ID,
    )
    NativeMatchService().run(request)


def _fixture_header(name: str) -> ReplayHeader:
    path = FIXTURES_DIR / name
    return next(r for r in iter_replay(path) if isinstance(r, ReplayHeader))


# ---------------------------------------------------------------------------
# Concern 1: canonical-identity pinning, now read from frozen fixtures
# instead of a live re-execution.
# ---------------------------------------------------------------------------


def test_alpha1_and_alpha2_canonical_ids_are_pinned_in_frozen_historical_replays():
    """v4_claimer vs v4_scout, arena 512, seed 5, ticks 50 -- pinned exactly
    as it was computed on this repository before the stable identity's
    registration, and re-confirmed exactly as it stood immediately before
    Phase 2B.10 retired both alphas from execution. The fixture replays
    themselves are the historical record now; there is no live mechanism
    left to regenerate them (see this file's module docstring)."""

    alpha1 = _fixture_header("alpha1_pinned_seed5_replay.jsonl")
    alpha2 = _fixture_header("alpha2_pinned_seed5_replay.jsonl")

    assert alpha1.match_id == "match_b53e76a536d65e9f35b9e560"
    assert alpha1.result_id == "result_4eac520d48af9cd1ae859365"
    assert alpha2.match_id == "match_779a09b9950d0e4db27b5ddb"
    assert alpha2.result_id == "result_50d49c7732848a9541fc9a93"
    assert alpha1.match_id != alpha2.match_id
    assert alpha1.ruleset_id == "bytefray-rules-4-alpha1"
    assert alpha2.ruleset_id == "bytefray-rules-4-alpha2"


def test_frozen_interleave_fixtures_confirm_alpha1_was_immune_to_control_interleaving():
    """The last live confirmation of "a stable-v4 execution does not mutate
    state a subsequent alpha1 execution reads" before retirement: alpha1
    was run, then a stable-v4 match, then alpha1 again with identical
    inputs -- both captured as fixtures. Their equality here is the frozen
    record of that proof, not a new live check (no live alpha1 execution
    remains possible)."""

    first = _fixture_header("alpha1_interleave_seed9_first_replay.jsonl")
    second = _fixture_header("alpha1_interleave_seed9_second_replay.jsonl")

    assert first.match_id == second.match_id == "match_439a7f1b8e11ccab3fcd4de0"
    assert first.result_id == second.result_id == "result_ade37bc6616f5492fab9dd00"
    assert first.reproducibility == second.reproducibility


# ---------------------------------------------------------------------------
# Concern 2: cross-execution state isolation for the live control, restated
# using the only other Ruleset family still executable post-retirement.
# ---------------------------------------------------------------------------


def test_stable_v4_execution_is_unaffected_by_an_interceding_execution_under_a_different_ruleset(
    tmp_path: Path,
):
    """Runs the control, then an interceding match under the differently-
    implemented ``bytefray-rules-2``, then the control again with
    identical inputs -- the second control run must reproduce the first
    exactly. Proves no cross-Ruleset shared/global state (module-level
    caches, mutable registries, RNG state) leaks between the two
    Ruleset families that remain executable after alpha1/alpha2's
    retirement."""

    first = _run_control(tmp_path, seed=9, label="isolation-first")
    _run_interceding_ruleset2(tmp_path, seed=9, label="isolation-interceding")
    second = _run_control(tmp_path, seed=9, label="isolation-second")

    assert first.match_id == second.match_id
    assert first.result_id == second.result_id
    assert first.reproducibility == second.reproducibility


# ---------------------------------------------------------------------------
# Bytefray V6 Phase 2B.1 -- regression coverage for _bootstrap_agent()'s
# starter-source validity check, the same defect and fix as in
# test_v4_stable_ruleset_equivalence.py (which carries the full battery of
# cases; docs/research/v6/V6_PHASE1_REPOSITORY_DIET_AUDIT.md Sec 8.2).
# Isolated tmp_path fixtures only -- never the real gitignored agents/
# catalog. Unaffected by the Phase 2B.10 conversion above.
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


def test_bootstrap_agent_never_touches_an_existing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A destination that already has content is never inspected or
    overwritten -- the pre-existing safety property the fix must not
    weaken."""

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
