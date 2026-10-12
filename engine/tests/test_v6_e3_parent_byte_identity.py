"""V6 E3 parent byte-identity freeze: whole-tick disruption as it behaved before E3.

E3 (slot-limited disruption, docs/research/v6/V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md)
adds ``RulesetPolicy.disruption_slot_limit``. Its default, ``None``, must be
*observationally identical* to disruption as it behaved before the field
existed: a disrupted process stays ineligible, and blind, for the rest of
the tick in which it was hit. That claim is proven here rather than argued.
The canonical replay digest, ``result_id`` and ``match_id`` of the fixed
matrix below were recorded against the unmodified runtime at ``9d34b01``
and committed *before* any disruption code changed. Every later build must
reproduce them byte for byte.

The matrix is the E3 representative set, run under both E3 parents and
under stable V4 (which is gameplay-identical to the K=1 parent but carries
its own identity):

* ``bytefray-rules-6-research-capture-hold-k2`` -- the E2 parent of the
  primary E3 treatment (K=2);
* ``bytefray-rules-6-research-scale`` -- the K=1 parent of the companion
  treatment;
* ``bytefray-rules-4`` -- the stable product Ruleset.

Pairings, all with the tracked E2 research fixtures
(``tools/research/v6/e2/fixtures/agents``, LF-only by ``.gitattributes``, so
every source digest -- and therefore every identity below -- is the same on
every platform): Global Sniper vs Disrupt-First Guard, Pure Repair Guard vs
Global Sniper, Spread Sniper vs Disrupt-First Guard, the V4 probe mirror,
and the Guarded Painter mirror. Each runs in both seat orientations at seeds
1-3, arena 512 and a 1000-tick limit -- the E2 matrix's own parameters.

What is frozen, and why exactly these values:

* ``replay_sha256`` -- SHA-256 of the canonical schema-4 replay bytes. It
  covers every tick's events and their order, scores, memory diffs, each
  entrant's per-tick ``cpu_used`` (the executed-action count that
  disruption suppresses), and every process snapshot, including its
  tick-level ``disrupted`` flag.
* ``result_id`` -- the canonical result identity (winner, termination
  reason, ticks, score, and each entrant's termination reason, statistics
  and metadata). ``result.json``'s raw bytes are deliberately not frozen:
  they carry per-execution occurrence metadata by design.
* ``match_id`` -- the request-derived identity, pinned so a change to
  identity derivation can never masquerade as (or hide) a gameplay change.
* ``winner``/``ticks``/``reason``/``score``, total executed ``actions`` per
  seat, and ``silenced`` -- per seat, the ticks the seat ended alive having
  executed no action at all (whole-tick disruption) -- are asserted first,
  so a regression reports *what* changed before the opaque digests do.

A mismatch here is an implementation defect in the ``None`` path, never
something to re-bless.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest
from battle_engine.agents import resolve_agent
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.replay import MatchResult, TickSnapshot, iter_replay
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V4_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

from tools.research.v6.experiment_harness import prepare_benchmark_data_root

ARENA_SIZE = 512
MAX_TICKS = 1000
QUOTA = 8
SEEDS = (1, 2, 3)

E2_ID = BYTEFRAY_RULESET_V6_RESEARCH_CAPTURE_HOLD_K2_ID
RS_ID = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
V4_ID = BYTEFRAY_RULESET_V4_ID
RULESETS = (E2_ID, RS_ID, V4_ID)

# The representative pairings, each run in both orientations.
PAIRINGS: tuple[tuple[str, str], ...] = (
    ("e2_sniper", "e2_disrupt_guard"),
    ("e2_repair_guard", "e2_sniper"),
    ("e2_spread_sniper", "e2_disrupt_guard"),
    ("v4_probe", "v4_probe_twin"),
    ("e2_guarded_painter", "e2_guarded_painter_twin"),
)


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


def run_corpus_match(root: Path, ruleset_id: str, seat_a: str, seat_b: str, seed: int) -> FrozenMatch:
    """Run one corpus match and describe it as a FrozenMatch."""

    prepare_benchmark_data_root(root, [seat_a, seat_b])
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
    final: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, TickSnapshot) and record.tick > 0:
            for agent in record.agents:
                actions[agent.agent_id] += agent.cpu_used
                if agent.alive and agent.cpu_used == 0:
                    silenced[agent.agent_id] += 1
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
    replay_sha256: str,
    result_id: str,
    match_id: str,
) -> FrozenMatch:
    return FrozenMatch(
        ruleset_id, seat_a, seat_b, seed, winner, ticks, reason, score, actions, silenced,
        replay_sha256, result_id, match_id,
    )


# Recorded against the unmodified whole-tick disruption runtime (see module
# docstring). One row per match, in ``corpus_cases()`` order.
FROZEN_E3_PARENT_CORPUS: tuple[FrozenMatch, ...] = (
    _m(E2_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       '6db6f07b533c7dcb55ec8caa5623faf6e5d7e86541d607279ade531ecf3ccdc0', 'result_6f9784ee586473975f94e8ba', 'match_f592e0917a67b7792d46f7a0'),
    _m(E2_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       '9560038c207d9cef11d91d83889f41903c2cb3bbab89b3e8bdd3fa9823140696', 'result_6430904083ad5af60b2d1df2', 'match_a05c12cbcaf7262228262446'),
    _m(E2_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       '98bf60cbf4e620187b6330b8870b9c1b4e3482b497508ac721f6183ee9c830ed', 'result_66184ba22ad7274c225c932d', 'match_54399442f74db4eab7262574'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       '05f06192fc6dd8ccd5e5057e340727ae624bce5de1cb4735caeb96ef7575ca17', 'result_156cbbb837e76d687e1d0cc3', 'match_d2d3ac0e3b37721efb3a127e'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       '99fcb548d13858710a2cd10557b2bf63f4023ec2ba74e06b7be5e59843b54383', 'result_e7de3a10774830f636f99405', 'match_1e433f7e37eb713e74f3f951'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4000, 4000), (500, 500),
       'e1699cf78d7f981755a07ee6f5c048dabc1fa659e56241019606705bab586d68', 'result_3af627a862885c0e8bac636d', 'match_ed640349fa5ed31c6d3ac7a2'),
    _m(E2_ID, 'e2_repair_guard', 'e2_sniper', 1, 'B', 2, 'last_agent_standing', (1.0, 7.0), (2, 16), (0, 0),
       '310c3a0949ade95a188eb636e5549a348f2430eb09dad2555f136321edd82600', 'result_d485799710a4b6cb96ee56e9', 'match_3dc06ad23089839e4f8a2f10'),
    _m(E2_ID, 'e2_repair_guard', 'e2_sniper', 2, 'B', 2, 'last_agent_standing', (1.0, 7.0), (2, 16), (0, 0),
       '25920f8768834322ecb97b61c883402f0774097cc24e387f7c5cf04eafac0781', 'result_47b20e3b63da526d636a57a1', 'match_6eeb7c08f813bab4ae320191'),
    _m(E2_ID, 'e2_repair_guard', 'e2_sniper', 3, 'B', 2, 'last_agent_standing', (1.0, 7.0), (2, 16), (0, 0),
       '900a2d9f82128d9b0430b21ffb3620b2019808c2368a89f81a86899ea460585a', 'result_383417ba66ce9259dd6dea0e', 'match_663e1b07f69f83a3a8e92e58'),
    _m(E2_ID, 'e2_sniper', 'e2_repair_guard', 1, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       '1628c0880759cd7998ea16ea7a4236be2516b662b5dfabccd20469b92e2653db', 'result_bcc05b1e7871d9968e421300', 'match_0135bc309de0e3b9362debba'),
    _m(E2_ID, 'e2_sniper', 'e2_repair_guard', 2, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       'cddf5fa835cc0e38176efc10aa8a3123f462f8a8103a290f5fd9c6dbeb03a3e0', 'result_d42bf02058d0ff6143d9e1ee', 'match_09f7ab437924f10b0398de35'),
    _m(E2_ID, 'e2_sniper', 'e2_repair_guard', 3, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       '1286803330fbe134dee7f2ef1b50ac7de58edb6cee354ae4d7dfbad545a248bb', 'result_aa1e848618bf693fffb7fc33', 'match_36ce7a80cf1c02aab7e17918'),
    _m(E2_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 1, 'A', 3, 'last_agent_standing', (8.0, 2.0), (24, 2), (0, 1),
       'f17b2ccc184151600ce0c0c0ecae76eb4d62c578251e7eabf8bc6cea16a97664', 'result_a50578c639ee53a4beaddf64', 'match_936e860b524e30b887cce70d'),
    _m(E2_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 2, 'A', 3, 'last_agent_standing', (8.0, 2.0), (24, 2), (0, 1),
       'af67ccad70b431fdaa7fb605c332ce7e9015d60f46182fd74b7912ae06059c33', 'result_27caae05f6c5337e7bc11c57', 'match_e84c372bf54e85f80d7fc542'),
    _m(E2_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 3, 'A', 3, 'last_agent_standing', (8.0, 2.0), (24, 2), (0, 1),
       '9e05b2f182f32cd986a0e037c1e6d765ae8c7d84c522b872d9ebe5ac35dc8e7f', 'result_5b0d35c67dfa22f58c5923d4', 'match_0dc35618dc2f8b0a856f0571'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 1, 'B', 4, 'last_agent_standing', (3.0, 9.0), (10, 24), (1, 1),
       '45a37865d99e0ece4186284c577ce9e2eec376a91481b8f57c034f2b814c47cb', 'result_73e9beb910c7b34d7b635159', 'match_ae2aa421fe250fa20e6aafc5'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 2, 'B', 4, 'last_agent_standing', (3.0, 9.0), (10, 24), (1, 1),
       '88a1d80fd88cb070f009634755fa4f4917aeaa4cd11e85c3a07af0e218c15499', 'result_afed0cf9061e2807f2db806f', 'match_2c12eb28db9889123bc89afe'),
    _m(E2_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 3, 'B', 4, 'last_agent_standing', (3.0, 9.0), (10, 24), (1, 1),
       'eac2d8ac98cfafcdd764f6d6c27cc332dfab3e13cd387f80a53ed9daccdebd8c', 'result_88dc51fbd54457f4f903c08f', 'match_da098544545d3fa25b7c8c9e'),
    _m(E2_ID, 'v4_probe', 'v4_probe_twin', 1, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       '960cd6d2d9c4c56ebfef0bf9b05f8ac1722bb6c75358424d05e69c0cade73e4d', 'result_a7b19d5c68361e1f9aa9ceeb', 'match_b04b5b470afe16119cb95ba2'),
    _m(E2_ID, 'v4_probe', 'v4_probe_twin', 2, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       '486edd458c280ade87b3c61416e036b9b12576c33078c7a6a47cd1f1c693bc0b', 'result_0725f28d1ba4e209369987ad', 'match_75ee964cf605944f0b718bbd'),
    _m(E2_ID, 'v4_probe', 'v4_probe_twin', 3, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       '94c7e3bc605d977dcacf540e2ee91436e10e480e79945accba1d88dfb61ab81e', 'result_2f5964f12d74e885d63bc253', 'match_63d2f9d120f4c3d37a1cc0b4'),
    _m(E2_ID, 'v4_probe_twin', 'v4_probe', 1, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       'd003d880ef81a949dcffdd37db81a8ca30108504196e474ee57b367190d23a00', 'result_95215782c97b55a0ab9a6d46', 'match_73762a681664b41ab4de356f'),
    _m(E2_ID, 'v4_probe_twin', 'v4_probe', 2, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       '7905ec4f075e31b0e07fa603373518d79118242bba84b2630cae53bf8661526f', 'result_7766ffdda6e0b1a805a29ec4', 'match_8145103624f4a54c20448103'),
    _m(E2_ID, 'v4_probe_twin', 'v4_probe', 3, 'A', 2, 'last_agent_standing', (7.0, 1.0), (8, 8), (1, 1),
       '363593a05779a8edc346f915d6aabc95e3517432429e4364daf3f6135f4ab44b', 'result_036e72084ffd9df0a59fb6d7', 'match_aee2ebcfe2e773b7cd8cd0b4'),
    _m(E2_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'B', 1000, 'tick_limit', (4219.0, 4382.0), (4000, 4000), (500, 500),
       '7ef77098943476bfc6531805cf1ed321460823236b7215a7d33f4ca90773d2bd', 'result_659d1873a361c2c233019c69', 'match_cd02ca3b64e8b3d2c7ab2359'),
    _m(E2_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'B', 1000, 'tick_limit', (4212.0, 4466.0), (4000, 4000), (500, 500),
       '1e2978c8e6223cd809abd4612effe37e1c9dd3048fd6908f69e20a70e808cc72', 'result_6b0032e895cbfabe9bc1fb62', 'match_13f7516917f06bcf398fdc6a'),
    _m(E2_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'B', 1000, 'tick_limit', (4268.0, 4367.0), (4000, 4000), (500, 500),
       'f68ebeb880c8c3e29222b1b0d0718c97f6c501eda7538772b3879659f294d75f', 'result_db46ab95c4d0cbf78d1ea0bb', 'match_b46f41e78fa664d9c45f82bb'),
    _m(E2_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'B', 1000, 'tick_limit', (4219.0, 4382.0), (4000, 4000), (500, 500),
       'b8e9cdac1ae72ee230ac91481d18ef742a927dc20bf40e25d2e0ff33c1678447', 'result_63770fa38d729a6f70a2dee0', 'match_4eb3597f22f370f9426a282d'),
    _m(E2_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'B', 1000, 'tick_limit', (4212.0, 4466.0), (4000, 4000), (500, 500),
       '9bd84e1765568e6e9192bf68adec7a6902abc9cc797ad1c9aafa8f5ddd8a63ac', 'result_f480615444e1c52ec540c419', 'match_edcc41f57f835d04638446df'),
    _m(E2_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'B', 1000, 'tick_limit', (4268.0, 4367.0), (4000, 4000), (500, 500),
       'cafae55077cfd59c745717e296c2599722477d7bb070a0262046a968d6841df8', 'result_8bfe3bb353a0435132c77151', 'match_2a1646f99b4945b489f11bce'),
    _m(RS_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '39ab576aa787ecab0d89aec99b6385a6e8ff48f23cbda10c4a6230173fb85cd6', 'result_e8edcd1d193204ef5a134f93', 'match_48eea65ff6c4c4d0d4eb63db'),
    _m(RS_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '5d3782bb1863c2fe0c710541da65e7d700e35c49c99da698fe569f5aa914dc41', 'result_8af9360ff6779ff1eef18b3f', 'match_82e77ae33165c8852eb4e2ef'),
    _m(RS_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'bdaa8fa8d54b3bce3fd6cc9ad91b236c1c2d9ba9368aa74b1ad8999d9334b8b8', 'result_116d263b8cb55f652dbf6c85', 'match_397c5f788d0242ae64114905'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       'db266ddd7ad2c3b27754d596423134901526cd92dcc8fe55ab4c88463061de29', 'result_81b6048f9cb89f3418fa3cdb', 'match_70c7a69e1a1e895d35aaf0da'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       '13c132e477cc9e55c82dcbca32b8ca6de9ab60df0f57d08ad3ea4c7dce3d1549', 'result_05e9ca689afd97db2daea329', 'match_4f252933c2ee08026faece3a'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       'fe7662fa1583efe48f2bb6035203acc83ee88728557e56735592e711801fac0b', 'result_f139224865628ed5da2aa35e', 'match_b9d8e1ab6a296920d29c2574'),
    _m(RS_ID, 'e2_repair_guard', 'e2_sniper', 1, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       '511d259e63c8fbf9c20f0019cb4739d749c2ee8c48b779a24a052388b4a11162', 'result_247e961a02c17bc1d1b4e5b2', 'match_e9775a2175323322f274b56c'),
    _m(RS_ID, 'e2_repair_guard', 'e2_sniper', 2, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       '0c06c2527712eceb5b9c13990615bb04deb566a886bfdca1af27494759f72891', 'result_48cc11a4b6c7d186513850c4', 'match_b2528f4fe3e2ab754ea86c1c'),
    _m(RS_ID, 'e2_repair_guard', 'e2_sniper', 3, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       '4cfbb44c32751bf52356e99bb5940d1b058328995857f1ce86f6395d3ad2f306', 'result_6325ac85d08de0bb55bf7df6', 'match_ad66a47a3f161e2ede7400c4'),
    _m(RS_ID, 'e2_sniper', 'e2_repair_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '54215fb2f62dd68cea64cf37503ea01e9a034bc433ad0ed9ab77420bb0cd1a74', 'result_0e9ad1aac1513163c2fe8377', 'match_eef0c0540e0d9303c15bdf77'),
    _m(RS_ID, 'e2_sniper', 'e2_repair_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '9ebb93d3d51ddb039d1e7ca24e1c60b3e9aacdb9e63ee85b214090f831933d98', 'result_2e4f1d4ad45a0b942115fb2e', 'match_3e4115e158529ae43e7cf7b3'),
    _m(RS_ID, 'e2_sniper', 'e2_repair_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '7037d7b6c6a738d35be20377af61131009926e7a6e1a968e7c4c67b769208455', 'result_07c8bcba7da394b77d1b9569', 'match_73fdbaa3b124a803de14f0bc'),
    _m(RS_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 1, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       '5acd1521d5483d0eb386d8bdd1384982f9c8eead1537033ca0ab875378a3f92e', 'result_7ed728e53c2a89839e67e5c6', 'match_dca67ecfb75c7d2cf8990b0c'),
    _m(RS_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 2, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       '0d642a0bfd6fbc7bb1958cec9987de6cd08342b36869a7924be980f2b0674cb5', 'result_17933e1721525bd14b6cea76', 'match_149bd2fffe8837b7ba462732'),
    _m(RS_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 3, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       'f0b7beeed55385f51503880fd9a032f5ebeebf41cfa12f095e9afa8c3d4781ee', 'result_f43a3f20bf5976e6d1e7e936', 'match_b9d0994869009a349f7d0f3b'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 1, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       'f150e33f5d0557a5f51ee2eea6872bd4af1f8880cefd0e3924a3b4aa584ecc55', 'result_a6291ca24360fe7c494005ed', 'match_eb3f9f8f49ce6570d7072fed'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 2, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       'a93abe9d53e1945cfcf0e14d3b8da4bfcecbfe9a395237a68483041ef00681f1', 'result_dc1d06e776786430e09f5b9f', 'match_58b68c4adba28b712ce5dc14'),
    _m(RS_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 3, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       '1d60ccf867df7b2a9c9a229947c783605398dad163e1a13ceb126672a37d299d', 'result_3c0b54abeabbd34ffd961983', 'match_9fc070dd4f1b3aba216b8e28'),
    _m(RS_ID, 'v4_probe', 'v4_probe_twin', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'fe6c722d6526fbe56467ea8b7d0dac3ca4e3adce249c4e22b497095ec40b869a', 'result_4f927f80a68413aa0ce9a8ee', 'match_e8f8803a776b07dbce1beab3'),
    _m(RS_ID, 'v4_probe', 'v4_probe_twin', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '301fa2e90bbb3b732b4cff7838618050704fec6013b0cb260da77d4933ce1fe1', 'result_9a7478b4f5f5fa9a6113fb97', 'match_bbe5d84e553ef354de306a9c'),
    _m(RS_ID, 'v4_probe', 'v4_probe_twin', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '4e4bcbce90cc01b860af25db9d4499581bebb0c22898d8c01a836ee49e158c9f', 'result_d0253b4e9a1d9100f28f6e65', 'match_3b7ee24c14eb17d585747472'),
    _m(RS_ID, 'v4_probe_twin', 'v4_probe', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '02934aa7d48cae2d27c628ce426412bd429d63145d1fe441e049c71e31fc3ba9', 'result_d98f2e02b4ecba39ec8378fa', 'match_a7b137f9eeb0ee5bdc1437ac'),
    _m(RS_ID, 'v4_probe_twin', 'v4_probe', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '72aab440ada2db68386e48044a590e0300741c6a764a1965dbf01d1afc7d1bde', 'result_ec21cc1d1f5e34c381d00785', 'match_36674634917f89d9084efcd1'),
    _m(RS_ID, 'v4_probe_twin', 'v4_probe', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '74e20439349466ad93173f0b58345fe294e2c05ca2c075203d423318832c4cd1', 'result_3c1be202da9dcb29c1b8465d', 'match_70f7bc8c8c062331429616b3'),
    _m(RS_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304), (38, 38),
       '1838ff0f3ff4752d21df4d479b9d2b1b46f1c3ee92bbbca95445a60025f766a5', 'result_6df8fe9d20cd241ffb65315a', 'match_e2aba112301645cf2b265abf'),
    _m(RS_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464), (58, 58),
       '4de6e7a27fbdeca6732a0105060a3bff20a4d97642c9bb1ea9ab1093d9e52a88', 'result_7d0b0e3bb57e4345976d7bff', 'match_d802207d3d4e978b976a09ce'),
    _m(RS_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280), (35, 35),
       '3621249d759bfbc4526dc5293722fe5842ac049c49013a434eb2fe7927b3c376', 'result_412c3128b750fc8be507a45a', 'match_791b45eff9e11e94791e6600'),
    _m(RS_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304), (38, 38),
       '478abbd082262bad1f4c2bb2370c68335cf04377913edc774a3a4f9c5406de40', 'result_5f213c73fd2bc11f39709c93', 'match_ed9c052a203d6c0ccde08f5c'),
    _m(RS_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464), (58, 58),
       'c887166b8752e48985172813d13421e0d338abd76243a5cfc99b5fd8b2a85fea', 'result_b19d93900c3f617857d153a5', 'match_f6b0b79e6a7e7e4bab212da2'),
    _m(RS_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280), (35, 35),
       'e168ed92592195e6355625a0393b8fbc6c94cada278314e7942d7261dbedb0c7', 'result_e5d544d814b6509ac723b63f', 'match_f485747d022978f4eab8bf74'),
    _m(V4_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '631584bfa7cfdb0f3c3ed7c452b1bc843c0c84a7498b65d155c73e012857f836', 'result_49446bd4a5df4e2113e69096', 'match_798613f286da19fb1379502d'),
    _m(V4_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'd53b6ce067324eb63a8e81dfbd12988b97a72a97897013989a0afece382a8d5e', 'result_79fcf94c2ed02a593edac353', 'match_1a850ede993639671f74a6d6'),
    _m(V4_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '26093ac844a4f756308fda868a0eb2b4f9631016eb1540cb0e72e178506653af', 'result_7f7d6e19d22a3682a3f08f89', 'match_781736384621caa85553f335'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       '97a0e3f07776d7b0fec23f15e1a3894fd142ca20856d09aa89da4090543f4dbc', 'result_f1bce70b1cd0a5a84c112437', 'match_fed0871b8add4a144f096d0a'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       'ab27d61ac965ef2116be76a321b3ff50bb0db3d5c454fc12e72aa33614df1956', 'result_5f848d84eaa8c29d506e163a', 'match_d8932783d5ea3dae6e13d6e2'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8), (0, 1),
       'b484ec898110b96bdcb76b66d1203c7bb3b99c459f1b58f512fe1f7983a7b169', 'result_1ae492cd7715b6cb83c23772', 'match_f1f1a4982dcaa24f5990d5e5'),
    _m(V4_ID, 'e2_repair_guard', 'e2_sniper', 1, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       'e6554eff7bb65d27ce8f175f3b2998f688fd0d42a1b83eff34577cf60032f693', 'result_c43820b03314e4136eaa5542', 'match_1adea356c8aa273046726856'),
    _m(V4_ID, 'e2_repair_guard', 'e2_sniper', 2, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       '8c32006213a2e758aea0dd6a0f606943c373087786815f2c097a3c237b86566d', 'result_b9e417888c72261801633910', 'match_9b26ccce43b0c96f64993229'),
    _m(V4_ID, 'e2_repair_guard', 'e2_sniper', 3, 'B', 1, 'last_agent_standing', (0.0, 6.0), (2, 8), (0, 0),
       '63e1d7fc766f35b075549e4513260b5e02662277375559123ef78028e02552ce', 'result_dc7bb7aa679926a0e361a93b', 'match_c98193b59eaf02316ee3e5d1'),
    _m(V4_ID, 'e2_sniper', 'e2_repair_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'd5ea5d789e5557a0a0d3e45da3fd5f6fec71ecc03da1b931ddb9ab338a3c7a0e', 'result_aa857a256d4fce2a62dece4d', 'match_b0abeb7ab5d28b6dd590c521'),
    _m(V4_ID, 'e2_sniper', 'e2_repair_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'cdb0796e4ad5d2c8791454da52953465225d6914dc91fd4d8e82b206a58f388c', 'result_76112f336fcfde5714c37f96', 'match_d554701c4c8a636c77168bc4'),
    _m(V4_ID, 'e2_sniper', 'e2_repair_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '3e62966ac99725a20b000c6db4dadcf8ebba71da2822fd9dd7edd50dc76d54e9', 'result_697ca5c1524ea8f6865e5a10', 'match_6a459f8598d5edacc1e8d255'),
    _m(V4_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 1, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       'eaf9a126f9f9a88501fd065c28a4361e71ff0246462b32524d2f869535200592', 'result_99cb68e59908648bff6ea047', 'match_80dceae81cdb8899f27c4477'),
    _m(V4_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 2, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       'e4cb65b85bc04e66434fa5d272823f7bf5cc2c637c7441c18d185e803e21062a', 'result_2482152a6f26bedf7f189f4c', 'match_7e582cd0494cf2ff49afe352'),
    _m(V4_ID, 'e2_spread_sniper', 'e2_disrupt_guard', 3, 'A', 2, 'last_agent_standing', (7.0, 1.0), (16, 2), (0, 1),
       'df73fbfb60251f72dd6b59872a0e8892d976aa90b544c573e1c773150a63b121', 'result_9edc8b5646974b92410a757e', 'match_ca39cc87285b50eac6b07d0c'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 1, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       '84805591f5df545f4a2f7775f50376fedd18d370fd703b5e77b1c628dd22eedc', 'result_5a51e67300f9816dcb21b55c', 'match_ebd3ec563593f90d390c0a5f'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 2, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       '817ffe6b3a3a1636e8770d3900e7e0ed500f47ef14541fa531bf9af412eff8c6', 'result_d3d7de96599c6d5db9c517ac', 'match_3887c2af594f5d9101489f3c'),
    _m(V4_ID, 'e2_disrupt_guard', 'e2_spread_sniper', 3, 'B', 3, 'last_agent_standing', (2.0, 8.0), (10, 16), (1, 1),
       '823c7cc518d7ff01b67b40cee83d846e14d99335477a1f6c40d2ec478cdc0536', 'result_0891b264b9c956b7b69fa0c1', 'match_9b120ffd128076d751c79613'),
    _m(V4_ID, 'v4_probe', 'v4_probe_twin', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '6847fd99c1a9148e73ac66646af30091c6efe5ffebd4c75b6b8622e587e8d22f', 'result_98625ec04a5ed39ca9aa3254', 'match_439f4c2c3d6225e47bc16149'),
    _m(V4_ID, 'v4_probe', 'v4_probe_twin', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '90ab3640593a55e107b885f9de2aeaf9ccb17c33cd9550d5e093310fbbf9bf0a', 'result_004c103e9e82cfcc277fb3dc', 'match_fa752892afa75017c91ede41'),
    _m(V4_ID, 'v4_probe', 'v4_probe_twin', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'de618a318c588e0892c8c0ede8e1819fe336e93804440ab4bd577ef3bf431955', 'result_dcceb87102bc5c6ec1a0b666', 'match_7e5101544a3f8d5ebfa2e544'),
    _m(V4_ID, 'v4_probe_twin', 'v4_probe', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '70d9c0d1d20cfc52203d03edafcbfba4f206d241dc3087b0c89fb44d48728d41', 'result_b91572189f2d4b7369aed018', 'match_af0e64ab7586788f83664a13'),
    _m(V4_ID, 'v4_probe_twin', 'v4_probe', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       'aaf610e0f6d1a93ff659bd20e76dd2326fdb49ff647c6e6b723e396cd97214b8', 'result_6e4ea9025ebcf3db2ddb4a08', 'match_c520a0753a58b0e4aa235726'),
    _m(V4_ID, 'v4_probe_twin', 'v4_probe', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0), (0, 0),
       '7ba0d37c94c2a221c04382c1e6f79f8e73dbf6402d1bf3977526ade9aa2339f0', 'result_83b8bd9973af440daab05fc7', 'match_6388f7e10c9204ed5fcdabd5'),
    _m(V4_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304), (38, 38),
       'deb8a9abeca051e4b2e67f9a99a512eec4c44d6c373bfc9417b5a7a62a3bf59b', 'result_bc04ea900b8e52ff8fece8e7', 'match_40bc317cb877eacf2e9fd402'),
    _m(V4_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464), (58, 58),
       '1e6f961c760e1859ce489a9fab77d8fffce25caad2a687d8e229421124e8e4fc', 'result_cb92f777c9f8ddbfda3d7476', 'match_93d829bc0451450664d63f3a'),
    _m(V4_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280), (35, 35),
       '4515024e7a5595bcb71e0e2f0fbe07b760ea8aa0f578ce884e63122d0a3c3bcc', 'result_8f803ac3c789c145f81f6fc7', 'match_4a2096b99de4ad09c3fc13f4'),
    _m(V4_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304), (38, 38),
       '842827271711d2e1b768c7a39a27e41f52d88cae4a61104749ddd19250ea989f', 'result_e0cb0870b1557a0c51245ca9', 'match_191bb48e14bef7c0cd477613'),
    _m(V4_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464), (58, 58),
       '0d5b1aa65338d14ac0c19322f2413755c1cd1040e9d8e9909c52b33f8d110122', 'result_b2e961e5c2dfd18ee6904f6f', 'match_6cd10813e67c1382c483aa11'),
    _m(V4_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280), (35, 35),
       '379fe5e8a5e573ad3afc2e89509562ae4700e852a344a778446470b8975d2f43', 'result_2154e69b94bf72fc784a9051', 'match_19a6ba0a4e439b71e712c495'),
)


def test_frozen_corpus_covers_the_declared_matrix() -> None:
    assert [
        (case.ruleset_id, case.seat_a, case.seat_b, case.seed) for case in FROZEN_E3_PARENT_CORPUS
    ] == list(corpus_cases())
    assert len(FROZEN_E3_PARENT_CORPUS) == len(RULESETS) * len(PAIRINGS) * 2 * len(SEEDS) == 90


def test_frozen_corpus_exercises_whole_tick_disruption() -> None:
    # Guard: the corpus must contain the whole-tick silencing E3 changes
    # under every parent, or its identity would say nothing about the
    # disruption path.
    for ruleset_id in RULESETS:
        rows = [case for case in FROZEN_E3_PARENT_CORPUS if case.ruleset_id == ruleset_id]
        assert sum(sum(case.silenced) for case in rows) > 0, ruleset_id
        assert any(case.reason == "last_agent_standing" for case in rows), ruleset_id
    # E2's scheduler-phase-locked stalemate (E2 design review Sec D.5): each seat is
    # silenced on exactly half of the 1000 ticks.
    assert FROZEN_E3_PARENT_CORPUS[0].silenced == (500, 500)


@pytest.mark.parametrize("frozen", FROZEN_E3_PARENT_CORPUS, ids=lambda case: case.label)
def test_parent_disruption_is_byte_identical_to_the_pre_e3_freeze(
    tmp_path: Path, frozen: FrozenMatch
) -> None:
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
    assert observed.match_id == frozen.match_id
    assert observed.result_id == frozen.result_id
    assert observed.replay_sha256 == frozen.replay_sha256
