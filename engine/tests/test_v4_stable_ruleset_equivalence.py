"""Frozen-golden characterization of ``bytefray-rules-4``, pinning the
Alpha2-vs-stable gameplay equivalence proven release-blocking at
v4.0.0-rc1 Phase 2.

**History.** From v4.0.0-rc1 Phase 2 through V6 Phase 2B.9, this file
proved the promotion claim directly:

    For identical gameplay inputs, bytefray-rules-4 and
    bytefray-rules-4-alpha2 produce identical gameplay behavior, with
    differences only where Ruleset identity is intentionally part of
    persisted/canonical identity.

It did this by running the *same* ``MatchRequest`` twice -- once under
each Ruleset identity, against real bundled v4 starter agents and the two
"adapted Alpha2" reference agents (``hydra_alpha2``/``nemesis_alpha2``) --
then diffing the two runs' full replay content and canonical result.

**Phase 2B.10 conversion.** ``bytefray-rules-4-alpha1`` and
``bytefray-rules-4-alpha2`` were retired from executable registration by
V6 Phase 2B.10 Scope B
(docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md), per the
disposition in
docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md
Sec E.2/T-8/V.B.1: alpha2's continued executability was load-bearing for
*this file's own proof*, so the registry edit could not land until this
proof was replaced. Rather than deleting the release-blocking evidence
that the promoted stable identity reproduces alpha2's exact gameplay, this
file was converted -- following the same frozen-golden pattern V6
Phase 2B.9 already established for
``test_ruleset_v2_promotion_equivalence.py`` -- into a permanent
characterization: the ``EXPECTED`` table below pins, per scenario, a
SHA-256 digest of the complete nulled-identity replay header, full tick
sequence, and terminal result (plus summary fields for diagnosability)
that ``bytefray-rules-4-alpha2`` produced in its last passing live run
before retirement. Every scenario is now run only under stable
``bytefray-rules-4`` and compared against that frozen snapshot.

**Provenance.** The frozen values were captured at commit
``8244e6b588397206d482ddaf2245201f5f09d80d`` (the ``v6-research`` HEAD
immediately before Phase 2B.10 Scope B's registry edit landed), using this
file's own pre-conversion scenario corpus and helper functions --
reproducible by checking out that commit's version of this file (which
still exercises ``bytefray-rules-4-alpha2`` directly) and rerunning it.
That capture first re-confirmed, for all 23 ruleset-dependent cases below,
that live alpha2-vs-stable equivalence still held (the identical
assertions this file's pre-conversion
``_assert_gameplay_equivalent_and_identity_differs`` made), then derived
these digests from the confirmed-passing alpha2 side. See the Phase 2B.10
completion report (docs/research/v6/V6_PHASE2B10_SCOPE_B_V4_ALPHA_RETIREMENT.md,
Sec C) for the full capture transcript.

**Mutation sensitivity.** Verified during this conversion (not a
permanent test): temporarily changing
``battle_engine.python_runtime.CORE_BEACON_BYTE`` caused every scenario
case below to fail on digest mismatch; reverting restored a clean pass.
See the completion report Sec C for the exact reproduction.

**Policy, restated from the precedent this pattern is copied from:** a
legitimate Ruleset 4 gameplay, Agent API, RNG, or schema change must
version this file's ``EXPECTED`` table deliberately; it must never be
refreshed in place merely to make a regression pass.

Corpus size is deliberately compact, not exhaustive -- unchanged rationale
from the pre-conversion file: each dimension (entrant count, arena size,
seed, agent archetype) is varied against a fixed baseline rather than
fully crossed, since the architecture-level evidence (RulesetPolicy field
equality, placement's fixed domain-separation constant,
process_runtime.py's complete absence of Ruleset-identity branching) has
always narrowed what could possibly differ to "nothing, if the policy
fields agree."

The 4 starter-source-validity regression tests at the bottom of this file
never touch ruleset execution and are unaffected by this conversion.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agent_api import AgentManifestError
from battle_engine.agents import agent_spec_from_dir, resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, ReplayHeader, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

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


def _run_stable(
    tmp_path: Path,
    entrant_names: tuple[str, ...],
    *,
    arena_size: int,
    seed: int,
    ticks: int,
    run_label: str,
) -> Path:
    """Run one match under stable ``bytefray-rules-4``; return replay_path.

    Starts are always omitted (resolved by this call through the identical
    production ``placement.resolve_direct_match_starts`` seam ``bytefray
    run`` uses) -- never precomputed once and reused, so this exercises
    the real resolution path rather than assuming its output.
    """

    specs = tuple(resolve_agent(tmp_path, name) for name in entrant_names)
    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
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
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_path is not None
    return replay_path


def _canonical_snapshot(replay_path: Path) -> dict[str, Any]:
    """Parse one replay into a JSON-serializable snapshot with every
    identity-bearing field nulled out -- the exact shape the frozen alpha2
    golden values were captured from, so the two sides are comparable."""

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
    return {
        "header": asdict(header),
        "ticks": [asdict(tick) for tick in ticks],
        "result": asdict(result),
    }


def _snapshot_digest(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _raw_header(replay_path: Path) -> ReplayHeader:
    return next(r for r in iter_replay(replay_path) if isinstance(r, ReplayHeader))


def _raw_result(replay_path: Path) -> MatchResult:
    return next(r for r in iter_replay(replay_path) if isinstance(r, MatchResult))


def _assert_matches_frozen_golden(
    replay_path: Path, scenario_key: str, *, ticks_expected: int | None = None
) -> None:
    expected = EXPECTED[scenario_key]
    snapshot = _canonical_snapshot(replay_path)
    digest = _snapshot_digest(snapshot)
    assert digest == expected["digest"], (
        f"{scenario_key}: stable bytefray-rules-4 gameplay diverged from the frozen "
        "pre-retirement alpha2 golden -- tick-by-tick behavior, terminal result, or "
        "header content no longer matches what was proven equivalent before alpha2 "
        "was retired"
    )
    raw_result = _raw_result(replay_path)
    assert raw_result.ticks == expected["ticks_run"]
    assert raw_result.termination_reason == expected["termination_reason"]
    assert raw_result.winner == expected["winner"]
    assert len(snapshot["ticks"]) > 0, "corpus sanity: a match that never ticked proves nothing"
    if ticks_expected is not None:
        assert raw_result.ticks == ticks_expected

    # Identity-bearing field: the control's own raw header must legitimately
    # carry its own ID -- never alpha2's (which can no longer execute at all
    # to produce a live comparison value; see the negative execution tests
    # in test_v6_phase2b10_scope_b_retirement.py for that side of the proof).
    raw_header = _raw_header(replay_path)
    assert raw_header.ruleset_id == BYTEFRAY_RULESET_V4_ID


# ---------------------------------------------------------------------------
# EXPECTED -- frozen from bytefray-rules-4-alpha2's last passing run against
# this exact scenario corpus, at commit 8244e6b588397206d482ddaf2245201f5f09d80d,
# immediately before Phase 2B.10 Scope B removed alpha2's executable
# registration. Each digest covers the complete nulled-identity replay
# header, full tick sequence, and terminal result; the summary fields exist
# only to make a mismatch diagnosable without recomputing the digest by
# hand.
# ---------------------------------------------------------------------------

EXPECTED: dict[str, dict[str, Any]] = {
    "grid-256-0": {
        "digest": "11f9cd00c321e013baf874177dc344f0a51a192b7b5c592015cdb0925c4d5810",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-256-1": {
        "digest": "4c8b3a2843c785f42c4af1ac5e168281c11a9d8cb32cd57d051cfbf4002407f9",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-256-3": {
        "digest": "7a041b2c50319dc1fe26180a00f178c2561a1c6bfb1ebe7701f343f945dddf0b",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-256-7": {
        "digest": "78bb0a408db5d7410904e9e4b5df36b774d2e3f2655880308a9c2175d089b1b2",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-256-42": {
        "digest": "3b556861a1ea1735fcc6d6364b640562b44c3c99bf2d3420b96bfe18b0f25fff",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-512-0": {
        "digest": "23dad73dea84eddbd81e8977a8f8cec09aabe8de640a37062b4ac0707db8ca2d",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-512-1": {
        "digest": "b5fe6f75238f677638286a24421671c2bb311c378027d79b9761d8c24706d8a9",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-512-3": {
        "digest": "68a477c84ba4a84ff2bc3a36feaa4797b44a53c4f25364587bece437db200042",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-512-7": {
        "digest": "6eb1dd39825f2f7f6562f5e578dc8e73ae3932e7fdcf46a2408a3810523c3f11",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-512-42": {
        "digest": "a7dd2f58f7c71fb0660328a7f32bbd21054e027cd8841afd058798cae5bd8ccb",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-1024-0": {
        "digest": "d023065ca93964ca25df5490ea4df0b52b1e052f5e96c4f0d5e889efeb11e450",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-1024-1": {
        "digest": "468d21a44250daad2464ddd4960f4bfc9a716095855115d3c8e5de63da3a7fed",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-1024-3": {
        "digest": "bf3ee1da83828808e7da4cf3270c060112fec176c6679a9a7dec6d49361ede11",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-1024-7": {
        "digest": "56db3815c127398ff8e26487699adbaeff8731519e34ce592774a286cffd089d",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "grid-1024-42": {
        "digest": "2b10a9d60d44b4baa67e7cffd0d006f3b14d402c9df8fac832990af6b19dec76",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "three-entrant": {
        "digest": "ae2e9dfe6a3f84237e8bb4a423eb5c5581e8a9c03818a2bc09f102893cc942b3",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "four-entrant": {
        "digest": "1bd039af60a4efc2e60f88487cac04bb8a480d309d5c71afdf8cdedc74b7e598",
        "ticks_run": 300,
        "termination_reason": "tick_limit",
        "winner": "B",
    },
    "hydra-nemesis-512-0": {
        "digest": "479081aa002c7d6295bc9fcf98933bdde49f1354cfab02ef2eaaba7d219c8989",
        "ticks_run": 6,
        "termination_reason": "last_agent_standing",
        "winner": "A",
    },
    "hydra-nemesis-512-7": {
        "digest": "e23b9089354a8a5b37fca1526e7de339630b895466fbccfc9015dbf8c328e4ac",
        "ticks_run": 4,
        "termination_reason": "last_agent_standing",
        "winner": "A",
    },
    "hydra-nemesis-1024-0": {
        "digest": "61d2a81403c9c91c76786c0c880e1bdfe724f9f7ee699b2c4a05f600eb260106",
        "ticks_run": 12,
        "termination_reason": "last_agent_standing",
        "winner": "A",
    },
    "hydra-nemesis-1024-7": {
        "digest": "459dbd443f666359bf399ba2924304943672d5b648553d07589a5ae610ff9a49",
        "ticks_run": 4,
        "termination_reason": "last_agent_standing",
        "winner": "A",
    },
    "multiproc-vs-singleproc": {
        "digest": "023023d2b8c42dc254bc424f2d81d38eff6b5de2ee380643cc53d3e359b5f841",
        "ticks_run": 1000,
        "termination_reason": "tick_limit",
        "winner": None,
    },
    "ticklimit": {
        "digest": "3feb67bc3cdbf82fdf8628389f80c4800938c9f9c73b5bbdec4c36cfa792efa1",
        "ticks_run": 15,
        "termination_reason": "tick_limit",
        "winner": None,
    },
}


# ---------------------------------------------------------------------------
# Arena size x seed grid (2 entrants, single-process short/medium-reach
# starters -- the baseline pairing every other dimension is varied against)
# ---------------------------------------------------------------------------

BASELINE_PAIR = ("v4_claimer", "v4_scout")


@pytest.mark.parametrize("arena_size", [256, 512, 1024])
@pytest.mark.parametrize("seed", [0, 1, 3, 7, 42])
def test_stable_v4_matches_frozen_golden_across_arena_and_seed_grid(
    tmp_path: Path, arena_size: int, seed: int
):
    for name in BASELINE_PAIR:
        _bootstrap_agent(tmp_path, name)
    key = f"grid-{arena_size}-{seed}"
    replay_path = _run_stable(
        tmp_path, BASELINE_PAIR, arena_size=arena_size, seed=seed, ticks=300, run_label=key
    )
    _assert_matches_frozen_golden(replay_path, key)


# ---------------------------------------------------------------------------
# Entrant count: 3 and 4 (2 is already covered by the grid above)
# ---------------------------------------------------------------------------


def test_stable_v4_matches_frozen_golden_with_three_entrants(tmp_path: Path):
    names = ("v4_claimer", "v4_scout", "v4_local_defender")
    for name in names:
        _bootstrap_agent(tmp_path, name)
    replay_path = _run_stable(tmp_path, names, arena_size=512, seed=7, ticks=300, run_label="three-entrant")
    _assert_matches_frozen_golden(replay_path, "three-entrant")


def test_stable_v4_matches_frozen_golden_with_four_entrants_including_a_multi_process_agent(
    tmp_path: Path,
):
    """v4_defender_scout (multi-process: a reach-2 defender and a reach-8
    scout sharing one entrant's quota) is included specifically to exercise
    quota allocation/redistribution across multiple own processes at N=4."""

    names = ("v4_claimer", "v4_scout", "v4_local_defender", "v4_defender_scout")
    for name in names:
        _bootstrap_agent(tmp_path, name)
    replay_path = _run_stable(tmp_path, names, arena_size=512, seed=0, ticks=300, run_label="four-entrant")
    _assert_matches_frozen_golden(replay_path, "four-entrant")


# ---------------------------------------------------------------------------
# Multi-process, disruption, and large-reach coverage: the adapted Alpha2
# reference agents named by the original governing task.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arena_size", [512, 1024])
@pytest.mark.parametrize("seed", [0, 7])
def test_stable_v4_matches_frozen_golden_for_hydra_vs_nemesis(tmp_path: Path, arena_size: int, seed: int):
    """hydra_alpha2 (4 processes, 3 at global/large reach) vs nemesis_alpha2
    (3 processes, including a process literally named "disruptor") --
    real, adapted-Alpha2 multi-process agents exercising large reach,
    process eligibility/selection order under real contention, and
    disruption, at two arena scales."""

    names = ("hydra_alpha2", "nemesis_alpha2")
    for name in names:
        _bootstrap_agent(tmp_path, name)
    key = f"hydra-nemesis-{arena_size}-{seed}"
    replay_path = _run_stable(tmp_path, names, arena_size=arena_size, seed=seed, ticks=1000, run_label=key)
    _assert_matches_frozen_golden(replay_path, key)


def test_stable_v4_matches_frozen_golden_with_multi_process_vs_single_process_attacker(tmp_path: Path):
    """v4_defender_scout (multi-process) vs v4_concentrated_attacker
    (single-process, reach=4) -- a second, independent multi-process
    pairing distinct from hydra/nemesis, at a generous tick budget so
    contact and likely core capture are both exercised."""

    names = ("v4_defender_scout", "v4_concentrated_attacker")
    for name in names:
        _bootstrap_agent(tmp_path, name)
    replay_path = _run_stable(
        tmp_path, names, arena_size=512, seed=3, ticks=1000, run_label="multiproc-vs-singleproc"
    )
    _assert_matches_frozen_golden(replay_path, "multiproc-vs-singleproc")


# ---------------------------------------------------------------------------
# Termination-reason coverage: tick-limit specifically (the grid above and
# the hydra/nemesis pairing already produce a mix of last_agent_standing/
# all_agents_dead/tick_limit matches organically; this pins tick_limit
# deliberately so it is never left to chance).
# ---------------------------------------------------------------------------


def test_stable_v4_matches_frozen_golden_at_tick_limit_termination(tmp_path: Path):
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

    replay_path = _run_stable(
        tmp_path,
        ("v4_local_defender", "v4_local_defender_twin"),
        arena_size=1024,
        seed=1,
        ticks=15,
        run_label="ticklimit",
    )
    _assert_matches_frozen_golden(replay_path, "ticklimit", ticks_expected=15)


# ---------------------------------------------------------------------------
# Bytefray V6 Phase 2B.1 -- regression coverage for _bootstrap_agent()'s
# starter-source validity check (docs/research/v6/V6_PHASE1_REPOSITORY_DIET
# _AUDIT.md Sec 8.2). Every case below would have passed silently on a
# stale/emptied higher-priority source directory before this fix, exactly
# reproducing the V6 Phase 0 failure at the site Phase 1 traced it to --
# entirely against isolated tmp_path fixtures, never the developer's real
# gitignored agents/ catalog. Unaffected by the Phase 2B.10 conversion:
# these never touch ruleset execution.
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
