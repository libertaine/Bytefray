"""``NativeMatchService.run`` dispatch-boundary characterization.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
retired VM/blob execution: every test in this file used to build raw VM
``MatchEntrant`` objects (``battle_engine.core.Kernel``/``builtins.build_agent``/
``enc``) and drive them through ``NativeMatchService``. The concerns those
tests actually protected -- artifact atomicity on success and on every
class of failure, duplicate-entrant-id rejection, and fail-closed Ruleset
resolution -- are dispatch-boundary properties of ``NativeMatchService``
itself, not VM-specific, so they are converted to exercise the retained
process path (bundled ``v4_claimer`` starter, Agent API v2) instead of
being dropped. The direct legacy-Kernel-vs-service comparison and the
VM-specific termination-reason enumeration were removed outright: both
literally compared against ``Kernel``, which no longer exists, and
equivalent termination-reason coverage for the retained control already
exists in ``test_v4_process_semantics.py``/``test_v4_production_integration.py``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from battle_engine.config import Config, Weights
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    UnsupportedMatchCompositionError,
)
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID, UnknownRulesetError


def _config() -> Config:
    # bytefray-rules-4 fixes the entrant action quota at Q=8
    # (ProcessMatchController.from_python_entrants); every VM-era arbitrary
    # instr_per_tick this file used to pass is replaced with that pin.
    return Config(
        arena_size=128,
        instr_per_tick=8,
        seed=73,
        win_mode="score_fallback",
        weights=Weights(alive=0.25, kill=3.5, territory=0.5, territory_bucket=16),
    )


def _real_v2_entrants(data_root: Path) -> tuple[MatchEntrant, ...]:
    """Two real, resolvable Agent API v2 entrants: the bundled ``v4_claimer``
    starter installed twice under different discovery ids, so a match can
    actually run end to end without authoring a throwaway agent by hand.
    """

    from battle_engine.agents import resolve_agent
    from battle_engine.starters import ensure_starter_agents

    ensure_starter_agents(data_root=data_root)
    spec = resolve_agent(data_root, "v4_claimer")
    return (
        MatchEntrant.python("A", "claimer-a", 0, spec),
        MatchEntrant.python("B", "claimer-b", 64, spec),
    )


def test_request_and_internal_results_are_frozen(tmp_path):
    entrants = _real_v2_entrants(tmp_path)
    request = MatchRequest(_config(), entrants, 5, tmp_path / "replay.jsonl", False)
    with pytest.raises(FrozenInstanceError):
        request.max_ticks = 2  # type: ignore[misc]

    result = NativeMatchService().run(request)
    with pytest.raises(TypeError):
        result.score["A"] = 99  # type: ignore[index]


def test_duplicate_entrant_ids_are_rejected(tmp_path):
    from battle_engine.agents import resolve_agent
    from battle_engine.starters import ensure_starter_agents

    ensure_starter_agents(data_root=tmp_path)
    spec = resolve_agent(tmp_path, "v4_claimer")
    entrants = (
        MatchEntrant.python("A", "first", 0, spec),
        MatchEntrant.python("A", "second", 32, spec),
    )

    with pytest.raises(UnsupportedMatchCompositionError, match="unique"):
        NativeMatchService().run(
            MatchRequest(_config(), entrants, 2, tmp_path / "replay.jsonl", False)
        )
    # Nothing should have been written for a request rejected before execution.
    assert not (tmp_path / "replay.jsonl").exists()


def test_unknown_ruleset_id_fails_closed_before_any_runtime_executes(tmp_path, monkeypatch):
    """A Ruleset that fails to resolve must abort before any gameplay runs.

    Simulates a future ``resolve_ruleset_policy`` rejecting the currently
    frozen ID (the resolver itself is fail-closed by construction -- see
    ``test_ruleset_policy.py``); this proves the *call site* on the native
    match boundary is on the critical path before the process controller is
    constructed, not merely available and unused. No replay/result artifact
    is written, matching every other pre-execution rejection in this file.
    """

    replay = tmp_path / "replay.jsonl"
    entrants = tuple(
        MatchEntrant.python(slot, f"agent-{slot.lower()}", start, {"kind": "python", "api_version": 2})
        for slot, start in (("A", 0), ("B", 32))
    )

    def _fail_resolution(ruleset_id: str) -> None:
        raise UnknownRulesetError(ruleset_id)

    monkeypatch.setattr("battle_engine.match_service.resolve_ruleset_policy", _fail_resolution)

    with pytest.raises(UnknownRulesetError):
        NativeMatchService().run(
            MatchRequest(_config(), entrants, 5, replay, False, ruleset_id=BYTEFRAY_RULESET_V4_ID)
        )

    assert not replay.exists()
    assert not replay.with_name("result.json").exists()
    assert not replay.with_name("summary.json").exists()


def test_replay_publication_is_atomic_on_success(tmp_path):
    replay = tmp_path / "replay.jsonl"
    entrants = _real_v2_entrants(tmp_path)

    result = NativeMatchService().run(
        MatchRequest(_config(), entrants, 5, replay, False)
    )

    assert replay.is_file()
    assert result.result_path is not None and result.result_path.is_file()
    # No leftover temporary file from the write-then-rename sequence.
    assert not list(tmp_path.glob(".replay.jsonl.*.tmp"))
    assert not list(tmp_path.glob(".replay.jsonl.*.canonical.tmp"))


def test_canonicalization_failure_leaves_no_artifacts(tmp_path, monkeypatch):
    replay = tmp_path / "replay.jsonl"
    summary = tmp_path / "summary.json"
    entrants = _real_v2_entrants(tmp_path)

    def fail_write(_path, _records):
        raise OSError("canonical write failed")

    monkeypatch.setattr("battle_engine.match_service.write_replay", fail_write)

    with pytest.raises(OSError, match="canonical write failed"):
        NativeMatchService().run(
            MatchRequest(_config(), entrants, 5, replay, False)
        )

    assert not replay.exists()
    assert not summary.exists()
    assert not replay.with_name("result.json").exists()
    assert not list(tmp_path.glob(".replay.jsonl.*.tmp"))
    assert not list(tmp_path.glob(".replay.jsonl.*.canonical.tmp"))


def test_stale_prior_artifacts_are_removed_even_when_the_new_run_fails(tmp_path, monkeypatch):
    replay = tmp_path / "replay.jsonl"
    summary = tmp_path / "summary.json"
    result_json = tmp_path / "result.json"
    replay.write_text('{"stale": true}\n', encoding="utf-8")
    summary.write_text('{"stale": true}', encoding="utf-8")
    result_json.write_text('{"stale": true}', encoding="utf-8")
    entrants = _real_v2_entrants(tmp_path)

    def fail_write(_path, _records):
        raise OSError("canonical write failed")

    monkeypatch.setattr("battle_engine.match_service.write_replay", fail_write)

    with pytest.raises(OSError):
        NativeMatchService().run(
            MatchRequest(_config(), entrants, 5, replay, False)
        )

    # A failed attempt must not leave the OLD artifacts behind either --
    # they no longer describe anything real once a new attempt was made.
    assert not replay.exists()
    assert not summary.exists()
    assert not result_json.exists()
