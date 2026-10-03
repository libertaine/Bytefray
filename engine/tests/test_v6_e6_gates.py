"""V6 E6: the E6-D gates (D-1, D-2, D-4, D-7), CQ-1, and the seed tooling (D-6).

D-1's independent re-derivation is checked against the engine on scripted,
non-family multi-process agents, under every E6 condition's Ruleset and both
lambda values. The scenarios are chosen to exercise hits, suppression, quota
redistribution, the wrap, and reaches both above and below 32. Every other
gate is exercised on hand-built summaries, cells and replay lines. No family
member plays, and no seed used here is a matrix seed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.replay import TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
    RULESET_V6_RESEARCH_SCALE,
)

from tools.research.v6.e6 import family, gates, rederive, seeds, telemetry, traces

# (Ruleset, detection radius, lambda) -- the four E6 conditions' Rulesets.
CONDITIONS = (
    (BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID, None, None),
    (BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, 32, None),
    (BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID, None, 1),
    (BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID, 32, 1),
)

AGENT_TEMPLATE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

SHARES = {shares!r}
REACH = {reach!r}
STEP = {step!r}


class Agent:
    def reset(self, context):
        self.flip = context.rng.randrange(2)
        self.tick = -1
        self.n = 0

    def declare_processes(self):
        return [ProcessDeclaration(f"p{{i}}", REACH[i], share) for i, share in enumerate(SHARES)]

    def act(self, observation):
        if observation.current_tick != self.tick:
            self.tick = observation.current_tick
            self.n = 0
        self.n += 1
        visible = observation.visible_enemy_anchor_addresses
        if visible and (self.n + self.flip) % 2 == 0:
            return AgentAction(ActionKindV2.WRITE, visible[(self.n // 2) % len(visible)], 1)
        if observation.self_process_id == "p0" and (self.n + self.tick) % 3:
            return AgentAction(ActionKindV2.MOVE, STEP)
        return AgentAction(ActionKindV2.READ, observation.self_anchor)


def create_agent():
    return Agent()
"""

# (name, shares, reaches, step): a SPLIT-like pair, an even pair and a single process.
SCOUTS = {
    "split_up": ([0.25, 0.75], [256, 20], 16),
    "split_down": ([0.25, 0.75], [256, 40], -16),
    "even_down": ([0.5, 0.5], [256, 256], -24),
    "solo_up": ([1.0], [256], 40),
}
# (seat A agent, seat B agent, starts): converging, and across the wrap.
SCENARIOS = (
    ("split_up", "split_down", (100, 260)),
    ("even_down", "split_up", (40, 420)),
    ("solo_up", "even_down", (470, 90)),
)


def _write(root: Path, name: str) -> None:
    shares, reach, step = SCOUTS[name]
    directory = root / "agents" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "agent.yaml").write_text(json.dumps({
        "name": name, "kind": "python", "api_version": 2, "entrypoint": "agent.py:create_agent",
        "version": "1.0.0"}), encoding="utf-8")
    (directory / "agent.py").write_text(AGENT_TEMPLATE.format(shares=shares, reach=reach, step=step),
                                        encoding="utf-8")


@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> dict[tuple[str, int, int], dict[str, Any]]:
    root = tmp_path_factory.mktemp("e6-d1")
    for name in SCOUTS:
        _write(root, name)
    out: dict[tuple[str, int, int], dict[str, Any]] = {}
    for ruleset_id, _radius, _slot in CONDITIONS:
        for index, (a, b, starts) in enumerate(SCENARIOS):
            for seed in (3, 4):
                run = root / "runs" / f"{ruleset_id}-{index}-{seed}"
                result = NativeMatchService().run(MatchRequest(
                    config=Config(seed=seed, arena_size=512, instr_per_tick=8),
                    entrants=(MatchEntrant.python("A", a, starts[0], resolve_agent(root, a)),
                              MatchEntrant.python("B", b, starts[1], resolve_agent(root, b))),
                    max_ticks=40, replay_path=run / "replay.jsonl", verbose=False, ruleset_id=ruleset_id,
                    trace_path=run / "trace.jsonl"))
                extraction = telemetry.extract(traces.iter_trace(run / "trace.jsonl"), arena=512,
                                               start=telemetry.tick_zero(run / "replay.jsonl"))
                disrupted = any(p.disrupted for r in iter_replay(run / "replay.jsonl")
                                if isinstance(r, TickSnapshot) for p in r.processes)
                out[(ruleset_id, index, seed)] = {"rows": extraction.rows, "summary": extraction.summary,
                                                  "ticks": result.ticks_run, "disrupted": disrupted}
    return out


def _check(data: dict[str, Any], *, radius: int | None, slot: int | None) -> rederive.CellCheck:
    return rederive.rederive_cell(data["rows"], data["summary"], ticks_run=data["ticks"], arena=512,
                                  detection_radius=radius, slot_limit=slot)


# ---------------------------------------------------------------------------
# D-1
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("ruleset_id", "radius", "slot"), CONDITIONS, ids=lambda v: str(v))
def test_d1_rederivation_agrees_with_the_engine(played: dict[Any, dict[str, Any]], ruleset_id: str,
                                                radius: int | None, slot: int | None) -> None:
    for (rid, index, seed), data in played.items():
        if rid != ruleset_id:
            continue
        check = _check(data, radius=radius, slot=slot)
        assert check.passed, (index, seed, check.samples)
        assert check.callbacks == len(data["rows"]) > 0


def test_the_scenarios_exercise_hits_under_every_ruleset(played: dict[Any, dict[str, Any]]) -> None:
    for ruleset_id, _radius, _slot in CONDITIONS:
        assert any(data["disrupted"] for (rid, _, _), data in played.items() if rid == ruleset_id), ruleset_id


def test_d1_fails_if_declared_reach_is_used_under_the_treatment(played: dict[Any, dict[str, Any]]) -> None:
    for ruleset_id, radius, slot in CONDITIONS:
        if radius is None:
            continue
        mismatched = [_check(data, radius=None, slot=slot).visibility_mismatches
                      for (rid, _, _), data in played.items() if rid == ruleset_id]
        assert sum(mismatched) > 0, ruleset_id


def test_d1_fails_if_the_radius_is_applied_under_a_control(played: dict[Any, dict[str, Any]]) -> None:
    for ruleset_id, radius, slot in CONDITIONS:
        if radius is not None:
            continue
        assert sum(_check(data, radius=32, slot=slot).visibility_mismatches
                   for (rid, _, _), data in played.items() if rid == ruleset_id) > 0


def test_d1_fails_under_the_wrong_lambda(played: dict[Any, dict[str, Any]]) -> None:
    for ruleset_id, radius, slot in CONDITIONS:
        wrong = None if slot == 1 else 1
        assert any(not _check(data, radius=radius, slot=wrong).passed
                   for (rid, _, _), data in played.items() if rid == ruleset_id), ruleset_id


def test_d1_fails_with_exclusive_distance(played: dict[Any, dict[str, Any]]) -> None:
    # A mutant '<' for '<=' must be seen: shrinking every radius by one does it.
    failures = 0
    for (rid, _, _), data in played.items():
        if rid == BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID:
            failures += _check(data, radius=31, slot=None).visibility_mismatches
    assert failures > 0


def test_d1_fails_on_a_tampered_trace(played: dict[Any, dict[str, Any]]) -> None:
    data = played[(BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, 0, 3)]
    rows = [list(row) for row in data["rows"]]
    visible = telemetry.ROW_FIELDS.index("visible")
    rows[5][visible] = [*rows[5][visible], 7]
    assert _check({**data, "rows": rows}, radius=32, slot=None).visibility_mismatches == 1
    anchor = telemetry.ROW_FIELDS.index("anchor")
    moved = [list(row) for row in data["rows"]]
    moved[3][anchor] = (moved[3][anchor] + 1) % 512
    assert not _check({**data, "rows": moved}, radius=32, slot=None).passed
    assert _check({**data, "rows": data["rows"][:-1]}, radius=32, slot=None).alignment_failures == 1


def test_offer_order_matches_the_engine_scheduler() -> None:
    class State:
        def __init__(self, name: str) -> None:
            self.name, self.alive = name, True

    for tick in range(1, 5):
        seen: list[str] = []
        RULESET_V6_RESEARCH_SCALE.run_scheduler([State("A"), State("B")], 8,
                                                lambda state, _slot, seen=seen: seen.append(state.name), tick=tick)
        assert list(rederive.offer_order(tick, ["A", "B"])) == seen


def test_largest_remainder_quotas() -> None:
    P = rederive._Process
    from fractions import Fraction
    both = [P("A", "sensor", 256, Fraction(1, 4), 0), P("A", "striker", 256, Fraction(3, 4), 0)]
    assert rederive.largest_remainder_quotas(both) == {"sensor": 2, "striker": 6}
    assert rederive.largest_remainder_quotas(both[1:]) == {"striker": 8}
    thirds = [P("A", name, 1, Fraction(1, 3), 0) for name in ("a", "b", "c")]
    assert rederive.largest_remainder_quotas(thirds) == {"a": 3, "b": 3, "c": 2}
    assert rederive.largest_remainder_quotas([]) == {}


# ---------------------------------------------------------------------------
# D-2, D-4 (hand-built summaries)
# ---------------------------------------------------------------------------


def _line(anchors: dict[str, dict[str, int]], d4: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"schedule_id": "cell", "summary": {"tick0_anchors": anchors, "d4_writes": d4 or []}}


def test_d2_passes_beyond_thirty_two_and_fails_at_it() -> None:
    assert gates.d2_initial_invisibility([_line({"A": {"main": 100}, "B": {"main": 133}})], arena=512)["status"] == "PASS"
    report = gates.d2_initial_invisibility([_line({"A": {"main": 100}, "B": {"main": 132}})], arena=512)
    assert (report["status"], report["closest_distance"]) == ("FAIL", 32)
    wrap = gates.d2_initial_invisibility([_line({"A": {"main": 500}, "B": {"s": 20, "t": 300}})], arena=512)
    assert wrap["status"] == "FAIL"  # 500 <-> 20 is 32 across the wrap
    assert gates.d2_initial_invisibility([], arena=512)["status"] == "FAIL"  # nothing checked is no pass


def test_d4_fails_on_a_planted_blind_core_write() -> None:
    informed = {"order": 3, "tick": 1, "entrant": "A", "address": 300, "informed": True}
    blind = {**informed, "informed": False}
    assert gates.d4_no_early_blind_strike([_line({}, [informed])])["status"] == "PASS"
    report = gates.d4_no_early_blind_strike([_line({}, [informed]), _line({}, [blind])])
    assert (report["status"], report["failures"]) == ("FAIL", 1)


# ---------------------------------------------------------------------------
# D-7 (hand-built mirror cells and replay lines)
# ---------------------------------------------------------------------------


def _mirror_cells(root: Path, member: str, seed: int, *, same: bool = True, seat: str = "A") -> list[dict[str, Any]]:
    primary, twin = family.package_id(member), family.package_id(member, "twin")
    cells = []
    for orientation in ("candidate_first", "opponent_first"):
        artifact = f"{primary}-{seed}-{orientation}"
        (root / artifact).mkdir(parents=True, exist_ok=True)
        extra = "" if same or orientation == "candidate_first" else "x"
        (root / artifact / "replay.jsonl").write_text(
            '{"record_type": "header"}\n' + f'{{"record_type": "tick", "tick": 1, "k": "{extra}"}}\n',
            encoding="utf-8")
        subject_is_a = orientation == "candidate_first"
        outcome = "win" if (seat == "A") == subject_is_a else "loss"
        cells.append({"subject_id": primary, "opponent_id": twin, "orientation": orientation, "seed": seed,
                      "artifact_dir": artifact, "outcome": outcome})
    return cells


def test_d7_passes_on_relabelings_and_fails_otherwise(tmp_path: Path) -> None:
    good = _mirror_cells(tmp_path, "RUSH", 5) + _mirror_cells(tmp_path, "GUARD", 5)
    assert gates.d7_mirror_relabeling(tmp_path, good, expected_units=2)["status"] == "PASS"
    assert gates.d7_mirror_relabeling(tmp_path, good, expected_units=3)["status"] == "FAIL"
    ticks = _mirror_cells(tmp_path / "t", "RUSH", 6, same=False)
    assert gates.d7_mirror_relabeling(tmp_path / "t", ticks, expected_units=1)["failure_samples"][0]["reason"] == (
        "tick records")
    seat = _mirror_cells(tmp_path / "s", "RUSH", 7)
    seat[1] = {**seat[1], "outcome": "win"}  # the same entrant wins from the other seat
    assert gates.d7_mirror_relabeling(tmp_path / "s", seat, expected_units=1)["status"] == "FAIL"
    assert gates.d7_mirror_relabeling(tmp_path, good[:1], expected_units=1)["status"] == "FAIL"


# ---------------------------------------------------------------------------
# CQ-1 (hand-built summaries: callback-stream digests)
# ---------------------------------------------------------------------------


def _cq1_lines(digest: Any) -> list[dict[str, Any]]:
    lines = []
    for a in family.OPPONENTS:
        for b in family.OPPONENTS:
            if a == b:
                continue
            for seed in (1, 2):
                lines.append({"seat_a": family.package_id(a), "seat_b": family.package_id(b), "seed": seed,
                              "rows_sha256": digest(a, b, seed)})
    return lines


def _stream(a: str, b: str, seed: int) -> str:
    """A digest that ignores which search variant sits in either seat."""
    group = set(gates.SEARCH_VARIANTS)
    names = ["S" if m in group else m for m in (a, b)]
    return hashlib.sha256(f"{names}|{seed}".encode()).hexdigest()


def test_cq1_passes_when_search_variants_play_identically() -> None:
    report = gates.cq1_search_inertness(_cq1_lines(_stream))
    assert report["status"] == "PASS"
    # 6 variant pairs x 7 opponents x 2 seeds x 2 seats
    assert report["checked"] == 6 * 7 * 2 * 2


def test_cq1_fails_when_a_search_parameter_leaks_into_control_play() -> None:
    def leaky(a: str, b: str, seed: int) -> str:
        return _stream(a, b, seed) + ("x" if a == "STEALTH" and b == "GUARD" else "")
    report = gates.cq1_search_inertness(_cq1_lines(leaky))
    # STEALTH v GUARD against each of the three other variants, at both seeds.
    assert report["status"] == "FAIL" and report["failures"] == 3 * 2


def test_cq1_compares_streams_not_outcomes() -> None:
    # Same (synthetic) outcome everywhere, but one stream differs: CQ-1 must fail.
    def one_off(a: str, b: str, seed: int) -> str:
        return _stream(a, b, seed) + ("y" if (a, b, seed) == ("LURK", "GREED", 2) else "")
    assert gates.cq1_search_inertness(_cq1_lines(one_off))["status"] == "FAIL"


def test_cq1_fails_on_a_missing_cell() -> None:
    lines = [line for line in _cq1_lines(_stream)
             if (line["seat_a"], line["seat_b"]) != (family.package_id("PACED"), family.package_id("ADAPT"))]
    assert gates.cq1_search_inertness(lines)["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D-6 and the seed tooling (a fixed test list, never the matrix's)
# ---------------------------------------------------------------------------

TEST_SEEDS = [(7919 * k * k + 104729 * k + 13) % seeds.SEED_BOUND for k in range(1, 33)]


def test_the_test_list_is_valid() -> None:
    assert len(set(TEST_SEEDS)) == 32 and all(0 <= s < 2**53 for s in TEST_SEEDS)


def test_golden_encoding_and_commitment() -> None:
    data = seeds.encode(TEST_SEEDS)
    assert data.startswith(f"{TEST_SEEDS[0]}\n".encode()) and data.endswith(b"\n") and b"\r" not in data
    assert data.count(b"\n") == 32
    assert seeds.commitment(TEST_SEEDS) == hashlib.sha256(data).hexdigest()
    assert seeds.decode(data) == TEST_SEEDS
    golden = seeds.encode(list(range(1, 33)))
    assert golden == "".join(f"{n}\n" for n in range(1, 33)).encode()
    assert seeds.commitment(list(range(1, 33))) == hashlib.sha256(golden).hexdigest()


@pytest.mark.parametrize("bad", [
    lambda s: s[:-1], lambda s: [*s[:-1], s[0]], lambda s: [*s[:-1], 2**53], lambda s: [*s[:-1], -1],
    lambda s: [*s[:-1], True], lambda s: [*s[:-1], 3.0],
])
def test_invalid_lists_are_rejected(bad: Any) -> None:
    with pytest.raises(seeds.SeedProtocolError):
        seeds.encode(bad(TEST_SEEDS))


@pytest.mark.parametrize("data", [b"1\r\n", b"01\n", b"+1\n", b" 1\n", b"1", b"1\n\n"])
def test_non_canonical_bytes_are_rejected(data: bytes) -> None:
    with pytest.raises(seeds.SeedProtocolError):
        seeds.decode(data, count=1)


def test_verify_fails_on_reorder_and_change() -> None:
    committed = seeds.commitment(TEST_SEEDS)
    assert seeds.verify(TEST_SEEDS, committed)
    assert not seeds.verify([TEST_SEEDS[1], TEST_SEEDS[0], *TEST_SEEDS[2:]], committed)
    assert not seeds.verify([TEST_SEEDS[0] + 1, *TEST_SEEDS[1:]], committed)


def test_generate_rejects_duplicates_and_respects_the_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    drawn = iter([5, 5, 9, 2**53 - 1, 9, 0])
    bounds: list[int] = []

    def fake(bound: int) -> int:
        bounds.append(bound)
        return next(drawn)

    monkeypatch.setattr(seeds.secrets, "randbelow", fake)
    assert seeds.generate(4) == [5, 9, 2**53 - 1, 0]
    assert set(bounds) == {2**53}


def test_execution_identity() -> None:
    structural, committed = "a" * 64, seeds.commitment(TEST_SEEDS)
    expected = hashlib.sha256(f"{structural}\n{committed}\n".encode()).hexdigest()[:12]
    assert seeds.execution_identity(structural, committed) == f"v6-e6-exec-v1-{expected}"
    with pytest.raises(seeds.SeedProtocolError):
        seeds.execution_identity("A" * 64, committed)


def test_private_storage_refuses_overwrite_and_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "seeds.private.txt"
    committed = seeds.write_private(TEST_SEEDS, path)
    assert seeds.load_private(committed, path) == TEST_SEEDS
    with pytest.raises(seeds.SeedProtocolError):
        seeds.write_private(TEST_SEEDS, path)
    with pytest.raises(seeds.SeedProtocolError):
        seeds.load_private("0" * 64, path)
    assert seeds.PRIVATE_SEEDS_PATH.parts[-3:] == ("runs", "research_v6_e6", "seeds.private.txt")


def test_d6_passes_only_when_everything_matches() -> None:
    structural = "b" * 64
    committed = seeds.commitment(TEST_SEEDS)
    identity = seeds.execution_identity(structural, committed)
    data = seeds.encode(TEST_SEEDS)
    ok = seeds.d6(data, committed=committed, structural_digest=structural, committed_execution_identity=identity,
                  cell_seeds=TEST_SEEDS[:5])
    assert ok["status"] == "PASS"
    assert seeds.d6(data, committed="0" * 64, structural_digest=structural, committed_execution_identity=identity,
                    cell_seeds=[])["status"] == "FAIL"
    assert seeds.d6(data, committed=committed, structural_digest=structural,
                    committed_execution_identity="v6-e6-exec-v1-000000000000", cell_seeds=[])["status"] == "FAIL"
    off = seeds.d6(data, committed=committed, structural_digest=structural, committed_execution_identity=identity,
                   cell_seeds=[1])
    assert off["status"] == "FAIL" and off["off_list_seeds"] == [1]
    assert seeds.d6(data + b"x\n", committed=committed, structural_digest=structural,
                    committed_execution_identity=identity, cell_seeds=[])["checks"]["canonical"] is False


def test_the_gate_report_shape() -> None:
    report = gates._report("X", 3, [])
    assert (report["status"], report["checked"]) == ("PASS", 3)
    assert gates._report("X", 0, [])["status"] == "FAIL"


# ---------------------------------------------------------------------------
# D-1, D-2, D-4 at field level: a traced evaluation field of scripted scouts
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def scout_field(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list[traces.TraceRecord], dict[str, Any]]:
    from battle_engine.agent_evaluation import EvaluationRequest, EvaluationService

    root = tmp_path_factory.mktemp("e6-scout-field")
    env = root / "env"
    for name in ("split_up", "split_down"):
        _write(env, name)
    field = root / "field"
    EvaluationService().run(EvaluationRequest(
        candidate_id="split_up", opponent_ids=["split_down"], seeds=(3, 4, 5), ticks=40, arena_size=512,
        ruleset_id=BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
        output_dir=field / "arena_512" / "00-split_up", data_root=env))
    records = traces.trace_field(field, data_root=env, ticks=40, arena_size=512, expected_cells=6)
    telemetry.telemetry_field(field, records, arena=512)
    state = json.loads((field / "arena_512" / "00-split_up" / "evaluation.json").read_text(encoding="utf-8"))
    cells = {cell["schedule_id"]: cell for cell in state["cells"]}
    return field, records, cells


def test_field_level_d1_passes_and_fails_under_the_wrong_lambda(
    scout_field: tuple[Path, list[traces.TraceRecord], dict[str, Any]]
) -> None:
    field, records, cells = scout_field
    report = gates.d1_visibility(field, records, cells, arena=512, slot_limit=1)
    assert (report["status"], report["checked"]) == ("PASS", 6) and report["callbacks"] > 0
    assert gates.d1_visibility(field, records, cells, arena=512, slot_limit=None)["status"] == "FAIL"
    assert gates.d1_visibility(field, records, cells, arena=512, slot_limit=1, detection_radius=256)["status"] == "FAIL"


def test_field_level_d2_and_d4_pass_on_real_summaries(
    scout_field: tuple[Path, list[traces.TraceRecord], dict[str, Any]]
) -> None:
    field, _, _ = scout_field
    summaries = telemetry.read_summaries(field)
    d2 = gates.d2_initial_invisibility(summaries, arena=512)
    assert d2["status"] == "PASS" and d2["closest_distance"] >= 64
    assert gates.d4_no_early_blind_strike(summaries)["status"] == "PASS"
