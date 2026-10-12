"""V6 E5 parent byte-identity freeze: default spawn as it behaved before E5.

E5 (anchor/core-0 separation,
docs/research/v6/V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md Sec F and
docs/research/v6/V6_E5_DESIGN_REVIEW_REVISION_1.md) adds
``RulesetPolicy.initial_anchor_placement``. Its default, ``"core_base"``,
must be *observationally identical* to process spawning as it behaved before
the field existed (review Sec F, P8). That claim is proven here rather than
argued. Every value below was recorded against the unmodified runtime at
``4fbd1d4`` -- ``ecf2769`` plus the documentation-only E5 review commit --
and committed *before* any placement, policy or Ruleset code changed (review
Sec O step 2). Every later build must reproduce them byte for byte.

The matrix runs under both E5 parents, which are also E4's parents:

* ``bytefray-rules-6-research-capture-hold-k2-disruption-slot1`` -- the
  historical T-E3 Ruleset (= C-E4), parent of the primary E5 treatment
  (K=2, lambda=1);
* ``bytefray-rules-6-research-disruption-slot1`` -- the historical T-E3K1
  Ruleset (= C-E4K1), parent of the companion E5 treatment (K=1, lambda=1).

Pairings (review Sec O step 2): the contests E5 measures, in the seven-fixture
E5 field -- Global Sniper vs Minimal Guard (sweep-backed opening contest),
Disrupt-First Guard vs Guarded Painter (anchor-only opening contest), Global
Sniper vs Disrupt-First Guard (multi-pass), Pure Repair Guard vs Global
Sniper (G.5), Spread Defender vs Minimal Guard (seat-dependent core
inference), Spread Sniper vs Pure Repair Guard, and the Guarded Painter and
Minimal Guard mirrors. Each runs in both seat orientations at seeds 1-3,
arena 512 and a 1000-tick limit. 2 x 8 x 2 x 3 = 96 matches. The fixtures
are tracked and LF-only by ``.gitattributes``, so every identity below is the
same on every platform.

What is frozen is exactly E4's parent-freeze set (replay SHA-256,
``result_id``, ``match_id``, the per-tick ``cpu_used`` and memory-write
digests, and the plain outcome fields), plus one digest E5 moves first:

* ``anchors_sha256`` -- every tick's process snapshot (entrant, process,
  anchor), tick 0 included, and each entrant's recorded ``pc``. Initial
  anchor placement is exactly what E5 changes, and ``pc`` is what the capture
  analyzer rebuilds cores from, so neither may move under ``"core_base"``.

A mismatch here is an implementation defect in the ``"core_base"`` path,
never something to re-bless.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import KillDeathEvent, MatchResult, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
)

from tools.research.v6.e3.entrants import prepare_data_root

ARENA_SIZE = 512
MAX_TICKS = 1000
QUOTA = 8
SEEDS = (1, 2, 3)

# Historical T-E3 = C-E4 (primary parent) and T-E3K1 = C-E4K1 (companion parent).
T_E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
T_E3K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
RULESETS = (T_E3_ID, T_E3K1_ID)

# The review Sec O step-2 pairings, each run in both orientations.
PAIRINGS: tuple[tuple[str, str], ...] = (
    ("e2_sniper", "e2_min_guard"),
    ("e2_disrupt_guard", "e2_guarded_painter"),
    ("e2_sniper", "e2_disrupt_guard"),
    ("e2_repair_guard", "e2_sniper"),
    ("e2_spread_defender", "e2_min_guard"),
    ("e2_spread_sniper", "e2_repair_guard"),
    ("e2_guarded_painter", "e2_guarded_painter_twin"),
    ("e2_min_guard", "e2_min_guard_twin"),
)

Capture = tuple[int, str, str, str | None]


@dataclass(frozen=True)
class FrozenMatch:
    ruleset_id: str
    seat_a: str
    seat_b: str
    seed: int
    winner: str | None
    ticks: int
    reason: str
    score: tuple[float, float]
    actions: tuple[int, int]
    silenced: tuple[int, int]
    captures: tuple[Capture, ...]
    cpu_sha256: str
    writes_sha256: str
    anchors_sha256: str
    replay_sha256: str
    result_id: str
    match_id: str

    @property
    def label(self) -> str:
        return f"{self.ruleset_id}:{self.seat_a}-vs-{self.seat_b}-s{self.seed}"


def corpus_cases() -> tuple[tuple[str, str, str, int], ...]:
    """The fixed matrix: (ruleset_id, seat_a, seat_b, seed)."""

    return tuple(
        (ruleset_id, seat_a, seat_b, seed)
        for ruleset_id in RULESETS
        for first, second in PAIRINGS
        for seat_a, seat_b in ((first, second), (second, first))
        for seed in SEEDS
    )


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode("utf-8")).hexdigest()


def run_corpus_match(root: Path, ruleset_id: str, seat_a: str, seat_b: str, seed: int) -> FrozenMatch:
    """Run one corpus match and describe it as a FrozenMatch."""

    prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=ARENA_SIZE,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    replay_path = root / "runs" / f"{ruleset_id}-{seat_a}-vs-{seat_b}-s{seed}" / "replay.jsonl"
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    result = NativeMatchService().run(
        MatchRequest(
            config=Config(seed=seed, arena_size=ARENA_SIZE, instr_per_tick=QUOTA),
            entrants=(
                MatchEntrant.python("A", seat_a, starts[0], resolve_agent(root, seat_a)),
                MatchEntrant.python("B", seat_b, starts[1], resolve_agent(root, seat_b)),
            ),
            max_ticks=MAX_TICKS,
            replay_path=replay_path,
            verbose=False,
            ruleset_id=ruleset_id,
        )
    )
    assert result.result_id is not None and result.match_id is not None
    actions = {"A": 0, "B": 0}
    silenced = {"A": 0, "B": 0}
    captures: list[Capture] = []
    cpu: list[list[int]] = []
    writes: list[list[object]] = []
    anchors: list[list[object]] = []
    final: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, TickSnapshot):
            anchors.append(
                [record.tick, [[p.entrant_id, p.process_id, p.anchor] for p in record.processes]]
            )
            if record.tick == 0:
                anchors.append(["pc", [[agent.agent_id, agent.pc] for agent in record.agents]])
                continue
            used = {agent.agent_id: agent.cpu_used for agent in record.agents}
            cpu.append([record.tick, used["A"], used["B"]])
            writes.append(
                [record.tick, [[diff.address, diff.length, diff.owner] for diff in record.memory_diffs]]
            )
            for agent in record.agents:
                actions[agent.agent_id] += agent.cpu_used
                if agent.alive and agent.cpu_used == 0:
                    silenced[agent.agent_id] += 1
            captures.extend(
                (record.tick, event.event_type, event.victim, event.killer)
                for event in record.events
                if isinstance(event, KillDeathEvent)
            )
        elif isinstance(record, MatchResult):
            final = record
    assert final is not None
    return FrozenMatch(
        ruleset_id=ruleset_id,
        seat_a=seat_a,
        seat_b=seat_b,
        seed=seed,
        winner=result.winner,
        ticks=result.ticks_run,
        reason=result.termination_reason.value,
        score=(float(final.score["A"]), float(final.score["B"])),
        actions=(actions["A"], actions["B"]),
        silenced=(silenced["A"], silenced["B"]),
        captures=tuple(captures),
        cpu_sha256=_digest(cpu),
        writes_sha256=_digest(writes),
        anchors_sha256=_digest(anchors),
        replay_sha256=hashlib.sha256(replay_path.read_bytes()).hexdigest(),
        result_id=result.result_id,
        match_id=result.match_id,
    )


def _m(
    ruleset_id: str,
    seat_a: str,
    seat_b: str,
    seed: int,
    winner: str | None,
    ticks: int,
    reason: str,
    score: tuple[float, float],
    actions: tuple[int, int],
    silenced: tuple[int, int],
    captures: tuple[Capture, ...],
    cpu_sha256: str,
    writes_sha256: str,
    anchors_sha256: str,
    replay_sha256: str,
    result_id: str,
    match_id: str,
) -> FrozenMatch:
    return FrozenMatch(
        ruleset_id, seat_a, seat_b, seed, winner, ticks, reason, score, actions, silenced, captures,
        cpu_sha256, writes_sha256, anchors_sha256, replay_sha256, result_id, match_id,
    )


# Recorded against the unmodified runtime (see module docstring). One row per
# match, in ``corpus_cases()`` order. Every row's replay_sha256, result_id and
# match_id also equal the preserved C-E4 / C-E4K1 corpus cell for the same
# match (matrix v6-e4-matrix-v1-fc29d575dd25), itself byte-identical to E3's
# T-E3 / T-E3K1, so this freeze is the historical control itself, not merely a
# snapshot of the tree it was recorded on.
FROZEN_E5_PARENT_CORPUS: tuple[FrozenMatch, ...] = (
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '893b3317b21bece60ece7c7b8b9843b5a806996b7da1ddc2a9b38d33b8a2dcb6',
       '81770607915a9198be7a09ae840c85ed13374bc57f463a4c4f75ba0c955ebea3',
       'aa3d985d4d51133d3f24816dab1036223d5f4cae2531b288144ef347b5bf4f3f', 'result_e620b7512002f11cc24597fe', 'match_ccf51a7d3fec7e90fb9f66ef'),
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '4269b0fd612ee787b3603364c3d3b14da140c088c5325ba5ef56dd5d5d13a731',
       'b168e206fc0835c54ba1e609467f4f880b408daf58e0b3ba51b74098992d5c8a',
       '99cafe45d90ad771c21651bb43035c2f582079a47afe3dab634a60ed130c480a', 'result_418457b6718d8137803bdeb0', 'match_7e066782af87804564cd41aa'),
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'a80110d5f372356df028942925bf889754363334f65cb7c5e911e0ac9c57c59e',
       '6a7e2b23723658ed42f90daa9a0fd175f59e5627300c2f6721851b2ad7278b6d',
       '6f1afdcc6f0a763961ef707747c0bf01b3a71d678c87cc6ff59cbf327e703c7a', 'result_b1cc677b3aa4b65bda8dc878', 'match_9e6128c3eab8fd9a65c5f218'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '6b60219434e79540b4649543ea213fa352705d69a3b15e46e2f1589417ce281e',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       'd61f9fa6908f318563632a75d17bea72be2c8e1ed9c9e746a9049ea6ca639daa', 'result_cb0a810cf05b26fb802e277c', 'match_e35d4075c951302b6ca25c83'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd86ad09d2cb6d4cbe7b8e2fb69768752a18fa48a23d9f0ba70210f4eacbe8a8b',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '307626564976e708ae1fb484babbfb40b170e61174ceb68a31db63e85cf5951f', 'result_b7b372e701a4013042a490ae', 'match_fa212c669b1dd3fbe13271ba'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '84838e5beb85b105c201e657b2e4139ff0d45c96db0b4d8b25719c0c8c7916a7',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       '1cdb706a0e7397381443fdb606856fbbaf220f7e54d0ba59fc9546cccecdaa0b', 'result_2912fb6bbb691b45e1ce0c16', 'match_47a2a13b81434cb08fc46b6f'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 1, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000), (0, 0),
       (),
       '56e7723219e4deff368040b791ed5d71239f39e1b75e97932b47ad1e047563ea', '4316ba8bde5a6c2dfe3346875aa3ac7efaf7a8b5234708ab0b9d130a8108be33',
       'b754267b941fe60131f5102c727be56bb1b4757ffd818e6d8ce0b820e96e00cb',
       'ce3174c3d437caa9913920d71cde48dd2b7534430d9af9cbff667e1a9fcce119', 'result_79cef81202ffeb3911a2911c', 'match_f8c9a76120da3350f7033d83'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 2, 'B', 1000, 'tick_limit', (1000.0, 7655.0), (6992, 7000), (0, 0),
       (),
       '34ddd973e11ff515eba17e1a824583dd02ec2a5333d5a35daf4551bc651a3cd0', 'd057895b6bc165925a1d0e84a20408afa1701a3ae7ae7a67fb34e5803922778c',
       'e6e05674b4a0d127055e48b5af873ad05911e035e7e764b6ff94d8191c627510',
       '160fafb6de421f1a612fb1e8bb05e389f29c53bd41350eca912c4bb9b3ef2149', 'result_66e2625e5e6b4347eb000ff8', 'match_e6de08cd8a76e7cd682bf6e4'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 3, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000), (0, 0),
       (),
       'a4377f12f6deb4671ae3a1f7033d1a60d01d93e1fe07b46fceafaf21e95f0f34', '9a8f88d5814b20c9cfc77608c05791ed2beadd447e4bba142fda2d16a9bbfa0a',
       'f8291f49422037e3d28ca944c7d572cc75135d625a011d22bf90ce58ebe415ae',
       'e3081afe0b13aa805350173cb95979aaa13bea2788ddeaaedfaa77d373887fcf', 'result_f57dcde38dc8303681f84aab', 'match_33eeb7ee263e50047b70f468'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 1, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992), (0, 0),
       (),
       '4a6f1842e5517f81bbbc03d7fe1b515b02acbfc9f79680354db50e3286bf6536', 'e877496db8c4658c6df70d897e1b6f761149c07ec0770cc5255bfa1df056c370',
       '74b12b2c19437699e8eba89af5838cb5208469a48ed098f98b519c9859e2fa42',
       '7e3fe1efcc4d1170acc63ac4ac33c072cd8eaa12d4fbf890e019c97777fb063b', 'result_f1ec6a7de5b544eb62f7410c', 'match_554beb90928420542d7cab39'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 2, 'A', 1000, 'tick_limit', (7654.0, 1000.0), (7000, 6992), (0, 0),
       (),
       '0fe5b8cf1ccdc7086a8e51081118bc7bfe3e7b0765aadb6c34f634a2d85f02d7', 'e17bbbcb711fe38c17680fbe29b12b006fb6c0851fa38e91200181031f00ff3f',
       '0b574a5933ff0128ddb8a6a3de5a314f19407f29dfeb6189bd987dddd45f4256',
       'ce6893317f77f7fb2b411eb762f1eb443def5b8666726a370f506aec214be338', 'result_b02e00cf67b8d9c4ac183eda', 'match_f47d3e42bb5c47743f7edac6'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 3, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992), (0, 0),
       (),
       'd4e2f8d4eb1beef7e6b1dca53277feee6ca16ada8fa16783ef083193d9d1f486', '2a39f4b087c7e6ed233a216b9964873cdd8e62b704830b3362a6ec03ad88347e',
       '54800cd17023ff6b9ea72964d9b19f5fcf812da53c04e05037cccb280a93da02',
       '5036208ab3bc129bca1f95871b0a48e0a4b89f01b9786880ef3bf908e06948c1', 'result_319a57a4472545f80b033ecc', 'match_4b67239427420876eadb81b5'),
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd9402ec6c38d9e73f102956d3a7baac6855eac3b4c28278fa94c5c9230e6fbb5',
       '81770607915a9198be7a09ae840c85ed13374bc57f463a4c4f75ba0c955ebea3',
       '33f5c13147d386aeb496893022e79f85d177fdb7ec22490e11d843ac9d0250aa', 'result_d23c5fe02307445fc603e0c5', 'match_66e99852e9ebceebd4dfea6b'),
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '60cbef2596b9c5b6e6f5446a3438e7f294fcc7ed8ecf2ba43b58ede47a415b7b',
       'b168e206fc0835c54ba1e609467f4f880b408daf58e0b3ba51b74098992d5c8a',
       'd4823c20760765308ab8c92419afba5e0ec1620e7091e9a88d95a88742247bad', 'result_a35c430b5461443948f4c169', 'match_8fde67f081aa466cc335c223'),
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '412d63c889d737c535205b50bad1900afbe436080dee1559d8f490aa92fa2940',
       '6a7e2b23723658ed42f90daa9a0fd175f59e5627300c2f6721851b2ad7278b6d',
       '3a73b2d0b13d2de10f894dff699d6b926c0dc741e3c65bfc352b0ec3646d69dc', 'result_a41bdefaec11bde8a354ff2d', 'match_b24b69b49b3cc211bc96a4a0'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '0e3c0a4abbc455aa8b062d27fc70336ba9c5eee9e3f7f8d56b9d1370c5fc2b6f',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       'a14104fc844d9d3cc015de8daca723303b75ffb103013b23bdf788291055d8d3', 'result_c53b55859fe1fb9296604063', 'match_6c315dd3fe8ef8132e0e4550'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'f3d0804bd10cf464fb9a229f3c993bac03bb84b418d22284293efa31ad0e1296',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '5965b5add4be91bbdedf16b73deb25a0f241b6b620658dbe8cd54918a520826a', 'result_2e9841626aaa892bec068604', 'match_5139af798387c215180e5558'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'c32ba4a574b5455b6b20897cb636cca2a5b2088509c2c3c640d37418e433476a',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       '72c5ebab0abe7b08f5d5e76566328a0a7c936885ddf2dabd1c8eee55dbe710f1', 'result_584beb25c6eda0844d206ce9', 'match_63fb4509114a211f005f24af'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'af89a8fc31a4847b0354d3c6dda8b47c92ffd419b7140b7c2f6b89d86e983316',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       '5cb5ed6beec3fa72f200812c9c7421ef65dab24fc18f1b9beb210f51636d490c', 'result_a85d2483b4dc4f433a5cadbe', 'match_43d5a795867c3e723b3ef1bc'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '5704ab1bd4fafe7301bfda5a88b981cdba47df63b8df17a7972d93abf5c93ced',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '8480a4bdc4e25e04b67d86a26ea678a14d5040961f58bf5cb7ba8790f5038461', 'result_03f0174250a12d46a7d9f054', 'match_e6672e61ffcb8676a7d02cad'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '180ecc277bcc84d646e4bb5e9999682c765800737d64ae42df27a691265d0a77',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       'd862cde40738bf7136267372a701e3363ae261b5147d390a226011f81fdecba0', 'result_c4be14c63e96931463efbc50', 'match_5219a868fed6f45ca2b753b3'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'cdf0a60c2208364d2730bfef9585d130eab1f3d322c7560d6b87c8c6e2dba658',
       '81770607915a9198be7a09ae840c85ed13374bc57f463a4c4f75ba0c955ebea3',
       'c4d2e2cffbeb9e5d3ed7bf28fa8b1d3a4321ba14d1460627c94bafd47b731fc4', 'result_b5be9a0a48886271c4da33e2', 'match_53d59fd53b31acebf22fc3e2'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '455445bd762f08303970a3b635cee5a3d17b2b0a2fcd31dd7d804b2356ce3c8e',
       'b168e206fc0835c54ba1e609467f4f880b408daf58e0b3ba51b74098992d5c8a',
       '1837c1298b8ce36b43c571a03a444dbb86528937e65c4ce3768af02b2c874e1e', 'result_c097de0251edababb8cef406', 'match_077400ba3acb526fb7bb319b'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '8413564668fe798cd6449b8b44ce2f4d0a8553905f522ead1bd5b5de2cf8ac3e',
       '6a7e2b23723658ed42f90daa9a0fd175f59e5627300c2f6721851b2ad7278b6d',
       'b29ea0c2da6aef0e725e3d01ad1b94fa6fe9d324161768032f8cbfc82bdb9aa7', 'result_aa37afc8c00a6f3543cdb9c5', 'match_f53aa7e19fd827b22de19ac3'),
    _m(T_E3_ID, 'e2_spread_defender', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'acb6b219bd31f2702c0fb44ffff1da098c8220caf27016acbaf29d0086df1214',
       'f242a40f634c3c3e4be8239870e7cab06c42696c405769ac4cad50d840f8a0c2',
       '2e327576956434908bb75ab8c9a9750121d1d6d489b31f73454ee203c8dd243d', 'result_462691799d4579735466dab8', 'match_64a10613999415407767b11d'),
    _m(T_E3_ID, 'e2_spread_defender', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '410ff8005d174682fcf6825412ab6c30886716997e8f47aba02c5cd0812b14f3',
       '9f2b6f7908c49fe573ca359132a703446ab2d3b76dfe2bc9d3d520fd4764f7c0',
       'f0215ed1877111f8b884d37aefb1581bdb6d25a18f1302be87e3d77b8865338c', 'result_7bc28de5966af421b1b9b4be', 'match_4eaa8a8b53779f39938f4fba'),
    _m(T_E3_ID, 'e2_spread_defender', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '3c90999a9fc987f38515a2dd11eb2f8ed11977463b197afd283ca190b0fbd978',
       '0d83db182b8c6fb962170924811e1efb0ca429d9e8e36f3d933a5557299b9ac8',
       '85cc4eee14bed66fe4094c1aa66e256b8c43fe20d84a57520f1d6416118713a6', 'result_0fedc0f60bb9bd987745c77c', 'match_1cd8fc382caabfbb45bc08b2'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_spread_defender', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '9f25a7e69ad36859cabcb4cb5aaf04656944941c4063b2639f3d3bf652d32935',
       'f39e4b8b20326aeb13737d364aee86d570629ca3f481fe7d48cc5f8422838c31',
       '395369919847ce75d70f45e311b068195b31034a3ed43aaa3c4b150874e17d6c', 'result_eb40f355760977deabf148c6', 'match_b9b30c2f911eef1a13ba0d05'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_spread_defender', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3d67fa73d3b2ae46c813cb6a84f5d19e67760f07ac58f1d8740aebdd223f36e3',
       'f27c75dadcb314bd8b957de2dff27379ab8dae69617a378699006638ce52e888',
       'd9040ae89d2afce40b4eddb51b9d457942cf977ae0830e8fcdc91bf10c609689', 'result_6df3fc559c021bcae7121d67', 'match_6487cdd059fc7a92f9d76445'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_spread_defender', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3da80e2bf59b813ceb12d813161a21224af58639a027d495b941e0e21ec5a91e',
       '5869c154ade36d903d321372dc7833d5df8f9bbfa19d262554cee801b7deea18',
       '6a15abb6f78c970a2e5c61ec63cd592a90e92892651999ceeba650e49ccc310a', 'result_41fe4b1edf6b80bf724ba3cd', 'match_80209b8a1be79eb4bee5e869'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_repair_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '0fdd468a0e25c54757a7413a821f5af164db8a41db2803dd8f648c2a63409034',
       '53258f80cd92f84465909a77c5ef8b477decdd6115adadc925bd908da7937c5c',
       '7c9b9f795d15c551e0a89c14443486d334fb6b338dfc92f1ca73e77d80004b13', 'result_73166089490470b9a6baa957', 'match_8e5f5a657a05a28d757f4d50'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_repair_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '282f0162ae3c80938339d61ec47dc589f8dece65d34a10cc20655ea9dd7a4965',
       'c42157f4fef4ab17d68b3d7fb122619f76cd287c1b9d8ab347ffa794f145b4a4',
       '13877bb2afbd73073a070ee1e1ed620070800fd3c3eccf699c9688134851b4f3', 'result_16b29e8e2e3c24965c33b855', 'match_91d5edf3c6ec82d1272d4e8e'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_repair_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'd1a69052c0e6d79523ab817b1cd8c07cb386787d3a78af7e7de6465d21120047',
       '311d70d9335052825ed51a9a2330693468176fa712fa6effdf48211e7219342f',
       '06ba7ba7ce23ef53af0ea552a0277d6edf748269c0de5ea02b7b9aa48813f619', 'result_2e25391dcc64bf6e109b688b', 'match_d0cb1158f404752604206566'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '46da8f8a3db2e0eac196aef412f4bebc0294f49982767db320ae03c4c90c9f0c',
       '5450b5bd213d0e8e9a802942bfee47a9ec63e61815f8846a601c810cf56dd372',
       '85bf97294e12d10e95fcfbd5046faa74a62ca15bee13de223cd400a1c104af4a', 'result_de56fe543ad11e0b85626e64', 'match_fc73269910b0dd4a74eed2c5'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'bae6d8be3fa5dd786c09a628bcf798aeeafba62e42552781e565d5f32fb0a93f',
       'e1cd721f6c896fb041d33984e52ab9542392d1bf7d4be51da98c7a3aae46efca',
       '7377ccb4ce1b9ea6d78302569797677c670030ea722d123f7f81327c9b920e4c', 'result_a8e7864a5e611e9062776424', 'match_c1a2e8a4692f1ac5f911be92'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'df987b9c3016b0c180c91735801c16252cd336db1ef43b7f3fb20218083aa0c3',
       '52342d9b8795dae34c98069cea996bf38aa01457efb6f744183ad54f22970d3b',
       'fb08802d3419b17f3f6855cd7609bef97bf3c1ff216015bd8a8f5a9d8a79c543', 'result_c43e72d1da257a717b981da1', 'match_5871147a6d97345806b6ae65'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'A', 48, 'last_agent_standing', (113.0, 107.0), (335, 335), (0, 0),
       ((48, 'kill', 'B', 'A'),),
       '1d9990eee1a8c2b9f9bc5effb01e86aa7d53543b537df144e576fe07cc69098d', 'f54a046c1b4ba2c370ada06a8176db6a1811b258951789356011d3ec4552b9fd',
       '57a838478cd661573823320c5ebfca33f30132736a6ee3bcf86221fe852576b1',
       '9183360f5abde31aa607f94287082659631aa4bffffbe77ef6987c6e50e9222b', 'result_eae78b2c529bf13d4735baf9', 'match_21cde6bb56f50292e95142a8'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'A', 72, 'last_agent_standing', (227.0, 216.0), (503, 503), (0, 0),
       ((72, 'kill', 'B', 'A'),),
       '6a97473248ce00ea3aa598ecddc5b90c7341ae994381fc1c7d3d0f2c0b40d342', '67370997fe21128ff9edcb913b12aa313a4712f9f6ee47009af3fcf9187328b9',
       '3dca23dbec3466aa07a469310bf29e9c266839a739696c5194167bc9e9d96e61',
       '8a720bac28459ace49ccd6ea8e733d5249bc4354fe36a225a3ace5d7ead75bb4', 'result_8f613c7655e5d0ef1cae407a', 'match_d1aadaaf94a3a93d1060b9b0'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'A', 159, 'last_agent_standing', (591.0, 603.0), (1112, 1111), (0, 0),
       ((159, 'kill', 'B', 'A'),),
       '7917da72f367f42805d006522787012541f6bbe05db02243ca647d23ea2a9eab', '179900534d8ad061e5c32459de2c6e962f110a93e91e4b4a5cbf5ac10fea4f31',
       '9cbc825101dba8283ccdd4f45c08faa696972ec519db2652017e9e86f56031a3',
       '39f0d9d545cd0ef4294d814cc74d34ea84ffd8744a2bf2494ea0242f9c711ffa', 'result_0ddeb4f62ec16bb53243f9c0', 'match_aee9e31488e5374d47cc1387'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'A', 48, 'last_agent_standing', (113.0, 107.0), (335, 335), (0, 0),
       ((48, 'kill', 'B', 'A'),),
       '1d9990eee1a8c2b9f9bc5effb01e86aa7d53543b537df144e576fe07cc69098d', 'f54a046c1b4ba2c370ada06a8176db6a1811b258951789356011d3ec4552b9fd',
       '57a838478cd661573823320c5ebfca33f30132736a6ee3bcf86221fe852576b1',
       '7d2042a93ea26f65483951205738be4b7ff93c4ac0ecd0f0dac2d729cd106053', 'result_df06886d70198e0734928c89', 'match_b582b81d4c7de8e232314e4b'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'A', 72, 'last_agent_standing', (227.0, 216.0), (503, 503), (0, 0),
       ((72, 'kill', 'B', 'A'),),
       '6a97473248ce00ea3aa598ecddc5b90c7341ae994381fc1c7d3d0f2c0b40d342', '67370997fe21128ff9edcb913b12aa313a4712f9f6ee47009af3fcf9187328b9',
       '3dca23dbec3466aa07a469310bf29e9c266839a739696c5194167bc9e9d96e61',
       '714b26bdfb628cfbdb0fbe480cb09693f49d33fdc9e7c8928d6b56170135d38f', 'result_046136d4fc94dc961bb53ad5', 'match_ee40b8c4fb51bb865ecf8995'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'A', 159, 'last_agent_standing', (591.0, 603.0), (1112, 1111), (0, 0),
       ((159, 'kill', 'B', 'A'),),
       '7917da72f367f42805d006522787012541f6bbe05db02243ca647d23ea2a9eab', '179900534d8ad061e5c32459de2c6e962f110a93e91e4b4a5cbf5ac10fea4f31',
       '9cbc825101dba8283ccdd4f45c08faa696972ec519db2652017e9e86f56031a3',
       'eadb1b5a4b68c1589601a2310dcd0fe11e8398d5df26d45c3629e4c214677592', 'result_2b98f9edd2ab1e5306c4399b', 'match_971320136d8254c37edf6128'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_min_guard_twin', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd728fb8e4720a331a6a4892e2b42114e6f428341ce17936863fc760055fe2d80',
       'b9887049b351ea71a0b9008242e7943c86c150d2cee06528c69ffe2dbc8f2559',
       'db7a032c9d5fb9616a63ee43cb3e394b3fea584f35b1e93269d1405f802313f6', 'result_a17037971277cbd46992b9cd', 'match_443e0b8cdd48d82e988e1f72'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_min_guard_twin', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'ff0432a7e5f08603fc8476afc8ec0e50dc9346ee94f082904a549f7ae10f5608',
       'c6bdecc3f79f8ea9edb0865097b7b169f4425d83da17a48eaaca91b25c0e62ec',
       '9253653764a57d86d5d2c7ca905b529728d1e98099a6279af2ede496915ee9c1', 'result_db0b94e520730035914993bd', 'match_c9565507f710a32c916b5208'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_min_guard_twin', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '7d7bc16fb7ca01e7c8bf10dd98b1191728ba2edeb4119d302ccc05520b20ae7e',
       '52301cbd10a0a993b48d8f5ee9adab3b8e30f7892212cb4461511783e9d65c28',
       'd8a85ea069129732a7a0a207914aba40f3cc754f042a7d3c9fcb4d8ca4719fad', 'result_26a5d0f6ec67e485727b31f7', 'match_d0040519747d39006ca6595d'),
    _m(T_E3_ID, 'e2_min_guard_twin', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd728fb8e4720a331a6a4892e2b42114e6f428341ce17936863fc760055fe2d80',
       'b9887049b351ea71a0b9008242e7943c86c150d2cee06528c69ffe2dbc8f2559',
       'a0914e0e108ec476fe2ef5310e38a13f9dfbeb5eb748d88d3ca9eb906de86ed5', 'result_7b899723ffb4a09350e90366', 'match_34f66607114dea533917d307'),
    _m(T_E3_ID, 'e2_min_guard_twin', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'ff0432a7e5f08603fc8476afc8ec0e50dc9346ee94f082904a549f7ae10f5608',
       'c6bdecc3f79f8ea9edb0865097b7b169f4425d83da17a48eaaca91b25c0e62ec',
       'aad1d49d332106f38ac5c3c4da02469510d9c591aa81358abbfee98777ef8133', 'result_f6b70ae7244f540fe5fe0b94', 'match_cd50548ab60fac681b542f35'),
    _m(T_E3_ID, 'e2_min_guard_twin', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '7d7bc16fb7ca01e7c8bf10dd98b1191728ba2edeb4119d302ccc05520b20ae7e',
       '52301cbd10a0a993b48d8f5ee9adab3b8e30f7892212cb4461511783e9d65c28',
       '5caad52cdf5663dacd42dbe5cdfd064bf1636b0b3d87dda9fb628e55211e1bfb', 'result_c807a950c1b0c15365c820b0', 'match_194989e0ad70560df0e3cfad'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '893b3317b21bece60ece7c7b8b9843b5a806996b7da1ddc2a9b38d33b8a2dcb6',
       '81770607915a9198be7a09ae840c85ed13374bc57f463a4c4f75ba0c955ebea3',
       '6bc04eea5099beae7e837d2942b3783896c99bc91be969ad20e3dc73217c0fa9', 'result_e5bb0edfd59bbf93ac65c0b0', 'match_44226083f187c4690ffa53cb'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '4269b0fd612ee787b3603364c3d3b14da140c088c5325ba5ef56dd5d5d13a731',
       'b168e206fc0835c54ba1e609467f4f880b408daf58e0b3ba51b74098992d5c8a',
       '679906c9aa3a2a3b9be529fdd43ecffc1cac1ad4dd8620ffdce461e1dae02f11', 'result_c926f0b61f6061ebf95accbb', 'match_502a70173f44eef42fc64beb'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'a80110d5f372356df028942925bf889754363334f65cb7c5e911e0ac9c57c59e',
       '6a7e2b23723658ed42f90daa9a0fd175f59e5627300c2f6721851b2ad7278b6d',
       'cd209dc87b71c5f478ad5738c801f0bd6e146e3cf7d4886a9def37afc2c1d5db', 'result_38e97b18b4c70750f3a0fbeb', 'match_736ce6870e1620672d09f529'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '6b60219434e79540b4649543ea213fa352705d69a3b15e46e2f1589417ce281e',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       '221b6c859c8099fc8b2e2a456845d3446109320850e7c26c3f2fa2977f695c53', 'result_3f5ea7fb667001db20376e39', 'match_dd552d384807c848dea9eede'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd86ad09d2cb6d4cbe7b8e2fb69768752a18fa48a23d9f0ba70210f4eacbe8a8b',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '9bb1a07b67587af4c0f5f2b23ea74a560a5269e93a58357242aa6e7a8fe13677', 'result_f95277637dce4be9d7af7e0c', 'match_1e1ea048c037b39cf77e632a'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '84838e5beb85b105c201e657b2e4139ff0d45c96db0b4d8b25719c0c8c7916a7',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       'd737b0f9cddff74c40529ab1305492ea44e54431f76e7d34d57093d27cf11172', 'result_7515a0f002891045ea94385f', 'match_38ee28febe71a13039c8bd2b'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 1, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000), (0, 0),
       (),
       '56e7723219e4deff368040b791ed5d71239f39e1b75e97932b47ad1e047563ea', '4316ba8bde5a6c2dfe3346875aa3ac7efaf7a8b5234708ab0b9d130a8108be33',
       'b754267b941fe60131f5102c727be56bb1b4757ffd818e6d8ce0b820e96e00cb',
       'f4811c7b774c5f735c2bc5ef52439f42c58caeca8dfe871fa3f2ff5a2cef4d5b', 'result_c3ee531f555bbeeb8431f7d3', 'match_c76d4330c2cf801f4d897e2a'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 2, 'B', 1000, 'tick_limit', (1000.0, 7655.0), (6992, 7000), (0, 0),
       (),
       '34ddd973e11ff515eba17e1a824583dd02ec2a5333d5a35daf4551bc651a3cd0', 'd057895b6bc165925a1d0e84a20408afa1701a3ae7ae7a67fb34e5803922778c',
       'e6e05674b4a0d127055e48b5af873ad05911e035e7e764b6ff94d8191c627510',
       'fe7f61c4080cb2327f6f39efe07b10692628b073eaf6ded24b987d661141484a', 'result_e1ec6fc06416e393cbb816e8', 'match_d2180a87699e8902c3220ab5'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 3, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000), (0, 0),
       (),
       'a4377f12f6deb4671ae3a1f7033d1a60d01d93e1fe07b46fceafaf21e95f0f34', '9a8f88d5814b20c9cfc77608c05791ed2beadd447e4bba142fda2d16a9bbfa0a',
       'f8291f49422037e3d28ca944c7d572cc75135d625a011d22bf90ce58ebe415ae',
       '1a8f20de84810d5d24272f7b98fbb7185c45e71834086641e30ce1f3b3cb354b', 'result_0a19f88863af6fb8d2b3181d', 'match_bf755dbf17bd6902b41c65bf'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 1, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992), (0, 0),
       (),
       '4a6f1842e5517f81bbbc03d7fe1b515b02acbfc9f79680354db50e3286bf6536', 'e877496db8c4658c6df70d897e1b6f761149c07ec0770cc5255bfa1df056c370',
       '74b12b2c19437699e8eba89af5838cb5208469a48ed098f98b519c9859e2fa42',
       'ad5be98b429741f3f163440e365a455b1a46797a02a12a0486e274aaa51f4236', 'result_51ec9110d455c139776e8cc2', 'match_c415962344b84523c466afde'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 2, 'A', 1000, 'tick_limit', (7654.0, 1000.0), (7000, 6992), (0, 0),
       (),
       '0fe5b8cf1ccdc7086a8e51081118bc7bfe3e7b0765aadb6c34f634a2d85f02d7', 'e17bbbcb711fe38c17680fbe29b12b006fb6c0851fa38e91200181031f00ff3f',
       '0b574a5933ff0128ddb8a6a3de5a314f19407f29dfeb6189bd987dddd45f4256',
       '2838eba43449d56bf84cdd2cd5919b4e2627997d19edc1e2dcf7fa818cfa4234', 'result_5688d7929a1fbb093ef304a8', 'match_1c3b5db24a54748d0de6c1c8'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 3, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992), (0, 0),
       (),
       'd4e2f8d4eb1beef7e6b1dca53277feee6ca16ada8fa16783ef083193d9d1f486', '2a39f4b087c7e6ed233a216b9964873cdd8e62b704830b3362a6ec03ad88347e',
       '54800cd17023ff6b9ea72964d9b19f5fcf812da53c04e05037cccb280a93da02',
       '814a2f701ac924211272cd52275712d9d5e8f3fa847db8722735fe81a8a48dec', 'result_7990d290b93472857ed159a9', 'match_013d57928f15266d806cdc05'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd9402ec6c38d9e73f102956d3a7baac6855eac3b4c28278fa94c5c9230e6fbb5',
       '81770607915a9198be7a09ae840c85ed13374bc57f463a4c4f75ba0c955ebea3',
       'fd2a88efba0e3110456d2960309966ec0d4f127ed2dc9a89ce48ca94a301e2c4', 'result_f42aace4402a9ea894cdf94c', 'match_26e6b773193f6f83f6b1fc41'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '60cbef2596b9c5b6e6f5446a3438e7f294fcc7ed8ecf2ba43b58ede47a415b7b',
       'b168e206fc0835c54ba1e609467f4f880b408daf58e0b3ba51b74098992d5c8a',
       'a5a0a11662a55468cedfc0504113acbdec96742dbf4201110f1df579bef7ba2f', 'result_2cf7d88a8a18169929cc97f8', 'match_cf9c39c002347e2e3516bbbf'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '412d63c889d737c535205b50bad1900afbe436080dee1559d8f490aa92fa2940',
       '6a7e2b23723658ed42f90daa9a0fd175f59e5627300c2f6721851b2ad7278b6d',
       '7bda83b8cbad6890b1c8561e83a99e26cdb545b67cbcbb8e4d0be16b768b8e9d', 'result_abfa2aa2b9987f297383770f', 'match_84bbf6db805054318f628d61'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '0e3c0a4abbc455aa8b062d27fc70336ba9c5eee9e3f7f8d56b9d1370c5fc2b6f',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       '74ae827c26694b7d1db4b453beece45e0d6c7e67ed1dba366cd16eb777da2ccc', 'result_6dc93d05edfa4dfa1af6681f', 'match_f99bd1a9c4aa6961d6c9ee6b'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'f3d0804bd10cf464fb9a229f3c993bac03bb84b418d22284293efa31ad0e1296',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '6d1191481be63cd23d690e03ec106b7b21f15d13878f3398053c880f8c8df937', 'result_f6a8b6da1b007ae1f4a88794', 'match_ff3b9943a1816f51c226a7a1'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'c32ba4a574b5455b6b20897cb636cca2a5b2088509c2c3c640d37418e433476a',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       '8d2a449375c978c43e8d0d63bb649c9ffae46b4f2de7a7145b0ea4e340ef7525', 'result_63f154742933304e70a346db', 'match_7381ff680a55fe63438ded7b'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'af89a8fc31a4847b0354d3c6dda8b47c92ffd419b7140b7c2f6b89d86e983316',
       'cdb5dedb89b9e998af3f7d0fc5831ca0bb7c8ca34a5c5267839c105825d95561',
       '9cc3192b704608e9c85402c975bfcfaf2c1d88c1195b09df99e797bff18a8cc7', 'result_165bda90929bb6b6ca2240dc', 'match_ceaab5591b1d72e0110e7ae5'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '5704ab1bd4fafe7301bfda5a88b981cdba47df63b8df17a7972d93abf5c93ced',
       '2b3fe0b955c2805e3e55f922938576aed086123a55e2ae02fffc6e40683b7604',
       '4d95ce6020c1139bc719cdaa7e9f64635c26aa790db1174c7c282be30641a5dd', 'result_2b9c4c2d6112a93f11262103', 'match_539350953af083a9873a38ab'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '180ecc277bcc84d646e4bb5e9999682c765800737d64ae42df27a691265d0a77',
       '28205134e44e1a4ddc0c4942fa1dbcb80d64051189fa70bf49038d18f23eba68',
       'dd651c6d9ffe3d03d564f1098687addf45b23d92482ba2d1b20094f3160bf9b5', 'result_deedd386b881ea9fcfcb8ddc', 'match_3f98653d1c79df3c33155c89'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 1, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '259f457050e850ed1e952cda52ac13ea40deb0825e0dbdd3b8b79a40bfd019ee',
       '4f8c5fa159d0ef659329a4099d6f59eb1b38f762324f34279c0832e019a8535a',
       '83f6c3f748ef7ea65d41c9ff13cea8e19b76350d7952263eae54599aa50b901f', 'result_cec8fb1ca0f231fbccbf7418', 'match_37e424d852692bafda78afcd'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 2, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '48a8433025c93dc520197ade2b6b3caeca1a3576f74c0cf9fa7c5efc32619ebc',
       '80a550514dc1f648c55433ecd114210eb09fb47f42142432e19d4eda7d8a5e7f',
       '06890016ceb2e538495d68558735b9e6a49194e096787b1f0738461ec6a04e73', 'result_653c2cd6c65b92a18024ce1b', 'match_2c73c4a19e83f309101719d4'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 3, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', 'fc4c0e3c0d71e1b255ce850240d5b8796f6c21e7a6c6305f4288cef10f557477',
       '6eb1f18b0de0bf233b2ab69787721d0cd62166b09350f2d7dc0ed9e653f3c0b9',
       '2d4f82dbcb327d4bed1d6af026895d9c60236a06226907ebfdb308140b0b38b0', 'result_6a07de2ac277401cc48185d2', 'match_ee87c599b2d9697903905802'),
    _m(T_E3K1_ID, 'e2_spread_defender', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'acb6b219bd31f2702c0fb44ffff1da098c8220caf27016acbaf29d0086df1214',
       'f242a40f634c3c3e4be8239870e7cab06c42696c405769ac4cad50d840f8a0c2',
       'f1f7327058aa9904c50583f31dbb46a95d2be87263d85d894d8a0dbe8d9bf0aa', 'result_391bc996725853dfbebe9b07', 'match_538ee21eb89242766b50d9b0'),
    _m(T_E3K1_ID, 'e2_spread_defender', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '410ff8005d174682fcf6825412ab6c30886716997e8f47aba02c5cd0812b14f3',
       '9f2b6f7908c49fe573ca359132a703446ab2d3b76dfe2bc9d3d520fd4764f7c0',
       '08ea567928b6a5e003aa198993a6551f8ed231abccdc0dccc305bb65291340fa', 'result_599b37f049fc4c1c0814f350', 'match_bed89f6dd8f38ae46ea1ec49'),
    _m(T_E3K1_ID, 'e2_spread_defender', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '3c90999a9fc987f38515a2dd11eb2f8ed11977463b197afd283ca190b0fbd978',
       '0d83db182b8c6fb962170924811e1efb0ca429d9e8e36f3d933a5557299b9ac8',
       'efbe685f0fa1e725be14cd1f233b164e3e55dd4862ba2c277d750d064510f8df', 'result_60e6edc53578efa9c87c6d56', 'match_91720399110b83eadf97cf3f'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_spread_defender', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '9f25a7e69ad36859cabcb4cb5aaf04656944941c4063b2639f3d3bf652d32935',
       'f39e4b8b20326aeb13737d364aee86d570629ca3f481fe7d48cc5f8422838c31',
       '977eb88bc5d4a7de66c255323c4f4977ae0302959495fd439b08df4451901e0b', 'result_72b698d759f3ca6e343a603f', 'match_3bde62de695aaf632439259f'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_spread_defender', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3d67fa73d3b2ae46c813cb6a84f5d19e67760f07ac58f1d8740aebdd223f36e3',
       'f27c75dadcb314bd8b957de2dff27379ab8dae69617a378699006638ce52e888',
       'c86355fd39808a9ab45b9c8a254a2da869ad339df50eab5dce7e4c4138a85bf8', 'result_0c75492e2c6fd1c4aa35df57', 'match_14958396d780a5f5a50e8419'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_spread_defender', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3da80e2bf59b813ceb12d813161a21224af58639a027d495b941e0e21ec5a91e',
       '5869c154ade36d903d321372dc7833d5df8f9bbfa19d262554cee801b7deea18',
       '3507315186981f44e6e983a18065d5b1e44c5da15e3050ed1cf97931af36b8a3', 'result_c7e834d2680bca7848e1d830', 'match_5008eb78fa28f6937c55fd2a'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_repair_guard', 1, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '07debd94457fbfbf92fae6e93a90f93b814a00925b4b4f1fce7525cf9e71ccef',
       '9c751035560bd83a024bfb3df40ac5f3406a2031f10951b1cc5b5bb681670899',
       '72dbc8c417c4597c1a935bf5df38c90a53a425080de81f45dece6c631f48c091', 'result_eda4df55ec75da459f1677f2', 'match_947a184b517c0a74d9b78bec'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_repair_guard', 2, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', 'e2f66b2763b1a6d46bdabcb785ad21749d46bef1bf01239223d2ec6889714d4e',
       '75822f256a34969b682cdd97671faa6294afdd43965bbaaa1027f853478490ea',
       '92eae6a3ebbb2a527d220039dd0bc105115fd0b4d814d538d14b3e216ace2d8b', 'result_b4d78f1878e6b55c74dbc635', 'match_b0753c54858afe89ea0dad92'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_repair_guard', 3, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '30eaac678ed68f6225e7e0ec5ac562c220ff80617085c429e21f43680cb3dd45',
       'e5a12877bce77dfe3d055b73a458557341972471b497d7c73e52708c42c6bd47',
       '8d85b5ab2120e6afbfdebab9e121bf58f25daab61538ea76d9eb9af0713e455f', 'result_d3f3b92ad4196c41a3f8f85a', 'match_99379d71db729b09512f869d'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '46da8f8a3db2e0eac196aef412f4bebc0294f49982767db320ae03c4c90c9f0c',
       '5450b5bd213d0e8e9a802942bfee47a9ec63e61815f8846a601c810cf56dd372',
       'f7e79303e2d12688afdbc32c3423946a6f5f71228d9b48b2e44d31ba5e0a1907', 'result_b943ba449371a62751c8ccdd', 'match_6d4415b9c48f1d340fbce4bc'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'bae6d8be3fa5dd786c09a628bcf798aeeafba62e42552781e565d5f32fb0a93f',
       'e1cd721f6c896fb041d33984e52ab9542392d1bf7d4be51da98c7a3aae46efca',
       'b4874d62f138dceeca9f350e5af53fad040469cbc999e50004cd65cd34f98dea', 'result_64bffcbb419e29491bfdd6df', 'match_259ef5918c48f7ccf88e258c'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'df987b9c3016b0c180c91735801c16252cd336db1ef43b7f3fb20218083aa0c3',
       '52342d9b8795dae34c98069cea996bf38aa01457efb6f744183ad54f22970d3b',
       '231de6eb3cb0e8285efc7660a12a2fa0531c1d20a3add5fa9aa312129570e41b', 'result_6b1db755644021c4c57d22e0', 'match_28d2d6e8ec540386f50aee22'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328), (0, 0),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')),
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       '55f3cbece7a7e9286fd94f055dd92de8cd6badc41431de33b81b37c90609633d',
       'f8a153c9b8d07f46cb2b84d07b1f453cf04a56dd701877457038cbe00c839bb9', 'result_b4613eb8208176c3a63d0e0e', 'match_d7f1abba6508a1ef09454aee'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496), (0, 0),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')),
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       'f1d54bbd873969422c06b8d4f249278e37e94b0632bee441df821b69a7f0b7d1',
       'd3a575687ce545e389cceabf047b5cc204ddd06cba912a75b565e1230a6eacca', 'result_04654a4f2cf9d91c20b9b597', 'match_3bfd127a97e81671ddcbc824'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301), (0, 0),
       ((43, 'kill', 'A', 'B'),),
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       '569d5df438aa02f318003d04c3488c462e819de39341090f6e9b4d14c5d1db79',
       '4078497fd283190add9d4aa64df87d16c860259792f8e542d81fd10e1e6900d5', 'result_dbcb6ac2b9f0292556ed23ae', 'match_92dbf63e8c4a522db47eb848'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328), (0, 0),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')),
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       '55f3cbece7a7e9286fd94f055dd92de8cd6badc41431de33b81b37c90609633d',
       '4679e074e00f32748194d835e24f917fda808e8a0dc92b1cdb7ffb4a5ad4f2eb', 'result_9137fa5119ee7df891a9f0dd', 'match_3fd22be4150ebee67cde298d'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496), (0, 0),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')),
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       'f1d54bbd873969422c06b8d4f249278e37e94b0632bee441df821b69a7f0b7d1',
       'e86cf005d0076054bed3a22cd113c3b8f6e3f1fb67a46b63053419d62789b0b0', 'result_4f0fe460a7fc1f149d789943', 'match_6feddbcfe12eec1108c9040b'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301), (0, 0),
       ((43, 'kill', 'A', 'B'),),
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       '569d5df438aa02f318003d04c3488c462e819de39341090f6e9b4d14c5d1db79',
       'ef68aa268bf5e39015cda419e33598c030b3f7a4ce685058d12239efbdb341af', 'result_f22fc7b5b214dc65bba474c5', 'match_b69b48183762ffc8d8db32db'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_min_guard_twin', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd728fb8e4720a331a6a4892e2b42114e6f428341ce17936863fc760055fe2d80',
       'b9887049b351ea71a0b9008242e7943c86c150d2cee06528c69ffe2dbc8f2559',
       'd1b295ce1c1b058cad7ff8438abdaaf3825656736bb2caa0d7d8176f5cd05133', 'result_fc3ef6c3c83a3dd306fff4f8', 'match_04e4cc915f98915f8108ae85'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_min_guard_twin', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'ff0432a7e5f08603fc8476afc8ec0e50dc9346ee94f082904a549f7ae10f5608',
       'c6bdecc3f79f8ea9edb0865097b7b169f4425d83da17a48eaaca91b25c0e62ec',
       '2716bbb307736e9a1baf18d319fcafcd1a0ebeeba2ba75f99ff85896976d9b2a', 'result_83d7e4fefec6d5d7de224e35', 'match_b1dea71320b29240bd5e8452'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_min_guard_twin', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '7d7bc16fb7ca01e7c8bf10dd98b1191728ba2edeb4119d302ccc05520b20ae7e',
       '52301cbd10a0a993b48d8f5ee9adab3b8e30f7892212cb4461511783e9d65c28',
       '3c36d5bbaa63cb24e93d327ef727a554d8d93b2cc34e3069c43c6db711e1261a', 'result_5c5b5c0ec96169871f49c35f', 'match_b2907883820db68d68eabdc9'),
    _m(T_E3K1_ID, 'e2_min_guard_twin', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd728fb8e4720a331a6a4892e2b42114e6f428341ce17936863fc760055fe2d80',
       'b9887049b351ea71a0b9008242e7943c86c150d2cee06528c69ffe2dbc8f2559',
       '797ad12eec253b9fc1584d24a8b7d9dd5955ec255ae7dcaee311183798f2f0b8', 'result_ab600a4d511707fa01cdaf1c', 'match_b94daef731a9956994e0ff01'),
    _m(T_E3K1_ID, 'e2_min_guard_twin', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'ff0432a7e5f08603fc8476afc8ec0e50dc9346ee94f082904a549f7ae10f5608',
       'c6bdecc3f79f8ea9edb0865097b7b169f4425d83da17a48eaaca91b25c0e62ec',
       'c9bc3818115bf4aa9e7e1ad56a84a53b3a7233cd6365616611fba41d5e768fc6', 'result_4a9be5e359fbefb211432fa0', 'match_2d62fbc3ec75db3e89b55843'),
    _m(T_E3K1_ID, 'e2_min_guard_twin', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '7d7bc16fb7ca01e7c8bf10dd98b1191728ba2edeb4119d302ccc05520b20ae7e',
       '52301cbd10a0a993b48d8f5ee9adab3b8e30f7892212cb4461511783e9d65c28',
       'd86ce1551d825616fd672897cfa1a896d9d303c5d8806bfc831bc0a24139390b', 'result_843a823a2b3f2b3e98543ce0', 'match_516a7ebf28be82368913ec1b'),
)


def test_frozen_corpus_covers_the_declared_matrix() -> None:
    assert [
        (case.ruleset_id, case.seat_a, case.seat_b, case.seed) for case in FROZEN_E5_PARENT_CORPUS
    ] == list(corpus_cases())
    assert len(FROZEN_E5_PARENT_CORPUS) == len(RULESETS) * len(PAIRINGS) * 2 * len(SEEDS) == 96


def _row(ruleset_id: str, seat_a: str, seat_b: str, seed: int) -> FrozenMatch:
    (row,) = [
        case
        for case in FROZEN_E5_PARENT_CORPUS
        if (case.ruleset_id, case.seat_a, case.seat_b, case.seed) == (ruleset_id, seat_a, seat_b, seed)
    ]
    return row


def test_frozen_corpus_exercises_the_paths_e5_changes() -> None:
    # Guard: the corpus must contain the long opening-pass and multi-pass
    # stalemates E5 targets and at least one capture, under both parents, or
    # its identity would say little about the "core_base" path.
    for ruleset_id in RULESETS:
        rows = [case for case in FROZEN_E5_PARENT_CORPUS if case.ruleset_id == ruleset_id]
        assert any(case.reason == "tick_limit" and case.ticks == MAX_TICKS for case in rows), ruleset_id
        assert any(case.captures for case in rows), ruleset_id
        # lambda = 1 (E3 G.4): no entrant is ever silenced for a whole tick.
        assert all(case.silenced == (0, 0) for case in rows), ruleset_id
        # The sweep-backed opening contest (review Sec B.4): a 1000-tick tie.
        opening = _row(ruleset_id, "e2_sniper", "e2_min_guard", 1)
        assert (opening.winner, opening.ticks, opening.actions) == ("tie", 1000, (7000, 7000))
    # Review Sec B.4 under the primary parent: the guarded-painter mirror is
    # decided by capture well before the tick limit.
    mirror = _row(T_E3_ID, "e2_guarded_painter", "e2_guarded_painter_twin", 1)
    assert mirror.reason == "last_agent_standing" and mirror.ticks < MAX_TICKS


@pytest.mark.parametrize("frozen", FROZEN_E5_PARENT_CORPUS, ids=lambda case: case.label)
def test_parent_is_byte_identical_to_the_pre_e5_freeze(tmp_path: Path, frozen: FrozenMatch) -> None:
    observed = run_corpus_match(
        tmp_path, frozen.ruleset_id, frozen.seat_a, frozen.seat_b, frozen.seed
    )
    assert (observed.winner, observed.ticks, observed.reason, observed.score) == (
        frozen.winner,
        frozen.ticks,
        frozen.reason,
        frozen.score,
    )
    assert (observed.actions, observed.silenced) == (frozen.actions, frozen.silenced)
    assert observed.captures == frozen.captures
    assert observed.anchors_sha256 == frozen.anchors_sha256
    assert observed.cpu_sha256 == frozen.cpu_sha256
    assert observed.writes_sha256 == frozen.writes_sha256
    assert observed.match_id == frozen.match_id
    assert observed.result_id == frozen.result_id
    assert observed.replay_sha256 == frozen.replay_sha256
