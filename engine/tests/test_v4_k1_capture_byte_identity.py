"""V6 E2 K=1 byte-identity freeze for stable ``bytefray-rules-4``.

docs/research/v6/V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md Sec J.1 requires that
``RulesetPolicy.capture_hold_ticks == 1`` -- the value every existing
Ruleset keeps -- be *observationally identical* to V4 core capture as it
behaved before E2's multi-tick capture hold existed. That section's claim is
proven here rather than argued: the canonical replay digest, ``result_id``,
and ``match_id`` of a small, fixed V4 matrix below were recorded against the
unmodified single-tick ``python_runtime.apply_core_capture`` at baseline
``174a640`` (plus the documentation-only E2 design-review commit), and
committed *before* the capture code was changed. Every later build must
reproduce them byte for byte.

The matrix is deliberately small but covers every capture shape V4 has:

* the exploit probe mirror (``CompetentGlobalSniperProbe``'s logic from
  ``test_v4_exploit_characterization.py``, inlined here so its own source
  bytes -- and therefore every identity hash below -- are self-contained),
  a tick-1 attributed ``kill`` by Seat A;
* ``v4_claimer`` vs ``v5_scout_striker``: early (tick 4) and late
  (ticks 172-176) attributed captures;
* ``v4_local_defender`` vs ``v5_dual_team``: tick-limit ties and captures
  at ticks 4-6;

each starter pair in both seat orientations, seeds 1-3, arena 512.

What is frozen, and why exactly these values:

* ``replay_sha256`` -- SHA-256 of the canonical schema-4 replay bytes
  ``NativeMatchService`` publishes (LF-only, ``replay.write_replay``). This
  covers every tick's events (``kill``/``death`` vocabulary, order, and the
  ``by`` attribution), scores, agent snapshots, and process snapshots.
* ``result_id`` -- the canonical result identity. ``result.json``'s own raw
  bytes are deliberately *not* frozen: they carry per-execution occurrence
  metadata (``occurrence_id``, ``completed_at``, ``product_version``) that
  differs on every run by design. ``result_id`` hashes everything
  outcome-bearing in that envelope (winner, termination reason, ticks,
  score, and every entrant's termination reason/statistics/metadata).
* ``match_id`` -- the request-derived identity, pinned so a change to
  identity derivation can never masquerade as (or hide) a gameplay change.

A mismatch here is an implementation defect in the K=1 path, never
something to re-bless.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import KillDeathEvent, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import BYTEFRAY_RULESET_V4_ID

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_AGENTS = REPO_ROOT / "engine" / "src" / "battle_engine" / "data" / "starter_agents"

ARENA_SIZE = 512
PROBE_NAME_A = "k1_probe_alpha"
PROBE_NAME_B = "k1_probe_beta"

# ``CompetentGlobalSniperProbe`` (test_v4_exploit_characterization.py),
# inlined verbatim in behavior. Written with explicit LF bytes so the
# entrant source digest -- and therefore every identity below -- is the
# same on every platform.
PROBE_SOURCE = """\
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration


class CompetentGlobalSniperProbe:
    def __init__(self):
        self.context = None
        self.write_step = 0

    def reset(self, context):
        self.context = context
        self.write_step = 0

    def declare_processes(self):
        return [ProcessDeclaration(id="sniper", reach=self.context.arena_size // 2, share=1.0)]

    def act(self, obs):
        if not obs.visible_enemy_anchor_addresses:
            return AgentAction(ActionKindV2.READ, operand=0)
        enemy_core_base = obs.visible_enemy_anchor_addresses[0]
        target_cell = (enemy_core_base + self.write_step) % self.context.arena_size
        self.write_step = (self.write_step + 1) % 8
        return AgentAction(ActionKindV2.WRITE, operand=target_cell, value=1)


def create_agent():
    return CompetentGlobalSniperProbe()
"""


@dataclass(frozen=True)
class FrozenMatch:
    seat_a: str
    seat_b: str
    seed: int
    max_ticks: int
    # Human-readable outcome, asserted first so a regression reports *what*
    # changed before the opaque digests do.
    winner: str
    ticks: int
    termination_reason: str
    capture_events: tuple[tuple[int, str, str, str | None], ...]
    replay_sha256: str
    result_id: str
    match_id: str

    @property
    def label(self) -> str:
        return f"{self.seat_a}-vs-{self.seat_b}-s{self.seed}"


# Recorded against the unmodified single-tick capture implementation (see
# module docstring). ``capture_events`` rows are
# ``(tick, event_type, victim, killer)`` for every ``kill``/``death`` event.
FROZEN_V4_K1_CORPUS: tuple[FrozenMatch, ...] = (
    FrozenMatch(
        seat_a='k1_probe_alpha',
        seat_b='k1_probe_beta',
        seed=1,
        max_ticks=200,
        winner='A',
        ticks=1,
        termination_reason='last_agent_standing',
        capture_events=((1, 'kill', 'B', 'A'),),
        replay_sha256='1b7681b54e6bb7b3a0a70b593171911077980dfd773eff73988886b7a994ec7a',
        result_id='result_d8a9c2dc27a3b14694bcce18',
        match_id='match_247eafff5b78eca9ae2caf85',
    ),
    FrozenMatch(
        seat_a='k1_probe_alpha',
        seat_b='k1_probe_beta',
        seed=2,
        max_ticks=200,
        winner='A',
        ticks=1,
        termination_reason='last_agent_standing',
        capture_events=((1, 'kill', 'B', 'A'),),
        replay_sha256='6262e316d92dcfcd0c5eb1bff67c928d00d8c7fed1a1c61266df6980adc9c402',
        result_id='result_bd289efcc9c35cdb78e3a5d5',
        match_id='match_1751d9d32dd68b09817f0b90',
    ),
    FrozenMatch(
        seat_a='k1_probe_alpha',
        seat_b='k1_probe_beta',
        seed=3,
        max_ticks=200,
        winner='A',
        ticks=1,
        termination_reason='last_agent_standing',
        capture_events=((1, 'kill', 'B', 'A'),),
        replay_sha256='0d8384d2f7d37cc8b14c84cb92b4f97fac72fc0bdd2d260a8a1afbfef1736d18',
        result_id='result_27876aa3f2f9fa5f16e5ec63',
        match_id='match_e943e1d2af75b0ceadc8a2e4',
    ),
    FrozenMatch(
        seat_a='v4_claimer',
        seat_b='v5_scout_striker',
        seed=1,
        max_ticks=200,
        winner='B',
        ticks=176,
        termination_reason='last_agent_standing',
        capture_events=((176, 'kill', 'A', 'B'),),
        replay_sha256='c0449c23187aec464e2ff2126ace31d3132ac6d94afde1c13c3910cae3cca13c',
        result_id='result_44aebb626bf7156d66930414',
        match_id='match_f8479ed11e5bfb00bbc1aca8',
    ),
    FrozenMatch(
        seat_a='v4_claimer',
        seat_b='v5_scout_striker',
        seed=2,
        max_ticks=200,
        winner='B',
        ticks=4,
        termination_reason='last_agent_standing',
        capture_events=((4, 'kill', 'A', 'B'),),
        replay_sha256='5c3e99ba4a585d12b768879f536c741475b1c5fe905d79e8e602ae64781d810d',
        result_id='result_cc0a6138379aa08599f893ac',
        match_id='match_64f7439017791134c7f17c69',
    ),
    FrozenMatch(
        seat_a='v4_claimer',
        seat_b='v5_scout_striker',
        seed=3,
        max_ticks=200,
        winner='B',
        ticks=4,
        termination_reason='last_agent_standing',
        capture_events=((4, 'kill', 'A', 'B'),),
        replay_sha256='b96e3f5c6e65f00abfe63d1bb3214dd51f79326b2e792fd533a4ffa30fdf8ad8',
        result_id='result_20a288b4d4c371180a1609c1',
        match_id='match_f054f5f0cdbfb4e5eba86dc0',
    ),
    FrozenMatch(
        seat_a='v5_scout_striker',
        seat_b='v4_claimer',
        seed=1,
        max_ticks=200,
        winner='A',
        ticks=172,
        termination_reason='last_agent_standing',
        capture_events=((172, 'kill', 'B', 'A'),),
        replay_sha256='b6cd53d9dc61d299ddde1396944ad9d7c6824349743b7883e4d5b6c6e86aa7c7',
        result_id='result_274e72f27ec55e9d46816833',
        match_id='match_dec5f562b9de3a749de23c6b',
    ),
    FrozenMatch(
        seat_a='v5_scout_striker',
        seat_b='v4_claimer',
        seed=2,
        max_ticks=200,
        winner='A',
        ticks=4,
        termination_reason='last_agent_standing',
        capture_events=((4, 'kill', 'B', 'A'),),
        replay_sha256='aa2df862e66699716201818a3ceca9d12ecb34ac4700a3e2c2180f32ed6cc479',
        result_id='result_81e098a3dd89fce7deba71e4',
        match_id='match_84d55e9114d7217ea0b5b27e',
    ),
    FrozenMatch(
        seat_a='v5_scout_striker',
        seat_b='v4_claimer',
        seed=3,
        max_ticks=200,
        winner='A',
        ticks=173,
        termination_reason='last_agent_standing',
        capture_events=((173, 'kill', 'B', 'A'),),
        replay_sha256='b79cd84b027ebe65e04a0a2f3c511507d6dd1f3d17870f0b437c17d553847bf3',
        result_id='result_0bba3cdea579d42407d88d91',
        match_id='match_1fd91db60fe4d183a6955fe6',
    ),
    FrozenMatch(
        seat_a='v4_local_defender',
        seat_b='v5_dual_team',
        seed=1,
        max_ticks=200,
        winner='tie',
        ticks=200,
        termination_reason='tick_limit',
        capture_events=(),
        replay_sha256='fc5eb5a88da0a03541219963ded5165ecf0b25327f2a67ece7ec4c4db5cae4a9',
        result_id='result_8b6e3917135fd3eece154636',
        match_id='match_1d57f236d2bd4509a4b53a02',
    ),
    FrozenMatch(
        seat_a='v4_local_defender',
        seat_b='v5_dual_team',
        seed=2,
        max_ticks=200,
        winner='B',
        ticks=4,
        termination_reason='last_agent_standing',
        capture_events=((4, 'kill', 'A', 'B'),),
        replay_sha256='621ec7c5e7fce87eab2b958ea99e6dc338789b5619b263aed3d5a663a130ddb0',
        result_id='result_d224b6f071520eece8b2ee01',
        match_id='match_6337d5502b0973c0fd3f3d93',
    ),
    FrozenMatch(
        seat_a='v4_local_defender',
        seat_b='v5_dual_team',
        seed=3,
        max_ticks=200,
        winner='tie',
        ticks=200,
        termination_reason='tick_limit',
        capture_events=(),
        replay_sha256='8845b3c9cda0cf459815dade2aad0c9f6036582bedbe49edfe4751d1f38b006e',
        result_id='result_391942f78eb311600c499c5b',
        match_id='match_124aae45d25ea8607c8492b5',
    ),
    FrozenMatch(
        seat_a='v5_dual_team',
        seat_b='v4_local_defender',
        seed=1,
        max_ticks=200,
        winner='A',
        ticks=6,
        termination_reason='last_agent_standing',
        capture_events=((6, 'kill', 'B', 'A'),),
        replay_sha256='1c0d84d7500f4a2c3c59411ad964a1ad979224430324f4fba58ff2c401030c06',
        result_id='result_cff81be0ca8eff62d337b355',
        match_id='match_f1107891f849b83d9efe90a0',
    ),
    FrozenMatch(
        seat_a='v5_dual_team',
        seat_b='v4_local_defender',
        seed=2,
        max_ticks=200,
        winner='A',
        ticks=5,
        termination_reason='last_agent_standing',
        capture_events=((5, 'kill', 'B', 'A'),),
        replay_sha256='6c96c9b2180294d21a502f8db109cf262995e9a402c688f81ee4de80cbc65252',
        result_id='result_605abec700666e2fb6c69e1b',
        match_id='match_6a88b6ea79e0f5cd753e72bb',
    ),
    FrozenMatch(
        seat_a='v5_dual_team',
        seat_b='v4_local_defender',
        seed=3,
        max_ticks=200,
        winner='A',
        ticks=6,
        termination_reason='last_agent_standing',
        capture_events=((6, 'kill', 'B', 'A'),),
        replay_sha256='e8ec428148020b5515c937de09bcac29699972b4d50a53d119911d9e2d4bc573',
        result_id='result_87834dd337e6b627dc3c1b0c',
        match_id='match_dfec9278adc61791d5be750c',
    ),
)


def _write_probe(root: Path, name: str) -> None:
    agent_dir = root / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "agent.yaml").write_bytes(
        (
            f'{{"name": "{name}", "kind": "python", "api_version": 2, '
            '"entrypoint": "agent.py:create_agent", "version": "1.0.0"}\n'
        ).encode()
    )
    (agent_dir / "agent.py").write_bytes(PROBE_SOURCE.encode())


def _install_agent(root: Path, name: str) -> None:
    if (root / "agents" / name).exists():
        return
    if name in (PROBE_NAME_A, PROBE_NAME_B):
        _write_probe(root, name)
        return
    shutil.copytree(
        STARTER_AGENTS / name,
        root / "agents" / name,
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def run_corpus_match(
    root: Path, seat_a: str, seat_b: str, seed: int, max_ticks: int
) -> tuple[FrozenMatch, Path]:
    """Run one corpus match under stable V4 and describe it as a FrozenMatch."""

    for name in (seat_a, seat_b):
        _install_agent(root, name)
    spec_a = resolve_agent(root, seat_a)
    spec_b = resolve_agent(root, seat_b)
    starts = resolve_direct_match_starts(
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
        arena_size=ARENA_SIZE,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    replay_path = root / "runs" / f"{seat_a}-vs-{seat_b}-s{seed}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    request = MatchRequest(
        config=Config(seed=seed, arena_size=ARENA_SIZE, instr_per_tick=8),
        entrants=(
            MatchEntrant.python("A", seat_a, starts[0], spec_a),
            MatchEntrant.python("B", seat_b, starts[1], spec_b),
        ),
        max_ticks=max_ticks,
        replay_path=replay_path,
        verbose=False,
        ruleset_id=BYTEFRAY_RULESET_V4_ID,
    )
    result = NativeMatchService().run(request)
    assert result.result_id is not None and result.match_id is not None
    capture_events = tuple(
        (record.tick, event.event_type, event.victim, event.killer)
        for record in iter_replay(replay_path)
        if isinstance(record, TickSnapshot)
        for event in record.events
        if isinstance(event, KillDeathEvent)
    )
    observed = FrozenMatch(
        seat_a=seat_a,
        seat_b=seat_b,
        seed=seed,
        max_ticks=max_ticks,
        winner=result.winner,
        ticks=result.ticks_run,
        termination_reason=result.termination_reason.value,
        capture_events=capture_events,
        replay_sha256=hashlib.sha256(replay_path.read_bytes()).hexdigest(),
        result_id=result.result_id,
        match_id=result.match_id,
    )
    return observed, replay_path


def corpus_cases() -> tuple[tuple[str, str, int, int], ...]:
    """The fixed matrix: (seat_a, seat_b, seed, max_ticks)."""

    cases: list[tuple[str, str, int, int]] = []
    for seed in (1, 2, 3):
        cases.append((PROBE_NAME_A, PROBE_NAME_B, seed, 200))
    for first, second in (
        ("v4_claimer", "v5_scout_striker"),
        ("v4_local_defender", "v5_dual_team"),
    ):
        for seat_a, seat_b in ((first, second), (second, first)):
            for seed in (1, 2, 3):
                cases.append((seat_a, seat_b, seed, 200))
    return tuple(cases)


def test_frozen_corpus_covers_the_declared_matrix() -> None:
    assert [
        (case.seat_a, case.seat_b, case.seed, case.max_ticks) for case in FROZEN_V4_K1_CORPUS
    ] == list(corpus_cases())


def test_frozen_corpus_exercises_attributed_core_capture() -> None:
    # Guard: the corpus must actually contain V4 core captures, including the
    # tick-1 probe-mirror kill, or its identity would say nothing about the
    # capture path E2 changes.
    kills = [event for case in FROZEN_V4_K1_CORPUS for event in case.capture_events]
    assert (1, "kill", "B", "A") in kills
    assert all(event_type == "kill" and by is not None for _, event_type, _, by in kills)
    assert {case.termination_reason for case in FROZEN_V4_K1_CORPUS} == {
        "last_agent_standing",
        "tick_limit",
    }


@pytest.mark.parametrize("frozen", FROZEN_V4_K1_CORPUS, ids=lambda case: case.label)
def test_v4_k1_capture_is_byte_identical_to_the_pre_e2_freeze(
    tmp_path: Path, frozen: FrozenMatch
) -> None:
    observed, _ = run_corpus_match(
        tmp_path, frozen.seat_a, frozen.seat_b, frozen.seed, frozen.max_ticks
    )
    assert (observed.winner, observed.ticks, observed.termination_reason) == (
        frozen.winner,
        frozen.ticks,
        frozen.termination_reason,
    )
    assert observed.capture_events == frozen.capture_events
    assert observed.match_id == frozen.match_id
    assert observed.result_id == frozen.result_id
    assert observed.replay_sha256 == frozen.replay_sha256
