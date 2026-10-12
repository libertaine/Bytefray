"""V6 E4 parent byte-identity freeze: forward pass order as it behaved before E4.

E4 (mirrored pass order,
docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec I-K)
adds ``RulesetPolicy.scheduler_pass_order`` and a keyword-only
``mirror_second_half`` flag on ``scheduler.run_chunked_quota``. Their
defaults (``"forward"`` and ``False``) must be *observationally identical*
to the scheduler as it behaved before either existed (review Sec J, P8).
That claim is proven here rather than argued. Every value below was recorded
against the unmodified scheduler at ``e52b5aa`` -- ``89ced9c`` plus the
documentation-only E4 design review and E3 addendum commits -- and committed
*before* any scheduler, policy or Ruleset code changed (review Sec R step 2).
Every later build must reproduce them byte for byte.

The matrix runs under both E4 parents:

* ``bytefray-rules-6-research-capture-hold-k2-disruption-slot1`` -- the
  historical T-E3 Ruleset, parent of the primary E4 treatment (K=2, lambda=1);
* ``bytefray-rules-6-research-disruption-slot1`` -- the historical T-E3K1
  Ruleset, parent of the companion E4 treatment (K=1, lambda=1).

Pairings (review Sec R step 2), with the tracked E2 research fixtures
(``tools/research/v6/e2/fixtures/agents``) and the E3 jam sniper
(``tools/research/v6/e3/fixtures/agents``), all LF-only by
``.gitattributes`` so every source digest -- and therefore every identity
below -- is the same on every platform: Global Sniper vs Disrupt-First
Guard, Pure Repair Guard vs Global Sniper, Spread Sniper vs Disrupt-First
Guard, Global Sniper vs Minimal Guard, the V4 probe mirror, the Guarded
Painter mirror, the Disrupt-First Guard mirror, and Jam Sniper vs Minimal
Guard. Each runs in both seat orientations at seeds 1-3, arena 512 and a
1000-tick limit -- the E3 matrix's own parameters. 2 x 8 x 2 x 3 = 96
matches.

What is frozen, and why exactly these values:

* ``replay_sha256`` -- SHA-256 of the canonical schema-4 replay bytes. It
  covers every tick's events and their order, scores, memory diffs in write
  order, each entrant's per-tick ``cpu_used``, and every process snapshot.
* ``result_id`` -- the canonical result identity (winner, termination
  reason, ticks, score, and each entrant's termination reason, statistics
  and metadata). ``result.json``'s raw bytes are deliberately not frozen:
  they carry per-execution occurrence metadata by design.
* ``match_id`` -- the request-derived identity, pinned so a change to
  identity derivation can never masquerade as (or hide) a gameplay change.
* The execution sequence, as two digests a scheduler change would move
  first: ``cpu_sha256`` over every tick's executed-action counts per seat,
  and ``writes_sha256`` over every tick's memory writes (address, length,
  owner) in the order they happened -- the in-tick interleaving of the two
  entrants' writes, which is exactly what pass order decides.
* ``winner``/``ticks``/``reason``/``score``, total executed ``actions`` per
  seat, ``silenced`` -- per seat, the ticks the seat ended alive having
  executed no action at all -- and ``captures`` (every ``kill``/``death``
  event as tick, type, victim, killer) are asserted first, so a regression
  reports *what* changed before the opaque digests do.

A mismatch here is an implementation defect in the ``"forward"`` path,
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

# Historical T-E3 (primary parent) and T-E3K1 (companion parent).
T_E3_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_DISRUPTION_SLOT1_ID
T_E3K1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
RULESETS = (T_E3_ID, T_E3K1_ID)

# The review Sec R step-2 pairings, each run in both orientations.
PAIRINGS: tuple[tuple[str, str], ...] = (
    ("e2_sniper", "e2_disrupt_guard"),
    ("e2_repair_guard", "e2_sniper"),
    ("e2_spread_sniper", "e2_disrupt_guard"),
    ("e2_sniper", "e2_min_guard"),
    ("v4_probe", "v4_probe_twin"),
    ("e2_guarded_painter", "e2_guarded_painter_twin"),
    ("e2_disrupt_guard", "e2_disrupt_guard_twin"),
    ("e3_jam_sniper", "e2_min_guard"),
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
    final: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, TickSnapshot) and record.tick > 0:
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
    replay_sha256: str,
    result_id: str,
    match_id: str,
) -> FrozenMatch:
    return FrozenMatch(
        ruleset_id, seat_a, seat_b, seed, winner, ticks, reason, score, actions, silenced, captures,
        cpu_sha256, writes_sha256, replay_sha256, result_id, match_id,
    )


# Recorded against the unmodified scheduler (see module docstring). One row
# per match, in ``corpus_cases()`` order. Every row's replay_sha256,
# result_id and match_id also equal the preserved historical T-E3 / T-E3K1
# corpus cell for the same match (matrix v6-e3-matrix-v1-634132ec3c15), so
# this freeze is the historical E3 treatment itself, not merely a snapshot
# of the tree it was recorded on.
FROZEN_E4_PARENT_CORPUS: tuple[FrozenMatch, ...] = (
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd9402ec6c38d9e73f102956d3a7baac6855eac3b4c28278fa94c5c9230e6fbb5',
       '33f5c13147d386aeb496893022e79f85d177fdb7ec22490e11d843ac9d0250aa', 'result_d23c5fe02307445fc603e0c5', 'match_66e99852e9ebceebd4dfea6b'),
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '60cbef2596b9c5b6e6f5446a3438e7f294fcc7ed8ecf2ba43b58ede47a415b7b',
       'd4823c20760765308ab8c92419afba5e0ec1620e7091e9a88d95a88742247bad', 'result_a35c430b5461443948f4c169', 'match_8fde67f081aa466cc335c223'),
    _m(T_E3_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '412d63c889d737c535205b50bad1900afbe436080dee1559d8f490aa92fa2940',
       '3a73b2d0b13d2de10f894dff699d6b926c0dc741e3c65bfc352b0ec3646d69dc', 'result_a41bdefaec11bde8a354ff2d', 'match_b24b69b49b3cc211bc96a4a0'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '0e3c0a4abbc455aa8b062d27fc70336ba9c5eee9e3f7f8d56b9d1370c5fc2b6f',
       'a14104fc844d9d3cc015de8daca723303b75ffb103013b23bdf788291055d8d3', 'result_c53b55859fe1fb9296604063', 'match_6c315dd3fe8ef8132e0e4550'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'f3d0804bd10cf464fb9a229f3c993bac03bb84b418d22284293efa31ad0e1296',
       '5965b5add4be91bbdedf16b73deb25a0f241b6b620658dbe8cd54918a520826a', 'result_2e9841626aaa892bec068604', 'match_5139af798387c215180e5558'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'c32ba4a574b5455b6b20897cb636cca2a5b2088509c2c3c640d37418e433476a',
       '72c5ebab0abe7b08f5d5e76566328a0a7c936885ddf2dabd1c8eee55dbe710f1', 'result_584beb25c6eda0844d206ce9', 'match_63fb4509114a211f005f24af'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'af89a8fc31a4847b0354d3c6dda8b47c92ffd419b7140b7c2f6b89d86e983316',
       '5cb5ed6beec3fa72f200812c9c7421ef65dab24fc18f1b9beb210f51636d490c', 'result_a85d2483b4dc4f433a5cadbe', 'match_43d5a795867c3e723b3ef1bc'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '5704ab1bd4fafe7301bfda5a88b981cdba47df63b8df17a7972d93abf5c93ced',
       '8480a4bdc4e25e04b67d86a26ea678a14d5040961f58bf5cb7ba8790f5038461', 'result_03f0174250a12d46a7d9f054', 'match_e6672e61ffcb8676a7d02cad'),
    _m(T_E3_ID, 'e2_repair_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '180ecc277bcc84d646e4bb5e9999682c765800737d64ae42df27a691265d0a77',
       'd862cde40738bf7136267372a701e3363ae261b5147d390a226011f81fdecba0', 'result_c4be14c63e96931463efbc50', 'match_5219a868fed6f45ca2b753b3'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'cdf0a60c2208364d2730bfef9585d130eab1f3d322c7560d6b87c8c6e2dba658',
       'c4d2e2cffbeb9e5d3ed7bf28fa8b1d3a4321ba14d1460627c94bafd47b731fc4', 'result_b5be9a0a48886271c4da33e2', 'match_53d59fd53b31acebf22fc3e2'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '455445bd762f08303970a3b635cee5a3d17b2b0a2fcd31dd7d804b2356ce3c8e',
       '1837c1298b8ce36b43c571a03a444dbb86528937e65c4ce3768af02b2c874e1e', 'result_c097de0251edababb8cef406', 'match_077400ba3acb526fb7bb319b'),
    _m(T_E3_ID, 'e2_sniper', 'e2_repair_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '8413564668fe798cd6449b8b44ce2f4d0a8553905f522ead1bd5b5de2cf8ac3e',
       'b29ea0c2da6aef0e725e3d01ad1b94fa6fe9d324161768032f8cbfc82bdb9aa7', 'result_aa37afc8c00a6f3543cdb9c5', 'match_f53aa7e19fd827b22de19ac3'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '2bb8ab0f906d82eb45aefc5f508dad53f69da174c3f1557b04f49e05d22118a1',
       '8c4200c3397ebc71784ddbfe195dd09b52d57f13dff4641dcaa385a2125313ca', 'result_683f38eb5facf9238b3dc5f7', 'match_36ecd9c8479ba11a4e2b0522'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'b5d1e9fb09c56646d143f95ab9f73d2d44cfa1b569670f2facd86c64d0f103af',
       '58fb0f94fbbe6d60e24d14391a6ae012da276fc471379d09c136e1bd5ca63f6a', 'result_5f72e58a904f06db1a2dbbba', 'match_c198f6725bae295a5208601a'),
    _m(T_E3_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '1cdd6193c7da446b3c4762e14b34fb3fb5f2deb63dc63150a303cf672cf46671',
       'd25d91a326cc86a564657baac1aab09f888be70e5c00b2b12cb85a13f0429de2', 'result_9f766229999c17174c06138a', 'match_b459b7172d4dbb6653642a39'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3d06408701d7b98342b5d4ab5135fab3c3f4083f2c34395cbb9063a5744a5f30',
       'aef8ddae968e9fcd1d56b30681085fd5fd8e8ab39e5976e230f4b95773e7e99a', 'result_89327c54cfd49bd7bc85c367', 'match_2336df195a00cda5e460ec8b'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', 'f4b65609d5eadd66281bf3297d9dfd3a99d64b5e71a3995d959f9894a9d27761',
       '78b42c703983cc3b2057e90fb70abdeb8ad3b949c58eb0663cb1129d5785a51e', 'result_3f7909eeaf3c980d9a176c94', 'match_33880f125c341896f15f53e6'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', 'e50e1caafad7ddedbe6227daed4cc58c3bec64f32882bee5859ba7e20eff0117',
       '9a5ef7c6d65bdd1be092eae86eb5ee3ee856ff03784b976133a85c8df6dce15b', 'result_13ac69d58bfbb38f41ef4efe', 'match_6750232453ef7763303b2a1d'),
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '893b3317b21bece60ece7c7b8b9843b5a806996b7da1ddc2a9b38d33b8a2dcb6',
       'aa3d985d4d51133d3f24816dab1036223d5f4cae2531b288144ef347b5bf4f3f', 'result_e620b7512002f11cc24597fe', 'match_ccf51a7d3fec7e90fb9f66ef'),
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '4269b0fd612ee787b3603364c3d3b14da140c088c5325ba5ef56dd5d5d13a731',
       '99cafe45d90ad771c21651bb43035c2f582079a47afe3dab634a60ed130c480a', 'result_418457b6718d8137803bdeb0', 'match_7e066782af87804564cd41aa'),
    _m(T_E3_ID, 'e2_sniper', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'a80110d5f372356df028942925bf889754363334f65cb7c5e911e0ac9c57c59e',
       '6f1afdcc6f0a763961ef707747c0bf01b3a71d678c87cc6ff59cbf327e703c7a', 'result_b1cc677b3aa4b65bda8dc878', 'match_9e6128c3eab8fd9a65c5f218'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '6b60219434e79540b4649543ea213fa352705d69a3b15e46e2f1589417ce281e',
       'd61f9fa6908f318563632a75d17bea72be2c8e1ed9c9e746a9049ea6ca639daa', 'result_cb0a810cf05b26fb802e277c', 'match_e35d4075c951302b6ca25c83'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd86ad09d2cb6d4cbe7b8e2fb69768752a18fa48a23d9f0ba70210f4eacbe8a8b',
       '307626564976e708ae1fb484babbfb40b170e61174ceb68a31db63e85cf5951f', 'result_b7b372e701a4013042a490ae', 'match_fa212c669b1dd3fbe13271ba'),
    _m(T_E3_ID, 'e2_min_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '84838e5beb85b105c201e657b2e4139ff0d45c96db0b4d8b25719c0c8c7916a7',
       '1cdb706a0e7397381443fdb606856fbbaf220f7e54d0ba59fc9546cccecdaa0b', 'result_2912fb6bbb691b45e1ce0c16', 'match_47a2a13b81434cb08fc46b6f'),
    _m(T_E3_ID, 'v4_probe', 'v4_probe_twin', 1, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'bc08b5c011d5deaa0e02dac579ffdda9b6788602fb9a5726d25ab99586027c8d',
       'c00999fb3b695bfe1f579e4dbc66565dcbc2929d438b907931a913bbafd96dc6', 'result_9720a55114aacbe76e54a3b9', 'match_6b900339a9cb8ceca2ddc1bf'),
    _m(T_E3_ID, 'v4_probe', 'v4_probe_twin', 2, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'dd5303067f6c6cc8bdc2d8032e907a971d1c185e5f95a4f2a69153591cfe6bab',
       '13563bee00470b3fcc17f0c19b66e6cadbdd31287ae96ea42de8e3cf4b595cb6', 'result_1b782989b0b4751bb4de3485', 'match_c710ee559f7ffa2b791ca516'),
    _m(T_E3_ID, 'v4_probe', 'v4_probe_twin', 3, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'e3abfaeff04d4cdc20cfbe8347cd138b987d3c4538e95e309964f7e0da237423',
       'f4a3cd1a61c5e7adcc526fe5406960722abbff454773b7a325d26adc10d2efcc', 'result_bc390589c1e32d03ed935ccc', 'match_a5a51fd31eaf68fb31978fa7'),
    _m(T_E3_ID, 'v4_probe_twin', 'v4_probe', 1, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'bc08b5c011d5deaa0e02dac579ffdda9b6788602fb9a5726d25ab99586027c8d',
       '92cd51a409c5f918036f93e76551b6f81b0b056311a1babffb5adaf5db54ff2d', 'result_d4974e879bffae41edacf9c2', 'match_3b0c1cb03bddc4f689d1cef4'),
    _m(T_E3_ID, 'v4_probe_twin', 'v4_probe', 2, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'dd5303067f6c6cc8bdc2d8032e907a971d1c185e5f95a4f2a69153591cfe6bab',
       '581218df54ee7eefe98b255bc71c3dd9f974fd489becf68aec386084df4a23af', 'result_b9773ca0a2c12ce0dd62ce04', 'match_a5508b59657a9edbdb4560b2'),
    _m(T_E3_ID, 'v4_probe_twin', 'v4_probe', 3, 'tie', 3, 'all_agents_dead', (7.0, 7.0), (21, 21), (0, 0),
       ((3, 'kill', 'A', 'B'), (3, 'kill', 'B', 'A')),
       '2d03cfd7510d8eeedc4eb56eb88690de8cdd97987063c459fa376b132e3b6dab', 'e3abfaeff04d4cdc20cfbe8347cd138b987d3c4538e95e309964f7e0da237423',
       'a6105f9d844dacd4eec006ca3f7bce24946e09888c708e1ad165dad79dee8c23', 'result_eae0ce3569d8d8b1447436b9', 'match_7ea0a14697003a895a329420'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'A', 48, 'last_agent_standing', (113.0, 107.0), (335, 335), (0, 0),
       ((48, 'kill', 'B', 'A'),),
       '1d9990eee1a8c2b9f9bc5effb01e86aa7d53543b537df144e576fe07cc69098d', 'f54a046c1b4ba2c370ada06a8176db6a1811b258951789356011d3ec4552b9fd',
       '9183360f5abde31aa607f94287082659631aa4bffffbe77ef6987c6e50e9222b', 'result_eae78b2c529bf13d4735baf9', 'match_21cde6bb56f50292e95142a8'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'A', 72, 'last_agent_standing', (227.0, 216.0), (503, 503), (0, 0),
       ((72, 'kill', 'B', 'A'),),
       '6a97473248ce00ea3aa598ecddc5b90c7341ae994381fc1c7d3d0f2c0b40d342', '67370997fe21128ff9edcb913b12aa313a4712f9f6ee47009af3fcf9187328b9',
       '8a720bac28459ace49ccd6ea8e733d5249bc4354fe36a225a3ace5d7ead75bb4', 'result_8f613c7655e5d0ef1cae407a', 'match_d1aadaaf94a3a93d1060b9b0'),
    _m(T_E3_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'A', 159, 'last_agent_standing', (591.0, 603.0), (1112, 1111), (0, 0),
       ((159, 'kill', 'B', 'A'),),
       '7917da72f367f42805d006522787012541f6bbe05db02243ca647d23ea2a9eab', '179900534d8ad061e5c32459de2c6e962f110a93e91e4b4a5cbf5ac10fea4f31',
       '39f0d9d545cd0ef4294d814cc74d34ea84ffd8744a2bf2494ea0242f9c711ffa', 'result_0ddeb4f62ec16bb53243f9c0', 'match_aee9e31488e5374d47cc1387'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'A', 48, 'last_agent_standing', (113.0, 107.0), (335, 335), (0, 0),
       ((48, 'kill', 'B', 'A'),),
       '1d9990eee1a8c2b9f9bc5effb01e86aa7d53543b537df144e576fe07cc69098d', 'f54a046c1b4ba2c370ada06a8176db6a1811b258951789356011d3ec4552b9fd',
       '7d2042a93ea26f65483951205738be4b7ff93c4ac0ecd0f0dac2d729cd106053', 'result_df06886d70198e0734928c89', 'match_b582b81d4c7de8e232314e4b'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'A', 72, 'last_agent_standing', (227.0, 216.0), (503, 503), (0, 0),
       ((72, 'kill', 'B', 'A'),),
       '6a97473248ce00ea3aa598ecddc5b90c7341ae994381fc1c7d3d0f2c0b40d342', '67370997fe21128ff9edcb913b12aa313a4712f9f6ee47009af3fcf9187328b9',
       '714b26bdfb628cfbdb0fbe480cb09693f49d33fdc9e7c8928d6b56170135d38f', 'result_046136d4fc94dc961bb53ad5', 'match_ee40b8c4fb51bb865ecf8995'),
    _m(T_E3_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'A', 159, 'last_agent_standing', (591.0, 603.0), (1112, 1111), (0, 0),
       ((159, 'kill', 'B', 'A'),),
       '7917da72f367f42805d006522787012541f6bbe05db02243ca647d23ea2a9eab', '179900534d8ad061e5c32459de2c6e962f110a93e91e4b4a5cbf5ac10fea4f31',
       'eadb1b5a4b68c1589601a2310dcd0fe11e8398d5df26d45c3629e4c214677592', 'result_2b98f9edd2ab1e5306c4399b', 'match_971320136d8254c37edf6128'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '221a87531a82ce230b7463b257e2cfea979f9016508df3f842d3c347463512ff',
       '94ca784a80e5eb0cb40e9aff7f2f8d8296e4b8272a55e7829ed446f99a0b5a50', 'result_04dcb13855c8776a13b955f1', 'match_a736cad1c7f4160cae15b11f'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '223febf5359a8029b9fd25292ee0ead4a547b1a101a112da22321701bd94e105',
       'b2f09c103d348ed09cc4bd46bd539da5701cf6e6c8ae549908483c47214e05f9', 'result_fb0c29d974c8e764bbdce68f', 'match_f7d7838cebfb1e01b7d7fa29'),
    _m(T_E3_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '09cd2018311b92adde346c6785f3e860628de19b6bb4931178f7d9e636ed8ceb',
       '8c03317e23b6f0cf67f2d1a6ba71405f272805d0c6043818f4bb238695338e89', 'result_d7eefce222fe6944e9030def', 'match_c32e4eafc0ae3a5fb7b400b7'),
    _m(T_E3_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '221a87531a82ce230b7463b257e2cfea979f9016508df3f842d3c347463512ff',
       'a218e4830a7efa22b64246a6c0c49e563a464d166a79829e44be15c83ea7318c', 'result_ed54768e8bd15a833daa97cf', 'match_2de325508a53a6ff09f594a0'),
    _m(T_E3_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '223febf5359a8029b9fd25292ee0ead4a547b1a101a112da22321701bd94e105',
       '4fd2d76946aae454902b85dc5e084a3d5e32fe6ab8475219977d170419d7896d', 'result_b2674e55c98191e6b8a341c5', 'match_ad65aa7a87c5d4fffa506c93'),
    _m(T_E3_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '09cd2018311b92adde346c6785f3e860628de19b6bb4931178f7d9e636ed8ceb',
       '090d87a4e12d0a05552e084c39df3eb19b92e107b5363caf561bbc5fc70c8f98', 'result_52b419b888efe86e05e5d7d3', 'match_a936e643564c427fbde0695f'),
    _m(T_E3_ID, 'e3_jam_sniper', 'e2_min_guard', 1, 'A', 4, 'last_agent_standing', (9.0, 3.0), (28, 18), (0, 0),
       ((4, 'kill', 'B', 'A'),),
       '0eee3e6152a34da694baa7a216ed349ea6c806d0cd98fa32330ad37540e04023', 'a3450c3f56f22405f67c79a2baf8198a62eccf67f97504bf1c012972efbe1309',
       '875d9d65b14aad9fd56d5ff62f4381932fa4cdbf35945bc2628b3ff83c6570fe', 'result_d7a53ca640e6283c683a8f5a', 'match_f5980341e29ebdf398edff53'),
    _m(T_E3_ID, 'e3_jam_sniper', 'e2_min_guard', 2, 'A', 4, 'last_agent_standing', (9.0, 3.0), (28, 18), (0, 0),
       ((4, 'kill', 'B', 'A'),),
       '0eee3e6152a34da694baa7a216ed349ea6c806d0cd98fa32330ad37540e04023', 'adfee9152e7018e113f2d9d493e0eeb3183ca439661a830cab7b43d3caf8e4e2',
       '254d27aec052ff054a51f11bdf7b19a84327e575f65831c1f6fac8e09248136b', 'result_d17f865c65c653f7def57ee5', 'match_66ebc86586928592dc9ad637'),
    _m(T_E3_ID, 'e3_jam_sniper', 'e2_min_guard', 3, 'A', 4, 'last_agent_standing', (9.0, 3.0), (28, 18), (0, 0),
       ((4, 'kill', 'B', 'A'),),
       '0eee3e6152a34da694baa7a216ed349ea6c806d0cd98fa32330ad37540e04023', '5743db4c509767e47ac19e55cbdfb2c211f738cbceb0fd92d0928c6cfd92594e',
       '9186530a57ce04dabddd7396bfbc0f0cc1676ef4b070b2038a7963d7ca733d4e', 'result_19917954538fe367881f71c2', 'match_029e16dbd9a80370db5310c2'),
    _m(T_E3_ID, 'e2_min_guard', 'e3_jam_sniper', 1, 'B', 4, 'last_agent_standing', (3.0, 9.0), (18, 28), (0, 0),
       ((4, 'kill', 'A', 'B'),),
       '4dbf183065fc8dee548231f2ebec8f7ccc1540014af1fadc0169e913789f1f50', '2c4c09d46b7a730d43339ef0f9b0b7021a895f92886b70d0133a2ddd38ebd48d',
       'ed1fd162aa039b8f2c80acbe3631dba06f3b911f9ca4ad7694797b25e40ab15d', 'result_accd29c16270a718f87170d1', 'match_2915226b47f4b992bdf5fcb7'),
    _m(T_E3_ID, 'e2_min_guard', 'e3_jam_sniper', 2, 'B', 4, 'last_agent_standing', (3.0, 9.0), (18, 28), (0, 0),
       ((4, 'kill', 'A', 'B'),),
       '4dbf183065fc8dee548231f2ebec8f7ccc1540014af1fadc0169e913789f1f50', 'bf78a7f84253d3b1f5524b68d030552291d6c5ddbeb2693b6a6eca374a04bdfd',
       'd8dffea341b812804a23eb2400b78a558a60aa9bcf4137c1c7e616f993b398bd', 'result_c6a8b12bce214dcf8b412ed7', 'match_137f0447e6e8b1e40599b8a9'),
    _m(T_E3_ID, 'e2_min_guard', 'e3_jam_sniper', 3, 'B', 4, 'last_agent_standing', (3.0, 9.0), (18, 28), (0, 0),
       ((4, 'kill', 'A', 'B'),),
       '4dbf183065fc8dee548231f2ebec8f7ccc1540014af1fadc0169e913789f1f50', 'ce6639e024c5be9cab2b33ab16ca4c1024760bd217569192244bbcbf8d1d00b4',
       'ad8d20ac4e7f58d3db33f9a2baae3800468a3a192a93f7fd58df52751838ebe3', 'result_af4478ad8e5746e2a7cbac9e', 'match_dc160263acfd64b7a1e58380'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd9402ec6c38d9e73f102956d3a7baac6855eac3b4c28278fa94c5c9230e6fbb5',
       'fd2a88efba0e3110456d2960309966ec0d4f127ed2dc9a89ce48ca94a301e2c4', 'result_f42aace4402a9ea894cdf94c', 'match_26e6b773193f6f83f6b1fc41'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '60cbef2596b9c5b6e6f5446a3438e7f294fcc7ed8ecf2ba43b58ede47a415b7b',
       'a5a0a11662a55468cedfc0504113acbdec96742dbf4201110f1df579bef7ba2f', 'result_2cf7d88a8a18169929cc97f8', 'match_cf9c39c002347e2e3516bbbf'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '412d63c889d737c535205b50bad1900afbe436080dee1559d8f490aa92fa2940',
       '7bda83b8cbad6890b1c8561e83a99e26cdb545b67cbcbb8e4d0be16b768b8e9d', 'result_abfa2aa2b9987f297383770f', 'match_84bbf6db805054318f628d61'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '0e3c0a4abbc455aa8b062d27fc70336ba9c5eee9e3f7f8d56b9d1370c5fc2b6f',
       '74ae827c26694b7d1db4b453beece45e0d6c7e67ed1dba366cd16eb777da2ccc', 'result_6dc93d05edfa4dfa1af6681f', 'match_f99bd1a9c4aa6961d6c9ee6b'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'f3d0804bd10cf464fb9a229f3c993bac03bb84b418d22284293efa31ad0e1296',
       '6d1191481be63cd23d690e03ec106b7b21f15d13878f3398053c880f8c8df937', 'result_f6a8b6da1b007ae1f4a88794', 'match_ff3b9943a1816f51c226a7a1'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'c32ba4a574b5455b6b20897cb636cca2a5b2088509c2c3c640d37418e433476a',
       '8d2a449375c978c43e8d0d63bb649c9ffae46b4f2de7a7145b0ea4e340ef7525', 'result_63f154742933304e70a346db', 'match_7381ff680a55fe63438ded7b'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', 'af89a8fc31a4847b0354d3c6dda8b47c92ffd419b7140b7c2f6b89d86e983316',
       '9cc3192b704608e9c85402c975bfcfaf2c1d88c1195b09df99e797bff18a8cc7', 'result_165bda90929bb6b6ca2240dc', 'match_ceaab5591b1d72e0110e7ae5'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '5704ab1bd4fafe7301bfda5a88b981cdba47df63b8df17a7972d93abf5c93ced',
       '4d95ce6020c1139bc719cdaa7e9f64635c26aa790db1174c7c282be30641a5dd', 'result_2b9c4c2d6112a93f11262103', 'match_539350953af083a9873a38ab'),
    _m(T_E3K1_ID, 'e2_repair_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 8000), (0, 0),
       (),
       '9da5f00f2c6bf0aed02a40ea2b69e8b469e9d9b833561c4f5c2a0121e8479b26', '180ecc277bcc84d646e4bb5e9999682c765800737d64ae42df27a691265d0a77',
       'dd651c6d9ffe3d03d564f1098687addf45b23d92482ba2d1b20094f3160bf9b5', 'result_deedd386b881ea9fcfcb8ddc', 'match_3f98653d1c79df3c33155c89'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 1, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '259f457050e850ed1e952cda52ac13ea40deb0825e0dbdd3b8b79a40bfd019ee',
       '83f6c3f748ef7ea65d41c9ff13cea8e19b76350d7952263eae54599aa50b901f', 'result_cec8fb1ca0f231fbccbf7418', 'match_37e424d852692bafda78afcd'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 2, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', '48a8433025c93dc520197ade2b6b3caeca1a3576f74c0cf9fa7c5efc32619ebc',
       '06890016ceb2e538495d68558735b9e6a49194e096787b1f0738461ec6a04e73', 'result_653c2cd6c65b92a18024ce1b', 'match_2c73c4a19e83f309101719d4'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_repair_guard', 3, 'A', 8, 'last_agent_standing', (13.0, 7.0), (64, 56), (0, 0),
       ((8, 'kill', 'B', 'A'),),
       'ce5815afb275b8bb75b02c82adb96b693d958104c3ed5ce424cf4ea95483a17a', 'fc4c0e3c0d71e1b255ce850240d5b8796f6c21e7a6c6305f4288cef10f557477',
       '2d4f82dbcb327d4bed1d6af026895d9c60236a06226907ebfdb308140b0b38b0', 'result_6a07de2ac277401cc48185d2', 'match_ee87c599b2d9697903905802'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '2bb8ab0f906d82eb45aefc5f508dad53f69da174c3f1557b04f49e05d22118a1',
       '39265bf25fb22abef99cf0cd6fa864c8ad9103244c8a6776ea04f48e4b2f1db6', 'result_1f2c29036f4696e306a37605', 'match_1562f473ad5a9d08e3224eab'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', 'b5d1e9fb09c56646d143f95ab9f73d2d44cfa1b569670f2facd86c64d0f103af',
       '83fcf0490f65734dc33a7b59aa9d3be9b51ba76644dbf61e96021d1f0a67abb7', 'result_0f4bc3d6c4b78f9632cfb0e5', 'match_344b742a7a9a5c5dcfdba44f'),
    _m(T_E3K1_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7000), (0, 0),
       (),
       '6102c3de429897133e516d2752f3413126bfb17e75d771dd8c24f82ede99b9d1', '1cdd6193c7da446b3c4762e14b34fb3fb5f2deb63dc63150a303cf672cf46671',
       'c69728d8645455b6d2a671ec2262f0ba62e870a65ce874223e35251b69c5fd20', 'result_e070da3d4e20e66bb2548b95', 'match_1c120435c9f814ea15ccc771'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', '3d06408701d7b98342b5d4ab5135fab3c3f4083f2c34395cbb9063a5744a5f30',
       'baf1476758e41a8d5bbf8a46f7382dd1f4a6bef815f21bc17946bd8b74faa26d', 'result_d90f5aab49a3117202a53e19', 'match_00f4458ac66c7ca4cdee9e17'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', 'f4b65609d5eadd66281bf3297d9dfd3a99d64b5e71a3995d959f9894a9d27761',
       'cc410183691bd6bed1c4f53c7e446d248717f23ea12b1306bdced5bdf16477fb', 'result_998cda0c5aed24bfde00d5b6', 'match_64722877e593f0b39b15ce43'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7999), (0, 0),
       (),
       '5b22c806e67f122ecf8d8603aba7b5e7411d9e65e8293f2bb182d2a756c2940a', 'e50e1caafad7ddedbe6227daed4cc58c3bec64f32882bee5859ba7e20eff0117',
       '067dd7500dc4a2e57234e080b69a07202eef2dbad7096fd67ef8e27c32afe559', 'result_c9f3253c686c2a84b293a9d2', 'match_1f803694e54e3ba3fbc5db10'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '893b3317b21bece60ece7c7b8b9843b5a806996b7da1ddc2a9b38d33b8a2dcb6',
       '6bc04eea5099beae7e837d2942b3783896c99bc91be969ad20e3dc73217c0fa9', 'result_e5bb0edfd59bbf93ac65c0b0', 'match_44226083f187c4690ffa53cb'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '4269b0fd612ee787b3603364c3d3b14da140c088c5325ba5ef56dd5d5d13a731',
       '679906c9aa3a2a3b9be529fdd43ecffc1cac1ad4dd8620ffdce461e1dae02f11', 'result_c926f0b61f6061ebf95accbb', 'match_502a70173f44eef42fc64beb'),
    _m(T_E3K1_ID, 'e2_sniper', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'a80110d5f372356df028942925bf889754363334f65cb7c5e911e0ac9c57c59e',
       'cd209dc87b71c5f478ad5738c801f0bd6e146e3cf7d4886a9def37afc2c1d5db', 'result_38e97b18b4c70750f3a0fbeb', 'match_736ce6870e1620672d09f529'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '6b60219434e79540b4649543ea213fa352705d69a3b15e46e2f1589417ce281e',
       '221b6c859c8099fc8b2e2a456845d3446109320850e7c26c3f2fa2977f695c53', 'result_3f5ea7fb667001db20376e39', 'match_dd552d384807c848dea9eede'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd86ad09d2cb6d4cbe7b8e2fb69768752a18fa48a23d9f0ba70210f4eacbe8a8b',
       '9bb1a07b67587af4c0f5f2b23ea74a560a5269e93a58357242aa6e7a8fe13677', 'result_f95277637dce4be9d7af7e0c', 'match_1e1ea048c037b39cf77e632a'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '84838e5beb85b105c201e657b2e4139ff0d45c96db0b4d8b25719c0c8c7916a7',
       'd737b0f9cddff74c40529ab1305492ea44e54431f76e7d34d57093d27cf11172', 'result_7515a0f002891045ea94385f', 'match_38ee28febe71a13039c8bd2b'),
    _m(T_E3K1_ID, 'v4_probe', 'v4_probe_twin', 1, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', '36c7ddc6d9da27181bc8b521806304d217a26c424086c3df75e806bfefd8d6af',
       '699c036522d630138caeee3fc275655923e1f713173bb9f91bc4f1c943464fc8', 'result_ac2530d789fb85aa82a8d57f', 'match_d6dff5b84cd89043e211d8a1'),
    _m(T_E3K1_ID, 'v4_probe', 'v4_probe_twin', 2, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', 'a2535a94d2389c383847aaf241d423e59e9e2a00ccbc0879b6f07485443e017a',
       'f0a1d2dfbb8a5762506f406bcfe100a41fa030f9dc52c7af78379c750e026ac9', 'result_1699d222c7653e10b33e80b2', 'match_5b9da567f0310f69edaf4875'),
    _m(T_E3K1_ID, 'v4_probe', 'v4_probe_twin', 3, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', '237f7de4a2f479157475d9436a7f46a1c18fff77a3e7709f816118cb16a909bf',
       '7385fbbfcf13f613e50bbe9230244ac0883b1f54bcfd261508bb4300b00fecc8', 'result_a3c1ae36ec20d5356ab91c9e', 'match_54f82f88cbc03e2345210284'),
    _m(T_E3K1_ID, 'v4_probe_twin', 'v4_probe', 1, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', '36c7ddc6d9da27181bc8b521806304d217a26c424086c3df75e806bfefd8d6af',
       'c96da0309ecec6455af52950a7222f99375641c90fccc9c68827810a832545af', 'result_4078b96e9a70d74490b6c543', 'match_3475c419987327fc839b0fb2'),
    _m(T_E3K1_ID, 'v4_probe_twin', 'v4_probe', 2, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', 'a2535a94d2389c383847aaf241d423e59e9e2a00ccbc0879b6f07485443e017a',
       '52afa3125da23d82c666b77dcf3575be6fe0b0f6ef27eef2bbd16105d3034c5e', 'result_7aa5d34b95934eceba0f3d9a', 'match_ab036bc52ac8e2d974e21cdd'),
    _m(T_E3K1_ID, 'v4_probe_twin', 'v4_probe', 3, 'tie', 2, 'all_agents_dead', (6.0, 6.0), (14, 14), (0, 0),
       ((2, 'kill', 'A', 'B'), (2, 'kill', 'B', 'A')),
       'ef6a24783a407d5046390b5d164fc81947faf54392cf3977df0b368884730f40', '237f7de4a2f479157475d9436a7f46a1c18fff77a3e7709f816118cb16a909bf',
       'd7021a29d67e78dbb18252abc35ebcec439e54ec4a8b572574a42dfc2b14f122', 'result_96389856653dca0b7c553261', 'match_17969e6827be4cbc444369e2'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328), (0, 0),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')),
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       'f8a153c9b8d07f46cb2b84d07b1f453cf04a56dd701877457038cbe00c839bb9', 'result_b4613eb8208176c3a63d0e0e', 'match_d7f1abba6508a1ef09454aee'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496), (0, 0),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')),
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       'd3a575687ce545e389cceabf047b5cc204ddd06cba912a75b565e1230a6eacca', 'result_04654a4f2cf9d91c20b9b597', 'match_3bfd127a97e81671ddcbc824'),
    _m(T_E3K1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301), (0, 0),
       ((43, 'kill', 'A', 'B'),),
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       '4078497fd283190add9d4aa64df87d16c860259792f8e542d81fd10e1e6900d5', 'result_dbcb6ac2b9f0292556ed23ae', 'match_92dbf63e8c4a522db47eb848'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328), (0, 0),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')),
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       '4679e074e00f32748194d835e24f917fda808e8a0dc92b1cdb7ffb4a5ad4f2eb', 'result_9137fa5119ee7df891a9f0dd', 'match_3fd22be4150ebee67cde298d'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496), (0, 0),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')),
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       'e86cf005d0076054bed3a22cd113c3b8f6e3f1fb67a46b63053419d62789b0b0', 'result_4f0fe460a7fc1f149d789943', 'match_6feddbcfe12eec1108c9040b'),
    _m(T_E3K1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301), (0, 0),
       ((43, 'kill', 'A', 'B'),),
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       'ef68aa268bf5e39015cda419e33598c030b3f7a4ce685058d12239efbdb341af', 'result_f22fc7b5b214dc65bba474c5', 'match_b69b48183762ffc8d8db32db'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '221a87531a82ce230b7463b257e2cfea979f9016508df3f842d3c347463512ff',
       'ab5e727391c4aff1275027fd7c04017c0bdb1b9416a89f00ae5e7f714458970b', 'result_b82592f367530656794e0abe', 'match_20af6278f6429c5130d2c3f2'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '223febf5359a8029b9fd25292ee0ead4a547b1a101a112da22321701bd94e105',
       '046366e9b8cbc4841bcc52122dbb5c8da48931eaf219de392f70b99a944f2a50', 'result_77821009393c9dae03dd1151', 'match_066b0e79be8d5c3603b5b5a1'),
    _m(T_E3K1_ID, 'e2_disrupt_guard', 'e2_disrupt_guard_twin', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '09cd2018311b92adde346c6785f3e860628de19b6bb4931178f7d9e636ed8ceb',
       '3bc03706f4ea948276c6e4e1ffc13e613cc48f930fb55cdd0258f0f366db9c0a', 'result_30d02a2bef8fba91adb4160f', 'match_ff33e64e0a213e8e3907c447'),
    _m(T_E3K1_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '221a87531a82ce230b7463b257e2cfea979f9016508df3f842d3c347463512ff',
       '41e36597a48790e59ed21f9a8cbecdbf2beae32b12246c2f2b5035d367b15dec', 'result_06bce0eeecb7f331f9e4d263', 'match_1e6c6bbd55fdb694c97a80f4'),
    _m(T_E3K1_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '223febf5359a8029b9fd25292ee0ead4a547b1a101a112da22321701bd94e105',
       '8e5e2ea800744395587d535e0f8d67010d7e5daf3c722999a3ea740b55f45fba', 'result_b89aa887c689cdb7819627f2', 'match_33ee728260906c742c8a34b2'),
    _m(T_E3K1_ID, 'e2_disrupt_guard_twin', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000), (0, 0),
       (),
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '09cd2018311b92adde346c6785f3e860628de19b6bb4931178f7d9e636ed8ceb',
       '38e282b6a144af06ad6d476a3378d7f1879be71d44a7ae33d72834e096b8d996', 'result_c68f643e6747569ef7413c32', 'match_1644d1f65621c339549495ce'),
    _m(T_E3K1_ID, 'e3_jam_sniper', 'e2_min_guard', 1, 'A', 3, 'last_agent_standing', (8.0, 2.0), (21, 13), (0, 0),
       ((3, 'kill', 'B', 'A'),),
       'd824044c45e5d5943f451c026b867a5e1ddcefd0d960dad2a108f48811b70938', 'c35d3f6a542a362fd23cc726cf8fc8ffeea053b7a0bce2580510f68cdeb5888f',
       '7013d01593399f78b923e053eb6d57cc6217f2137c0ceadd142873cb66f05a02', 'result_f4aefc0ba0900df278baee78', 'match_874725c5e8300dc900e4bf08'),
    _m(T_E3K1_ID, 'e3_jam_sniper', 'e2_min_guard', 2, 'A', 3, 'last_agent_standing', (8.0, 2.0), (21, 13), (0, 0),
       ((3, 'kill', 'B', 'A'),),
       'd824044c45e5d5943f451c026b867a5e1ddcefd0d960dad2a108f48811b70938', '1bbbfc7896c67d74c6ee8a4159112ce21d4b76db23d4de2c41c122f0ef00daa4',
       '20ffc9bc77488ec472c055e64689fb192ea51050762dfc0019b832be13e14b03', 'result_c562d08a124c7c991d035e8a', 'match_e7a6bb41b15605a892e25f66'),
    _m(T_E3K1_ID, 'e3_jam_sniper', 'e2_min_guard', 3, 'A', 3, 'last_agent_standing', (8.0, 2.0), (21, 13), (0, 0),
       ((3, 'kill', 'B', 'A'),),
       'd824044c45e5d5943f451c026b867a5e1ddcefd0d960dad2a108f48811b70938', '14d2dc53dcec9460f3ea5d67d04fd97a23c8c37c2c494f7bc2c7c6ef44cd167e',
       '4c8e0a91fe0aa33c75bb1a91a4e0fd444fc0769e7e1a5258d28f1754fe462172', 'result_35544b07f732efdbd01a8892', 'match_21eb371bba12149f0060a6f2'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e3_jam_sniper', 1, 'B', 3, 'last_agent_standing', (2.0, 8.0), (14, 21), (0, 0),
       ((3, 'kill', 'A', 'B'),),
       '53aabbd0b44fd53eb1d108765588cdfd807b05b65be8915804a066fe158ed9b3', '28b8cf6538ae5aee2e80e9340cc089ba39b814f9a6f4b1964b7d0f07981df57a',
       '4b3f446c43a6769991e98fc303c6cb40551a11992a88d5a8f15c6061f1997d16', 'result_74dacc1c7dc70daa962ec889', 'match_cf4a7c75f4df3d73a9bb9c2c'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e3_jam_sniper', 2, 'B', 3, 'last_agent_standing', (2.0, 8.0), (14, 21), (0, 0),
       ((3, 'kill', 'A', 'B'),),
       '53aabbd0b44fd53eb1d108765588cdfd807b05b65be8915804a066fe158ed9b3', '25868d12524911337242f0ae9c66f289e35c8607c39c77d88e3b38c7f5dd9315',
       'ddbfd9ace4a18e87804547857c2a51aaef1b5ebb512614d5272c7b0dad6ec49f', 'result_11972695c39aaeb5d4c41d8d', 'match_af09c4b99f5bf6cb4a831825'),
    _m(T_E3K1_ID, 'e2_min_guard', 'e3_jam_sniper', 3, 'B', 3, 'last_agent_standing', (2.0, 8.0), (14, 21), (0, 0),
       ((3, 'kill', 'A', 'B'),),
       '53aabbd0b44fd53eb1d108765588cdfd807b05b65be8915804a066fe158ed9b3', '71077728b8643d6cf58181d45f8615daecfef172f133908a2a12d3b5d316b322',
       'faab08b7ba730872cd651196f7f9040411d87f3dcdac19faa308f4e372305d38', 'result_e7921af3201dbeb3fe27a81a', 'match_e870e77055b1386d113191f5'),
)


def test_frozen_corpus_covers_the_declared_matrix() -> None:
    assert [
        (case.ruleset_id, case.seat_a, case.seat_b, case.seed) for case in FROZEN_E4_PARENT_CORPUS
    ] == list(corpus_cases())
    assert len(FROZEN_E4_PARENT_CORPUS) == len(RULESETS) * len(PAIRINGS) * 2 * len(SEEDS) == 96


def _row(ruleset_id: str, seat_a: str, seat_b: str, seed: int) -> FrozenMatch:
    (row,) = [
        case
        for case in FROZEN_E4_PARENT_CORPUS
        if (case.ruleset_id, case.seat_a, case.seat_b, case.seed) == (ruleset_id, seat_a, seat_b, seed)
    ]
    return row


def test_frozen_corpus_exercises_the_paths_e4_changes() -> None:
    # Guard: the corpus must contain the long pass-order-sensitive
    # stalemates E4 targets and the early captures it must leave alone, under
    # both parents, or its identity would say little about the forward path.
    for ruleset_id in RULESETS:
        rows = [case for case in FROZEN_E4_PARENT_CORPUS if case.ruleset_id == ruleset_id]
        assert any(case.reason == "tick_limit" and case.ticks == MAX_TICKS for case in rows), ruleset_id
        assert any(case.captures for case in rows), ruleset_id
        # lambda = 1 (E3 G.4): no entrant is ever silenced for a whole tick.
        assert all(case.silenced == (0, 0) for case in rows), ruleset_id
        # The canonical multi-pass sweep (review Sec D.2): a 1000-tick tie.
        stalemate = _row(ruleset_id, "e2_sniper", "e2_disrupt_guard", 1)
        assert (stalemate.winner, stalemate.ticks, stalemate.actions) == ("tie", 1000, (7000, 7000))
    # Review Sec L-4 and L-5 under the primary parent: the probe mirror is a
    # mutual elimination at tick 3; jam sniper v min guard a capture at tick 4.
    probe = _row(T_E3_ID, "v4_probe", "v4_probe_twin", 1)
    assert (probe.winner, probe.ticks, probe.reason) == ("tie", 3, "all_agents_dead")
    jam = _row(T_E3_ID, "e3_jam_sniper", "e2_min_guard", 1)
    assert (jam.winner, jam.ticks, jam.reason) == ("A", 4, "last_agent_standing")


@pytest.mark.parametrize("frozen", FROZEN_E4_PARENT_CORPUS, ids=lambda case: case.label)
def test_parent_is_byte_identical_to_the_pre_e4_freeze(tmp_path: Path, frozen: FrozenMatch) -> None:
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
    assert observed.cpu_sha256 == frozen.cpu_sha256
    assert observed.writes_sha256 == frozen.writes_sha256
    assert observed.match_id == frozen.match_id
    assert observed.result_id == frozen.result_id
    assert observed.replay_sha256 == frozen.replay_sha256
