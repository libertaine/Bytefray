"""V6 E6 parent byte-identity freeze: enemy visibility as it behaved before E6.

E6 (priced sensing, docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md
and docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md phase I-0)
adds ``RulesetPolicy.detection_radius``. Its default, ``None``, must be
*observationally identical* to enemy-anchor visibility as it behaved before
the field existed (pre-registration clause D-3). That claim is proven here
rather than argued. Every value below was recorded against the unmodified
runtime at ``f43f5d2`` -- the E6 registration commit, documentation only
since ``9d43cac`` -- and committed *before* any policy, visibility or Ruleset
code changed. Every later build must reproduce them byte for byte.

The matrix runs under both E6 parents:

* ``bytefray-rules-6-research-scale`` -- the stable-equivalent research
  control, parent of the primary E6 treatment (K=1, whole-tick disruption);
* ``bytefray-rules-6-research-disruption-slot1`` -- parent of the companion
  E6 treatment (K=1, lambda=1).

Pairings: the contests whose play depends on what an entrant can see --
Global Sniper vs Minimal Guard and vs Disrupt-First Guard (global
visibility, and core inference from the first visible anchor), Disrupt-First
Guard vs Guarded Painter (disrupt on sight), Spread Sniper vs Spread
Defender (several visible locations), the bounded-reach ``v4_scout``
(declared reach 8, sensing only within that reach, searching by movement)
against the Pure Repair Guard and the Global Sniper, and the Guarded Painter
mirror. Each runs in both seat orientations at seeds 1-3, arena 512 and a
1000-tick limit. 2 x 7 x 2 x 3 = 84 matches. The fixtures are tracked and
LF-only by ``.gitattributes``, so every identity below is the same on every
platform.

What is frozen is the E4/E5 parent-freeze set (replay SHA-256, ``result_id``,
``match_id``, the per-tick ``cpu_used``, memory-write and anchor digests, and
the plain outcome fields), plus the one digest E6 moves:

* ``observations_sha256`` -- every traced decision, in execution order: the
  acting entrant and process, its full ``ObservationV2`` (including
  ``visible_enemy_anchor_addresses``), its action and the applied result.
  ``wall_time_ms`` is excluded, as the only non-deterministic trace field.
  Enemy visibility is exactly what E6 changes, so under ``None`` it may not
  move for any entrant, including one whose declared reach is bounded.

Each match runs with ``MatchRequest.trace_path`` set. At recording time,
every case was also run without a trace and gave the identical replay
SHA-256, ``result_id`` and ``match_id``: tracing observes the match, it does
not change it.

A mismatch here is an implementation defect in the ``None`` path, never
something to re-bless.
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
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID,
)

from tools.research.v6.e3.entrants import prepare_data_root

ARENA_SIZE = 512
MAX_TICKS = 1000
QUOTA = 8
SEEDS = (1, 2, 3)

# The primary parent (stable-equivalent research control) and the companion parent.
SCALE_ID = BYTEFRAY_RULESET_V6_RESEARCH_SCALE_ID
SLOT1_ID = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_ID
RULESETS = (SCALE_ID, SLOT1_ID)

# Visibility-dependent contests, each run in both orientations.
PAIRINGS: tuple[tuple[str, str], ...] = (
    ("e2_sniper", "e2_min_guard"),
    ("e2_sniper", "e2_disrupt_guard"),
    ("e2_disrupt_guard", "e2_guarded_painter"),
    ("e2_spread_sniper", "e2_spread_defender"),
    ("v4_scout", "e2_repair_guard"),
    ("v4_scout", "e2_sniper"),
    ("e2_guarded_painter", "e2_guarded_painter_twin"),
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
    captures: tuple[Capture, ...]
    decisions: int
    cpu_sha256: str
    writes_sha256: str
    anchors_sha256: str
    observations_sha256: str
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


def observation_stream(trace_path: Path) -> list[object]:
    """Every traced decision in execution order, without ``wall_time_ms``."""

    stream: list[object] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("record_type") != "decision_v2":
            continue
        stream.append(
            [
                record["agent_id"],
                record["process_id"],
                record["observation"],
                record["action"],
                record["applied_result"],
                record["diagnostic"],
            ]
        )
    return stream


def run_corpus_match(
    root: Path,
    ruleset_id: str,
    seat_a: str,
    seat_b: str,
    seed: int,
    *,
    traced: bool = True,
) -> FrozenMatch:
    """Run one corpus match and describe it as a FrozenMatch.

    ``traced=False`` exists only to confirm, when recording, that tracing
    does not change the match; its ``observations_sha256`` is empty.
    """

    prepare_data_root(root, [seat_a, seat_b])
    starts = resolve_direct_match_starts(
        ruleset_id=ruleset_id,
        arena_size=ARENA_SIZE,
        entrant_count=2,
        supplied_starts=[None, None],
        seed=seed,
    )
    cell = root / "runs" / f"{ruleset_id}-{seat_a}-vs-{seat_b}-s{seed}-{'t' if traced else 'u'}"
    replay_path = cell / "replay.jsonl"
    trace_path = cell / "trace.jsonl" if traced else None
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
            trace_path=trace_path,
            ruleset_id=ruleset_id,
        )
    )
    assert result.result_id is not None and result.match_id is not None
    actions = {"A": 0, "B": 0}
    captures: list[Capture] = []
    cpu: list[list[int]] = []
    writes: list[list[object]] = []
    anchors: list[list[object]] = []
    final: MatchResult | None = None
    for record in iter_replay(replay_path):
        if isinstance(record, TickSnapshot):
            anchors.append(
                [record.tick, [[p.entrant_id, p.process_id, p.anchor, p.reach] for p in record.processes]]
            )
            if record.tick == 0:
                continue
            used = {agent.agent_id: agent.cpu_used for agent in record.agents}
            cpu.append([record.tick, used["A"], used["B"]])
            writes.append(
                [record.tick, [[diff.address, diff.length, diff.owner] for diff in record.memory_diffs]]
            )
            for agent in record.agents:
                actions[agent.agent_id] += agent.cpu_used
            captures.extend(
                (record.tick, event.event_type, event.victim, event.killer)
                for event in record.events
                if isinstance(event, KillDeathEvent)
            )
        elif isinstance(record, MatchResult):
            final = record
    assert final is not None
    stream = observation_stream(trace_path) if trace_path is not None else []
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
        captures=tuple(captures),
        decisions=len(stream),
        cpu_sha256=_digest(cpu),
        writes_sha256=_digest(writes),
        anchors_sha256=_digest(anchors),
        observations_sha256=_digest(stream) if trace_path is not None else "",
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
    captures: tuple[Capture, ...],
    decisions: int,
    cpu_sha256: str,
    writes_sha256: str,
    anchors_sha256: str,
    observations_sha256: str,
    replay_sha256: str,
    result_id: str,
    match_id: str,
) -> FrozenMatch:
    return FrozenMatch(
        ruleset_id, seat_a, seat_b, seed, winner, ticks, reason, score, actions, captures, decisions,
        cpu_sha256, writes_sha256, anchors_sha256, observations_sha256, replay_sha256, result_id, match_id,
    )


# Recorded against the unmodified runtime (see module docstring). One row per
# match, in ``corpus_cases()`` order.
FROZEN_E6_PARENT_CORPUS: tuple[FrozenMatch, ...] = (
    _m(SCALE_ID, 'e2_sniper', 'e2_min_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '09334cd2a1bdf5f24b61b21c41ffec20e7c1f43b586b2373d660fb14dab8ac21',
       '7a4e142c4c26aa3288d306d5841ecabf4a3097a80221945ac466647d236040be', 'ce41c5baf63b6dbae209e12ae6e8709acb29c0ff2a79cb3be2c7bbc371dae028',
       '9ab18377c0f30371469aa614537d829dad88a19dec009677cf7d3eade04d6cc7', 'result_5b607b54ae880bc820587429', 'match_ffee3e56c10b1d72ffa75464'),
    _m(SCALE_ID, 'e2_sniper', 'e2_min_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '266a6d7053eb39e0476e16947869a7edc6501f760269991799fa2a89a3e31b49',
       '2f4e3791574446f36e6fb439d4cab219fe3a8f09bbaa8f9de526c087e255738b', 'f4d3c72b0e8a5ca435f0cdaf98c6dbd4bce1b1f03a5d5dd3f41074995654d018',
       '74497bb3d7fe1b7ebf4b2ac04f1c3b493ca93a3d40ef100cba09b7968653ac02', 'result_78b9fd4864dd86c83794b0e4', 'match_05a4f8e1ededea2c5809ec88'),
    _m(SCALE_ID, 'e2_sniper', 'e2_min_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '578de517e9e4266255c084a360c7d2f3078eb0c34bbe66e538ccef6645878980',
       'f31fe8a6ceffaf647b22d9e6a01abceea0d734e44b3e4d253c2fa9cf0eca3299', '9b7a092ce3d607a98be52c3fbc28da1bdbf0890bcd1a54a67ad109ef78c57fb8',
       '225ac34d1c81740174f4ae07f91f88f0f72e4e7e5788961dfe0fc4ea6e365a81', 'result_21d24768099d5d94ddb4880f', 'match_b25875448c98e6f67ac69db8'),
    _m(SCALE_ID, 'e2_min_guard', 'e2_sniper', 1, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', 'dcf78109d7d7abf6c3e56fea849cb9a7dc04a5ddbac82669ae253222e9202649',
       '732e89d1d29c0a2a9114936648d1d8f5baa22f6553309e57eea6c605a9c7b453', '7e6fab473bb043b706d00fc8f756a550c5ee868e61748ef9515942342390423b',
       '7378a9567a27dc0f9c86d83ea0351231d40a31af7ce5d8b9c4831bd783d9a2cc', 'result_1d9cd0b932cee2b858f35da8', 'match_4d92dcd9128ae0f77d260d00'),
    _m(SCALE_ID, 'e2_min_guard', 'e2_sniper', 2, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', 'fb188e9b707289b9f5c651efae41c96ff8a0b577d88e5e3ecaec1bae5fa4e08d',
       'cbabd2c50e761dc92ad2becd9ad7eb2ac64beeb0c8de1cf9f16c2175a98387a4', '4dfc964749d8a93b170b19b2d399f0c7a1aadb1ed609ed21a213da21bd9c334c',
       'e28747ebb9223c08a458cdb44fc7da1942e679b9a2df3c7a116fc9b1a151750a', 'result_596c6dc7481d4f0c21c18e5f', 'match_00c584c9918fb90e0abfe12b'),
    _m(SCALE_ID, 'e2_min_guard', 'e2_sniper', 3, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', '372ee33a80408e98554924bc1e765fcb223e4c3eedcc88d208db40f204f74bb3',
       '55a34356310e2f9cff7c65cf7e72ac448ec4715630b38b7787fe5264d0ab19cd', 'b0655303f2f7faab79abab61448ab1b2af15ea9eedaa056035a9e446ee2ebaf6',
       '55f754eb5c3d14a2746aeda6811fe2221c6ab547ee0679a4bea8a280279c3679', 'result_7b6cdd91ddbb70445c7c149b', 'match_56e79084cf7b43eec62a73ef'),
    _m(SCALE_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '09334cd2a1bdf5f24b61b21c41ffec20e7c1f43b586b2373d660fb14dab8ac21',
       '7a4e142c4c26aa3288d306d5841ecabf4a3097a80221945ac466647d236040be', 'ce41c5baf63b6dbae209e12ae6e8709acb29c0ff2a79cb3be2c7bbc371dae028',
       '39ab576aa787ecab0d89aec99b6385a6e8ff48f23cbda10c4a6230173fb85cd6', 'result_e8edcd1d193204ef5a134f93', 'match_48eea65ff6c4c4d0d4eb63db'),
    _m(SCALE_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '266a6d7053eb39e0476e16947869a7edc6501f760269991799fa2a89a3e31b49',
       '2f4e3791574446f36e6fb439d4cab219fe3a8f09bbaa8f9de526c087e255738b', 'f4d3c72b0e8a5ca435f0cdaf98c6dbd4bce1b1f03a5d5dd3f41074995654d018',
       '5d3782bb1863c2fe0c710541da65e7d700e35c49c99da698fe569f5aa914dc41', 'result_8af9360ff6779ff1eef18b3f', 'match_82e77ae33165c8852eb4e2ef'),
    _m(SCALE_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '578de517e9e4266255c084a360c7d2f3078eb0c34bbe66e538ccef6645878980',
       'f31fe8a6ceffaf647b22d9e6a01abceea0d734e44b3e4d253c2fa9cf0eca3299', '9b7a092ce3d607a98be52c3fbc28da1bdbf0890bcd1a54a67ad109ef78c57fb8',
       'bdaa8fa8d54b3bce3fd6cc9ad91b236c1c2d9ba9368aa74b1ad8999d9334b8b8', 'result_116d263b8cb55f652dbf6c85', 'match_397c5f788d0242ae64114905'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', '7880f65c2af9be4cd9f2c83dedee186f1578bcd85e6aeb692aa3282c743631c4',
       '732e89d1d29c0a2a9114936648d1d8f5baa22f6553309e57eea6c605a9c7b453', 'ed7c1a0e25d7e70d83049ecd15b8c74e5c80d733b4728a4dcf49fa96a49b513d',
       'db266ddd7ad2c3b27754d596423134901526cd92dcc8fe55ab4c88463061de29', 'result_81b6048f9cb89f3418fa3cdb', 'match_70c7a69e1a1e895d35aaf0da'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', '294d8d2a955c04c74bae175ca480e592de569e8419a22578cc469f8a4df9f16b',
       'cbabd2c50e761dc92ad2becd9ad7eb2ac64beeb0c8de1cf9f16c2175a98387a4', 'b1829ea78ff46ab177a31ed61205c27ee47789c067f80d1f873124dbcd1cf69b',
       '13c132e477cc9e55c82dcbca32b8ca6de9ab60df0f57d08ad3ea4c7dce3d1549', 'result_05e9ca689afd97db2daea329', 'match_4f252933c2ee08026faece3a'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'B', 2, 'last_agent_standing', (1.0, 7.0), (8, 8),
       ((2, 'kill', 'A', 'B'),), 16,
       '918ec0c6f87fcbdc08b3220f2dfbc049ee4d5807739c8e37fa36e4ba1b44f744', '94e301ae3906fc6845cd45ef5b1d8954aeb845ff61f3ba20bc76dfc57f97c462',
       '55a34356310e2f9cff7c65cf7e72ac448ec4715630b38b7787fe5264d0ab19cd', 'd2c2dc34222d7fcb94e71134af5ddefa3a932aebd4308d28b28aa16aec7c1fe7',
       'fe7662fa1583efe48f2bb6035203acc83ee88728557e56735592e711801fac0b', 'result_f139224865628ed5da2aa35e', 'match_b9d8e1ab6a296920d29c2574'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 1, 'B', 1000, 'tick_limit', (1000.0, 7413.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', 'c8ad1e67833b3202166859d7c913f30ee650fc4d4e2e5cfc5daae361183328d9',
       'e9f5281133aed636ad645bb1847a2d8e9bb64cb2b926da4d15bf037d4344024b', '3539425416666c9e16704c979e672fa272ede755890526c59a4bbfb0ad778a9a',
       '7fe19ef70cad20f590d6ef7a33a808763aab7cdde508a887a7083ae53354aa7b', 'result_422e2f72233a7140aadf3056', 'match_4b409eb89e091f9526226e81'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 2, 'B', 1000, 'tick_limit', (1000.0, 7417.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', 'a3be5993832c2528dd397f6d26417512e91bd6d581d6e11200093eace9654de9',
       '63af2e6405a60f2dce488bb3ce842f8efe8186b1d2fa01f6ba69ab839aee9ed2', '10058e99de79e0baf66dd03a1da70d9a7bbe1a7cba882cc051ba0909a41dd19e',
       'a86e8b7bebac5f8ec6f57ac41ee3e81772d9cba57c414c0ffb93fbc68fe72b29', 'result_d00ff8cd7c57a339b9e5d79c', 'match_049552707c5dfe4aa6060584'),
    _m(SCALE_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 3, 'B', 1000, 'tick_limit', (1000.0, 7413.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', 'eed0920d004d7ed2ddb67c77c4ddd4308ca021a095714a8f1939b7f198e468ec',
       '343989d4d145149625297725d131a403f8f96c5a0ca4f5dfa1fd1983e7ec2eeb', '360a819f3917b4a57578d7ddbfe87fc903df1ec8f56295bb38f1c81406529f01',
       'da61c89ef6ce79dae20ba7b750974b92def831a1d493c1edded021889c07d469', 'result_f831f77654adef432abb9548', 'match_1704506aae4a4660801d86ab'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 1, 'A', 1000, 'tick_limit', (7420.0, 1000.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', 'ef0b9c4cbd15a8a1e174bd29557d1a296afe0f74f6092d884ebde1bb1f3a6f29',
       'ea5a92cef03046fb0c13472c2b35d01f3926e970bbd8beeade8e919337b832d2', 'f46fe42ec9ae34083e3bd7cc0395f4c1808d266a2eeee72787a2fc2b09570d8f',
       '20feef072fe2e1b55eb2fc79fedf01c10fa1c34091255b3fffacfb9fc41e237c', 'result_d7fe3cc48ac8db21df1d76bd', 'match_697a29be1ddb42358a70df18'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 2, 'A', 1000, 'tick_limit', (7424.0, 1000.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', '8965de013879eb386865881a909dfe6fde7c9b72772cd02a7192bc966305347a',
       'e0af0983b7010394b3f768e9177e3cc063dd4d131fd9c3eecefc1c8a71997eef', '2cf930cf10a77aae8d16ac59979a355fe32f4832ae32ce43e7905ca5b8df1c8f',
       'bf63afbb473c1325e3c13f47d5acfff815f12c7ec2176319ed2526f207ce6c25', 'result_67e52e6cf8033b0890ce7b29', 'match_0986ca31b06e7a4202e1b7e3'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 3, 'A', 1000, 'tick_limit', (7420.0, 1000.0), (4000, 4000),
       (), 8000,
       '01f908b0acdcf8e40fc001e64a1021827653ff9af5c4c3127c51badaaadcd463', '8559f71cb0ba200ede90ae33a865dc5205be9cab15ccdbe9ddf0cdc010f61df4',
       'f11553593420eb516318f2003f7bbfe0164a789c4a5f0b0bd1609f032b566cbc', 'd8d42d31f9ac27c7df5b5645b0abf406de216738578fb5fe4b2352289c931565',
       '1b541f8c6396f708e7cc21996afb63a2903ff034afb7616418e81226bf4f233c', 'result_727ba4b1500bb5625e461918', 'match_5da75bceb6131e45487ee6fb'),
    _m(SCALE_ID, 'e2_spread_sniper', 'e2_spread_defender', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5006, 4994),
       (), 10000,
       'f3b8a624efe828ac10df2d373862f47329286fa815c0e31876cd18c26ee23686', '3dda3a75290e414da202aef78511862228e87d0d375aade5e5b99c3cecf6e6b6',
       '7a7c514974eb355ddd95ba4870855b0da3f58e8463c55815f63d6482ef8c0d15', '78d7f0412d284cd3283d3597fdcd08faa25e0ed5f2c122a1de89ea585316f40d',
       '2d2b063004697dc63f15acb4453c06879198b00c628f722dbcf6d022007a80ae', 'result_a54969f8e4b8679d25e7e83a', 'match_9dc0f0ecc2a9818273db1049'),
    _m(SCALE_ID, 'e2_spread_sniper', 'e2_spread_defender', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5006, 4994),
       (), 10000,
       'f3b8a624efe828ac10df2d373862f47329286fa815c0e31876cd18c26ee23686', 'e22fc6d0f9dd088e608085645e4920926821425b4df10cf39d24147eabd85129',
       'a061e9bf3037f783ee45016d8931410a863e25519a7e784daac0760a6532cb53', 'e2d59ee1bec54c369643b7c7ab5df11044b8a6973fbca90938d32f1905a5af6d',
       '46fa4b9b9b840f1375730f50f57caa33760cf97484682772c919f43e13ba5048', 'result_8c0f20873dc26ca18f286391', 'match_d8cf759793c86aad2f0a08f0'),
    _m(SCALE_ID, 'e2_spread_sniper', 'e2_spread_defender', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5006, 4994),
       (), 10000,
       'f3b8a624efe828ac10df2d373862f47329286fa815c0e31876cd18c26ee23686', '8e5db25c87ffdc6a73207f164a34d891486f3bf86e33fc8e6f44531c427eeb25',
       '5154449721c164ee38e80e081d0e6048a5d03d8aaf62f29a8891ac0463724648', '9f4cc70e9743b54abf074adb5e118ba6da7d63c7f50939795017e008425e6fc9',
       '9cb6eff830dce19f541d5eebc5d79f90351b9f430ea4dc6ce343e109a4fff3f6', 'result_a9b3dc1aa2da28e83064dd5c', 'match_3ab40f2e9752f0196aa56756'),
    _m(SCALE_ID, 'e2_spread_defender', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5000, 5000),
       (), 10000,
       '7618e371e62e385e6ec54313e350a5159ee0059967074e0ade762e0512bf9adc', '951d663c852ef73b9e23bac688682880c24580cde753d8916d20a432aa227ef2',
       '376a40c2cb2cadd578599eb27d8d9b212a70b434a6c95a7d0dba444e6f112ca0', '49a3fdcec7da337994b0787bc51b2125ad858cd0ee5d1e5577362b61ac050bfa',
       '23132df8577c0c447a3f9628903d9069ddb831a797c7c4a5179618c7096e0686', 'result_19ba6ec4068b2ce1564934d0', 'match_d0be318061b8ee4d0897ddee'),
    _m(SCALE_ID, 'e2_spread_defender', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5000, 5000),
       (), 10000,
       '7618e371e62e385e6ec54313e350a5159ee0059967074e0ade762e0512bf9adc', 'cdb5557229821a42490bd8f7d0786c68a3eb4975036c4fc0aa866c3f12ed6000',
       '34e7eaa6f8d82596edf5a6832228af674383a9fb051f37ba467a7336af78433c', '94e4c8a0a4fce4d890fd2145d3b77f07031bff0050f787be8531883a510319cb',
       '5f590d0d2a302695aa7f9c4baf125ef9a51a335aedc3aeac19eec001fca1e12a', 'result_e2cbec674a141eb41c267b37', 'match_9093d4ebde15c02f09ed99e4'),
    _m(SCALE_ID, 'e2_spread_defender', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (5000, 5000),
       (), 10000,
       '7618e371e62e385e6ec54313e350a5159ee0059967074e0ade762e0512bf9adc', 'cdf0b23139a7ab016d28735ca09e73a758572478b913076485bd78ebe1f3f36a',
       '6dcfeb9d8a3f6c9cf46fddea10c00c955eb962ca6b686685469666c846747d0a', 'fcbb4c3ce334213f4a8abc0a1b03089446a818fbb866070e6ca873f5df389e97',
       'f7e12a7174e38ba76c3cc9d5794e6105f418213a263cf96572fc91051f03907a', 'result_82371d2862a69937a29a7f67', 'match_137f88403e5d0300ac0873c1'),
    _m(SCALE_ID, 'v4_scout', 'e2_repair_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 1042),
       (), 9042,
       'f3bf72f74fc6c9721a42abb963042d3802057bd8a4ff6f91ffac1589ef938133', '2a9e60e797d9d6b9ef126af2419c08a31c180d32cc9c83e677eb3ce6bc9ec474',
       'ee632771c752e31cac4e6d06ca9d5b74a9320855927cb20efdfe102815c1979f', '358de962577b471effecd4ec14b692dbeaa87e3250c55f904683d3f31b3491f4',
       '79d2e4e107cfead4c6396062ad5f2bed56b07ff2f91e26363449d0fabb8686db', 'result_9d3176ff5072d07bfb24666d', 'match_68e13bd45186cea5fb3df001'),
    _m(SCALE_ID, 'v4_scout', 'e2_repair_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 1036),
       (), 9036,
       '98b8aebf191444c68ccd1de6a5cf4f36e97c9e9dca67234942a99ceed151f1fe', 'bc0f4da3755d14585b9bab78af299789c7c47946768bd2070638b848a21dcde9',
       '4acb78cedcabe88a1a38479b6dbad4d2e0cb8a88b91b3f6ba24c0931ed80fae6', 'f44e174cffd28a0c01aad0c008bbaf4a20797134b82ceaa57d6ee0d733a045d7',
       'b21747e7a6b4e07f550322df7a2f43b83a036b0601353b0134b9fee6df44c7cf', 'result_ce025c15cde0dc38593559c9', 'match_c356db4454d9b1c49ec21538'),
    _m(SCALE_ID, 'v4_scout', 'e2_repair_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 1044),
       (), 9044,
       'a996e519644142fb41db839434f551768206802dac7d19000029ecf29d5c117d', '214ce49ae2f3294d6f4aa6dc8c090213b9839de433b22308465943393b15ae2d',
       '7dd32f7dc95e1e6c09a1f58bb845fb1eb3274ff77df7e2f8ceda307080bba3dc', '9dfa3d8ff369d6d748aa9c8385fa9010b12649a61f8a75ac82a4f26d1bd5ba31',
       '5ac451a4653f4dae238711211d5d36cd07d6baff4ef84cdbeaea058c656b71bf', 'result_f63c5770450cdee13690b761', 'match_3fd4f93ff83adbc44b7f710c'),
    _m(SCALE_ID, 'e2_repair_guard', 'v4_scout', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (1012, 8000),
       (), 9012,
       '3e3d59879c1dd0aa6e7ac86b59877c7b7ba810a557e42acbbdf05bfa268017b6', 'c56b6e6017ac0aee11b04cfa4aa23bf42aa5dc17e242c6782f5c276eb1d1021e',
       '65d6eb9c790aa85a5bebb13e99e8ff626e9ccbe17b755d6ea4642d9eefc4b0b8', '650f918a16a3b456198c6b8cea97fa938780aa1d97c4f8c5f254d99e5acdc973',
       'bdc6f758b274bb889a70ed50d07d06d1f9766ac4a512f32e2046241d5e19fff7', 'result_b2677a2f179d685315f2d493', 'match_c4704b5e1a4f9243ee1a4f05'),
    _m(SCALE_ID, 'e2_repair_guard', 'v4_scout', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (1020, 8000),
       (), 9020,
       '8604353d54fd8cff91d8c0d10cc56863b7059d9c63525183707fbb2b74027321', 'cac5ca75fd721e8c01e536f0c306146b42b717377b04926235dab9d645a8dcc1',
       '8a8f27b1ec2de5575f2204b8e7dda58bb17a01bc79d85876efe9046b178be70b', 'db1e18c9038ca2ed59c9567d210400e412431ebde044419181ebf988b82b151e',
       '8bba3f18f114a5da33a1a8d2c193ed0fdc748433b23bc22be5253de2d379a99a', 'result_75b26c02a997286451592e20', 'match_08c7ae067cb64775545eda4b'),
    _m(SCALE_ID, 'e2_repair_guard', 'v4_scout', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (1010, 8000),
       (), 9010,
       'e1d1e82394cf2f19c6e1dab431811a9c7efa7d6ba35e9953034763136da1f72d', '539f38b509443a2879e631c0492767858bc521a31104a613c79566d2fbb4c279',
       '0fe32f09cd697981f556b6e9d4dde577f81ec75b6bbef4d3e8ee7d22322032ce', '004d62761d19fc90ee6fce075660a385f0a913bc641c2cfd9018090a5b145a2e',
       '2b2215a1e0089241e492d71648cfaf17aac18fd9fdabfd833527e93dc7300699', 'result_0f8a85cb9d75b23adc296385', 'match_811c7df180c5142bec97d16b'),
    _m(SCALE_ID, 'v4_scout', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (3856, 4192),
       (), 8048,
       '11b0697abc9783a341d5b138b2e398bd0039f4b5792afb6c73d5171b78637760', '4d54e311c13cf65fd4d17747ca61bf4363d60c0b3914029dfd8db74a8cbdfbd3',
       'a5054323f60de2d5709f9cd4a563845e207166cc61b4511ac966d8aee691eafe', 'b041c47144a9b58849422362ceb740eb7b3fadb19aec5e15da679a308a8ac421',
       '719dfbe81483ca8213538c894f01d37b2e7207e78fb1c21a76f3220f5fb78036', 'result_fea43e3b3cd16231536e539b', 'match_9ddb539ecbccbe23a60c5700'),
    _m(SCALE_ID, 'v4_scout', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (3880, 4160),
       (), 8040,
       '9b68b0b07836cf74a42735e8724994a1e16d8e56ed04b331973ce55513e4be52', '78e9df1c262eda9297b720435f0f25895bee9cce239f6b4ffe5ea967457b4a3b',
       'd38e2cbfd7e89c2cbbe28b5e80e77da99f8a5c2ee095d59b2f7e3f1ef8f7537c', 'c04390fc7b92c59106c3a0b81b9de97965955bee033ee6604ad6110e65148f36',
       '01c91e5f4c34aa64a58eee0d09f423d5c13c3490cef27f3e84adf57d3108bf59', 'result_577c65bee4204cbe082f802b', 'match_105a1741848c07c9bbb92cda'),
    _m(SCALE_ID, 'v4_scout', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (3850, 4200),
       (), 8050,
       '92661f282bf4773bdd4163495238740b9586249056259cfd6cf34230a667e3fe', '6afd4d530b56a49cff40389f85bfe9321f4f809954b2421bf759c00f9d0cbd4b',
       'b03d93c0d183479044fac11256a8347de5f813c9a57cc059b1e0f5d9c3f88e5f', 'be2477196f578380c78e72cb8938f640adcd63530975591ffb863b53b8f99368',
       '6e22ef5ce7e23093db15e99cf69e271fead844d182a70fb06bbd66482d730499', 'result_03ee04a8921c05c136b976b7', 'match_723115da58f3a7eba5f41c05'),
    _m(SCALE_ID, 'e2_sniper', 'v4_scout', 1, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '09334cd2a1bdf5f24b61b21c41ffec20e7c1f43b586b2373d660fb14dab8ac21',
       'd3580caeec1d084e793e53870fa1c186608b90f64fccfd074549de4505d7aedb', 'ce41c5baf63b6dbae209e12ae6e8709acb29c0ff2a79cb3be2c7bbc371dae028',
       '6f3f11e77db919e79e40923a8e6cc1533815566c2143f615b39cdccdcc7b2dd6', 'result_9cda623e134ae5c6ab5a3c67', 'match_31788106b1f31e7659df6dee'),
    _m(SCALE_ID, 'e2_sniper', 'v4_scout', 2, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '266a6d7053eb39e0476e16947869a7edc6501f760269991799fa2a89a3e31b49',
       '5507c59b671b12db468e30c108657d8a48cbe4f901df7e30aac89ee2e731b6cb', 'f4d3c72b0e8a5ca435f0cdaf98c6dbd4bce1b1f03a5d5dd3f41074995654d018',
       '16d126610a3866ce835decb5c7fe83e7a2763f607e9078ad3f7c549a21e3b632', 'result_62c696de10fb80dcab4e31e9', 'match_2c880b05d0810087626f20f3'),
    _m(SCALE_ID, 'e2_sniper', 'v4_scout', 3, 'A', 1, 'last_agent_standing', (6.0, 0.0), (8, 0),
       ((1, 'kill', 'B', 'A'),), 8,
       'c7a030d214af63e10ede7995b119c3e2809c287e97253d29d1d206c95b9fa5dd', '578de517e9e4266255c084a360c7d2f3078eb0c34bbe66e538ccef6645878980',
       '69dfd7f89fc24f53492866ff03c89cb58e23acc959b086a8a693793ce4057aee', '9b7a092ce3d607a98be52c3fbc28da1bdbf0890bcd1a54a67ad109ef78c57fb8',
       '4c57f338d7e8645b215d3564df9b262015dda1daf860a4b46b9b1f4d8b8e67b6', 'result_867790d8cc79c33ae0ed709f', 'match_105f4d77f1bcb92cda25f708'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304),
       ((77, 'kill', 'B', 'A'),), 616,
       'ec80dedb2c2e7a868852bb364737c60a261c362d1a3c052b010a0f274fd23874', '9552441440895c369d04b81a9b75192cd4b769a8c32e7a15abe54c18b3ebffe3',
       'e967b7b405c9181962ae92d55dfdf4b39c0ac67ba05f1dc46ee42ab248f21ada', '26c9fe45b48d4e0248e264376e683a139733cbbac6cf03a55099f1956ab24271',
       '1838ff0f3ff4752d21df4d479b9d2b1b46f1c3ee92bbbca95445a60025f766a5', 'result_6df8fe9d20cd241ffb65315a', 'match_e2aba112301645cf2b265abf'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464),
       ((117, 'kill', 'B', 'A'),), 936,
       '80ca7fc50aa395508023ff2221873913ac1fc9e4f21ec96170d859c59351a96f', '7e15551887a0a2783ece6471827e51cac64d666ccf075f6a25ae2df80616b57b',
       'db205a49e85159f3387f7806e683022a6eca41d0d7c0dbd76debdc869f26cf62', '15051f2fdaf83b772bcc8831bda22865bab6ee9c70bf6d23bb68213ed59017e0',
       '4de6e7a27fbdeca6732a0105060a3bff20a4d97642c9bb1ea9ab1093d9e52a88', 'result_7d0b0e3bb57e4345976d7bff', 'match_d802207d3d4e978b976a09ce'),
    _m(SCALE_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280),
       ((71, 'kill', 'B', 'A'),), 568,
       'f8d498de09a1c4f32961bd83f05ecf948925dfe425e904ef800e297ddc7aa8d9', '04863d30db5cfed61de7637634f083e43dbae651b8c48425b41e51d1ee537dfa',
       '858f1c90a7a0114414393210368b3f35590194bc0e4e60571a25170e5ff5b9e8', '360f21a190bc15ae6336ea1658f235cdbe4e4392d1a9f31bdd4067e8779e6784',
       '3621249d759bfbc4526dc5293722fe5842ac049c49013a434eb2fe7927b3c376', 'result_412c3128b750fc8be507a45a', 'match_791b45eff9e11e94791e6600'),
    _m(SCALE_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'A', 77, 'last_agent_standing', (176.0, 167.0), (312, 304),
       ((77, 'kill', 'B', 'A'),), 616,
       'ec80dedb2c2e7a868852bb364737c60a261c362d1a3c052b010a0f274fd23874', '9552441440895c369d04b81a9b75192cd4b769a8c32e7a15abe54c18b3ebffe3',
       'e967b7b405c9181962ae92d55dfdf4b39c0ac67ba05f1dc46ee42ab248f21ada', '26c9fe45b48d4e0248e264376e683a139733cbbac6cf03a55099f1956ab24271',
       '478abbd082262bad1f4c2bb2370c68335cf04377913edc774a3a4f9c5406de40', 'result_5f213c73fd2bc11f39709c93', 'match_ed9c052a203d6c0ccde08f5c'),
    _m(SCALE_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'A', 117, 'last_agent_standing', (358.0, 346.0), (472, 464),
       ((117, 'kill', 'B', 'A'),), 936,
       '80ca7fc50aa395508023ff2221873913ac1fc9e4f21ec96170d859c59351a96f', '7e15551887a0a2783ece6471827e51cac64d666ccf075f6a25ae2df80616b57b',
       'db205a49e85159f3387f7806e683022a6eca41d0d7c0dbd76debdc869f26cf62', '15051f2fdaf83b772bcc8831bda22865bab6ee9c70bf6d23bb68213ed59017e0',
       'c887166b8752e48985172813d13421e0d338abd76243a5cfc99b5fd8b2a85fea', 'result_b19d93900c3f617857d153a5', 'match_f6b0b79e6a7e7e4bab212da2'),
    _m(SCALE_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'A', 71, 'last_agent_standing', (155.0, 146.0), (288, 280),
       ((71, 'kill', 'B', 'A'),), 568,
       'f8d498de09a1c4f32961bd83f05ecf948925dfe425e904ef800e297ddc7aa8d9', '04863d30db5cfed61de7637634f083e43dbae651b8c48425b41e51d1ee537dfa',
       '858f1c90a7a0114414393210368b3f35590194bc0e4e60571a25170e5ff5b9e8', '360f21a190bc15ae6336ea1658f235cdbe4e4392d1a9f31bdd4067e8779e6784',
       'e168ed92592195e6355625a0393b8fbc6c94cada278314e7942d7261dbedb0c7', 'result_e5d544d814b6509ac723b63f', 'match_f485747d022978f4eab8bf74'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_min_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '893b3317b21bece60ece7c7b8b9843b5a806996b7da1ddc2a9b38d33b8a2dcb6',
       'a01bcc7e26eae2509457bbddf62121b2016e346efb19a26529f82d92d2234dee', '44f32b3948dbae844df02d4b3cc4865f4a868fc579af743e4735c14f044a91da',
       '6bc04eea5099beae7e837d2942b3783896c99bc91be969ad20e3dc73217c0fa9', 'result_e5bb0edfd59bbf93ac65c0b0', 'match_44226083f187c4690ffa53cb'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_min_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '4269b0fd612ee787b3603364c3d3b14da140c088c5325ba5ef56dd5d5d13a731',
       '30c5b5b93b277a6bac5bcd3f38c85010e94d50fa204a284848373b87f0803f62', '34ebee005c80ef347255b6b1d8cac891690b097995135a6f686d53d6059c5c53',
       '679906c9aa3a2a3b9be529fdd43ecffc1cac1ad4dd8620ffdce461e1dae02f11', 'result_c926f0b61f6061ebf95accbb', 'match_502a70173f44eef42fc64beb'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_min_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'a80110d5f372356df028942925bf889754363334f65cb7c5e911e0ac9c57c59e',
       '8922c946afb5a9d8b5e306cb9f4f47d24b01bfb54618c2dc267dc835f15a083b', '0ced4a5cfaf9d922d9957bf7a51af3afa82a2e029500b8540b887e56be034a54',
       'cd209dc87b71c5f478ad5738c801f0bd6e146e3cf7d4886a9def37afc2c1d5db', 'result_38e97b18b4c70750f3a0fbeb', 'match_736ce6870e1620672d09f529'),
    _m(SLOT1_ID, 'e2_min_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '6b60219434e79540b4649543ea213fa352705d69a3b15e46e2f1589417ce281e',
       '7e98f148bafe21c17abf0080c37500d5e7a9d1151d001dcfc8e1f9dc506198ca', 'cfbbf52fdc3c4d921c9a9532bbaac7e291060f1879d4dbf72a1957b9752eefe4',
       '221b6c859c8099fc8b2e2a456845d3446109320850e7c26c3f2fa2977f695c53', 'result_3f5ea7fb667001db20376e39', 'match_dd552d384807c848dea9eede'),
    _m(SLOT1_ID, 'e2_min_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd86ad09d2cb6d4cbe7b8e2fb69768752a18fa48a23d9f0ba70210f4eacbe8a8b',
       '38bfb3bec194101988ea073c8387f9e7734aa4a34fc63ba5ecb50ae5253c6d0a', '4666cc88f6f879abf3f52cc994ebbd0ca8d93daef7a703121db0427470215bc0',
       '9bb1a07b67587af4c0f5f2b23ea74a560a5269e93a58357242aa6e7a8fe13677', 'result_f95277637dce4be9d7af7e0c', 'match_1e1ea048c037b39cf77e632a'),
    _m(SLOT1_ID, 'e2_min_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '84838e5beb85b105c201e657b2e4139ff0d45c96db0b4d8b25719c0c8c7916a7',
       '78aecf53103fb61f4e1f6584947f81aec980e34cc6cb7ccd6f9356403382adfb', 'bfa5dec2cd2756db64c502bb83523fec784836f5edbf2a9ba29c5c5faab495e1',
       'd737b0f9cddff74c40529ab1305492ea44e54431f76e7d34d57093d27cf11172', 'result_7515a0f002891045ea94385f', 'match_38ee28febe71a13039c8bd2b'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_disrupt_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'd9402ec6c38d9e73f102956d3a7baac6855eac3b4c28278fa94c5c9230e6fbb5',
       'a01bcc7e26eae2509457bbddf62121b2016e346efb19a26529f82d92d2234dee', '820265b77d63c20be4fd85db49487fb2d83726202654cabcfb8d424efe0419a9',
       'fd2a88efba0e3110456d2960309966ec0d4f127ed2dc9a89ce48ca94a301e2c4', 'result_f42aace4402a9ea894cdf94c', 'match_26e6b773193f6f83f6b1fc41'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_disrupt_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '60cbef2596b9c5b6e6f5446a3438e7f294fcc7ed8ecf2ba43b58ede47a415b7b',
       '30c5b5b93b277a6bac5bcd3f38c85010e94d50fa204a284848373b87f0803f62', '66ad2c6686c668f8d5565ce5ec299ecb48caf0a60bc579cb194e8d7277f28e33',
       'a5a0a11662a55468cedfc0504113acbdec96742dbf4201110f1df579bef7ba2f', 'result_2cf7d88a8a18169929cc97f8', 'match_cf9c39c002347e2e3516bbbf'),
    _m(SLOT1_ID, 'e2_sniper', 'e2_disrupt_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '412d63c889d737c535205b50bad1900afbe436080dee1559d8f490aa92fa2940',
       '8922c946afb5a9d8b5e306cb9f4f47d24b01bfb54618c2dc267dc835f15a083b', 'bc0ffbabec7fb4fc48ac3d5769f1cec7a0a245523da7424c9b43c963968dbd2b',
       '7bda83b8cbad6890b1c8561e83a99e26cdb545b67cbcbb8e4d0be16b768b8e9d', 'result_abfa2aa2b9987f297383770f', 'match_84bbf6db805054318f628d61'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', '0e3c0a4abbc455aa8b062d27fc70336ba9c5eee9e3f7f8d56b9d1370c5fc2b6f',
       '7e98f148bafe21c17abf0080c37500d5e7a9d1151d001dcfc8e1f9dc506198ca', '65543f0bb77c24bc51395aff3ce5828241057acc5f424d242323d1f3ac65f851',
       '74ae827c26694b7d1db4b453beece45e0d6c7e67ed1dba366cd16eb777da2ccc', 'result_6dc93d05edfa4dfa1af6681f', 'match_f99bd1a9c4aa6961d6c9ee6b'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'f3d0804bd10cf464fb9a229f3c993bac03bb84b418d22284293efa31ad0e1296',
       '38bfb3bec194101988ea073c8387f9e7734aa4a34fc63ba5ecb50ae5253c6d0a', '2d5244d2bd69bb9390360b66359d7a6b2bfe0779b6c7c29a7cac543721163d04',
       '6d1191481be63cd23d690e03ec106b7b21f15d13878f3398053c880f8c8df937', 'result_f6a8b6da1b007ae1f4a88794', 'match_ff3b9943a1816f51c226a7a1'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (7000, 7000),
       (), 14000,
       '99cf9a5c7e4387e6275cafc1694c8e2a3f30bbf1aae4d28d1ddfef4346124711', 'c32ba4a574b5455b6b20897cb636cca2a5b2088509c2c3c640d37418e433476a',
       '78aecf53103fb61f4e1f6584947f81aec980e34cc6cb7ccd6f9356403382adfb', 'd3d6c6daf9ee55b4bb12f2a23cd84b47fd778b83e5629968e1b78492855a4b8e',
       '8d2a449375c978c43e8d0d63bb649c9ffae46b4f2de7a7145b0ea4e340ef7525', 'result_63f154742933304e70a346db', 'match_7381ff680a55fe63438ded7b'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 1, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000),
       (), 13992,
       '56e7723219e4deff368040b791ed5d71239f39e1b75e97932b47ad1e047563ea', '4316ba8bde5a6c2dfe3346875aa3ac7efaf7a8b5234708ab0b9d130a8108be33',
       'e9f5281133aed636ad645bb1847a2d8e9bb64cb2b926da4d15bf037d4344024b', '6fdabaf01166b264361536964be309f0ea8dffeeead0431d5ded12fcc552ec9a',
       'f4811c7b774c5f735c2bc5ef52439f42c58caeca8dfe871fa3f2ff5a2cef4d5b', 'result_c3ee531f555bbeeb8431f7d3', 'match_c76d4330c2cf801f4d897e2a'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 2, 'B', 1000, 'tick_limit', (1000.0, 7655.0), (6992, 7000),
       (), 13992,
       '34ddd973e11ff515eba17e1a824583dd02ec2a5333d5a35daf4551bc651a3cd0', 'd057895b6bc165925a1d0e84a20408afa1701a3ae7ae7a67fb34e5803922778c',
       '63af2e6405a60f2dce488bb3ce842f8efe8186b1d2fa01f6ba69ab839aee9ed2', 'c910702010d9291e7e9df84a746147a07bb413212c20eba2a7c605b9dfd9b2f8',
       'fe7f61c4080cb2327f6f39efe07b10692628b073eaf6ded24b987d661141484a', 'result_e1ec6fc06416e393cbb816e8', 'match_d2180a87699e8902c3220ab5'),
    _m(SLOT1_ID, 'e2_disrupt_guard', 'e2_guarded_painter', 3, 'B', 1000, 'tick_limit', (1000.0, 7653.0), (6992, 7000),
       (), 13992,
       'a4377f12f6deb4671ae3a1f7033d1a60d01d93e1fe07b46fceafaf21e95f0f34', '9a8f88d5814b20c9cfc77608c05791ed2beadd447e4bba142fda2d16a9bbfa0a',
       '343989d4d145149625297725d131a403f8f96c5a0ca4f5dfa1fd1983e7ec2eeb', '72a5a80a5eac964d3fba597272d940b6edd133b8866f7df4c3b7364d1de1516e',
       '1a8f20de84810d5d24272f7b98fbb7185c45e71834086641e30ce1f3b3cb354b', 'result_0a19f88863af6fb8d2b3181d', 'match_bf755dbf17bd6902b41c65bf'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 1, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992),
       (), 13992,
       '4a6f1842e5517f81bbbc03d7fe1b515b02acbfc9f79680354db50e3286bf6536', 'e877496db8c4658c6df70d897e1b6f761149c07ec0770cc5255bfa1df056c370',
       'ea5a92cef03046fb0c13472c2b35d01f3926e970bbd8beeade8e919337b832d2', 'ca0a7a5a6268e1a4e21585b85f63db4d1539df073a693369900fc704a8dd2bca',
       'ad5be98b429741f3f163440e365a455b1a46797a02a12a0486e274aaa51f4236', 'result_51ec9110d455c139776e8cc2', 'match_c415962344b84523c466afde'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 2, 'A', 1000, 'tick_limit', (7654.0, 1000.0), (7000, 6992),
       (), 13992,
       '0fe5b8cf1ccdc7086a8e51081118bc7bfe3e7b0765aadb6c34f634a2d85f02d7', 'e17bbbcb711fe38c17680fbe29b12b006fb6c0851fa38e91200181031f00ff3f',
       'e0af0983b7010394b3f768e9177e3cc063dd4d131fd9c3eecefc1c8a71997eef', '8b1851f5c7479d3d2eb2dfe6365e184a6f132f7d3507954ae875c82ae95da4f6',
       '2838eba43449d56bf84cdd2cd5919b4e2627997d19edc1e2dcf7fa818cfa4234', 'result_5688d7929a1fbb093ef304a8', 'match_1c3b5db24a54748d0de6c1c8'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_disrupt_guard', 3, 'A', 1000, 'tick_limit', (7652.0, 1000.0), (7000, 6992),
       (), 13992,
       'd4e2f8d4eb1beef7e6b1dca53277feee6ca16ada8fa16783ef083193d9d1f486', '2a39f4b087c7e6ed233a216b9964873cdd8e62b704830b3362a6ec03ad88347e',
       'f11553593420eb516318f2003f7bbfe0164a789c4a5f0b0bd1609f032b566cbc', '4cf6d8f0e310b28be853addfd8315f7d96af05a7fd6f620eb7cb64c1ceff23eb',
       '814a2f701ac924211272cd52275712d9d5e8f3fa847db8722735fe81a8a48dec', 'result_7990d290b93472857ed159a9', 'match_013d57928f15266d806cdc05'),
    _m(SLOT1_ID, 'e2_spread_sniper', 'e2_spread_defender', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', '21a5a0cd1a265395a2b24313d9e6e4eecb62962db75ce79f2165efaa1de5ffc7',
       '2f01135b318ff2afa79519f4e3a20f9e6ce108d8de304a5c6088f082837b9f20', '3d3cca621dd3b492dfc9a5c8820b83057ea2c4279436d5671241d9a83e2b88ae',
       'f7a0f43daaf35d485823083855e7d253a13b69eaae7184e0f4b9d0778f3a02fd', 'result_1db4c75f839fe30e354d5935', 'match_9f07d968b5b3adbbaafde772'),
    _m(SLOT1_ID, 'e2_spread_sniper', 'e2_spread_defender', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', '824cee3187caaf851aab5430370d9477b175d24d445199e0f0793071a4133768',
       'a71dce54cdeb1eee2baaa2f27460b414ab3759d0464fc28558ab9c8aea5fe9e6', '96255caddaad0dde8e62663957aa08e103c839d1c97b117b01aa3320a1a5160c',
       '944e35c2f564d1503cfc58f8848b284796e32a82bc18e572eb7de0ea683dfaca', 'result_857f7e0283ba0283dc4cdb28', 'match_7a133d49f2c01706751198ac'),
    _m(SLOT1_ID, 'e2_spread_sniper', 'e2_spread_defender', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', '4739d2fa1dfd719142c47dfeb16975b22f8c28493a7ed6b9fc174a21110b1f94',
       'dcc1e99b131c247a3ce8ec75b7181d8874296219b887891b199fa72ec65235c7', '73cc5f3a27ab7352e60a6b81ea6af703f2087071db0304c82fcbe6a115353dcc',
       '0f9176c4fb6937edf89c25cf7b609638e86a265eb6142385abb2599fc6d7c790', 'result_f8f73403b0d1ffa1aae30e0e', 'match_fa174fcbbcd6f3ed58eb85a1'),
    _m(SLOT1_ID, 'e2_spread_defender', 'e2_spread_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', 'ac9df061852a964caa2c7469df6248a8261dd68cefbc6c2aae2506fe2ed2a126',
       '5dd77500bcc405cdfa794bde6c204b3672e582fad535402bd8a4d3e2e81eb0ad', 'ca59c62037fa7a91bf5d8df2de4226ec359359bd00e2892c079842a46d6669f0',
       'a3c44e4f5695d042919b297d04b1c0a18d135e04bd964acb26616dd7d0ca5b1a', 'result_eb1bb5c792774cc9caab06f0', 'match_d05fa1087840e73ef0971791'),
    _m(SLOT1_ID, 'e2_spread_defender', 'e2_spread_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', '5bfc6d7631ba80865f82023614a16ab8a59cd8d2499cf401a49ba17e5e40a04c',
       '35955556679a7e7cffd0b73fe820d6a99b9c84c5f767dd93a0d0c15e0af909c1', '20aa06ef25e78ba88ea788305b2631b7473572c0ce8559efa462f2cf4828780d',
       '1c94020df4572717c83c9fee986b0630c58fc3c05b03539f63bff3814679c1b5', 'result_ab466daee829d05f4cb8c308', 'match_7e02c4286b14b42881f1ac29'),
    _m(SLOT1_ID, 'e2_spread_defender', 'e2_spread_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 7999),
       (), 15999,
       '4f8a5a23350b65efcd074ed3a19d9f6a3e864009b69850be6c35c28eab5a2e4f', '8ccae5c924697632a779f4bbc1ac97d6da2f1e22e8a16814784cecf488fb6b92',
       '421af569b161c0e47124e6b1f4b6c0bd1193c0e69ba78d39820bbc632c04ed35', '456b5714f7527c75a5abd239e30daaf190174e342477cdb8ea4421d253b1eb87',
       '794ae0af12306a0c931074486ddef4d28cd7f832fa8a0beb189ae1d3e6b0865b', 'result_2c117b945f65ad9d66501046', 'match_1310a716c4eb53aa9681394a'),
    _m(SLOT1_ID, 'v4_scout', 'e2_repair_guard', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 4521),
       (), 12521,
       'e489bad01780e2618984a7398f514f82a524e980f98f951123f8241a7f15404b', 'df4c8e5e880cfb6e4106b4675a725075db443fdce6b6f30672d75ca87a88dfc6',
       'ee632771c752e31cac4e6d06ca9d5b74a9320855927cb20efdfe102815c1979f', '929bf5b98a9d351057a4ed1ea114050a5dc09545d53ead0ef3e2e53d5a37ba0b',
       '9304e630dd7fd70409ef055f30e164ccb171536e3c645a19a3fc38b29a398e4f', 'result_a76d9d11d7ee19dbe302294f', 'match_cb6a218686c07b4c189dcc78'),
    _m(SLOT1_ID, 'v4_scout', 'e2_repair_guard', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 4518),
       (), 12518,
       '4430d527b79186dd608ac332d85de3e0ba932123f651cf81c281da81cbc970cb', '8507cb7f1d1e6c828ecc7d9429eb9f1c7a3449d22507ba04b3b7798bb24837f2',
       '4acb78cedcabe88a1a38479b6dbad4d2e0cb8a88b91b3f6ba24c0931ed80fae6', '580bf48d09c86e0e851dcc67f002372064f4ebe857064acf4cc4536301549f56',
       '03c2a6ae18c789737091e95a7b08f6bc5ac262d2fe4aa37b2eace18122ed321d', 'result_20676a38722194bb42032818', 'match_0d20dd5b95df4ea133b1b584'),
    _m(SLOT1_ID, 'v4_scout', 'e2_repair_guard', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (8000, 4522),
       (), 12522,
       'e912a1e784d7e5cb15bd25c407a9f62da94348d965b92e5ad5d32f20298f801f', '2de0ca3b93203c06d3834ef07f1bae41ae2080a29be09a6051de943e77d14f25',
       '7dd32f7dc95e1e6c09a1f58bb845fb1eb3274ff77df7e2f8ceda307080bba3dc', 'e48317632b325ecbd01ac3087ca707957f8ccc55e4007518ab80a7fd937de4c6',
       'f37e447682fa5bcc69d5201c6c28a3d611c74a8fdb5ae37e8fcf7a6cbc4e4f4e', 'result_f984a1d505c4144544d2a401', 'match_a14663dbf74417a59df67b8a'),
    _m(SLOT1_ID, 'e2_repair_guard', 'v4_scout', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4506, 8000),
       (), 12506,
       '2dc53fb1ceb2948727ae3dae3434fc00a20c38d01faa770dd3f0cfa1c9198ce3', 'ccca14efa4c722baf9138cb5f24a35f4f29e2a2cb9fbce9b1d76c1f103451184',
       '65d6eb9c790aa85a5bebb13e99e8ff626e9ccbe17b755d6ea4642d9eefc4b0b8', 'de332528bc1eda2302d6da8bc5f821d6d2f94435b48238177e6af3fa9c7aed14',
       '0a54ff71c64dd2b447e7394b68cd44fb5903807cefe9ebd983e72347cd09c6fc', 'result_3904d2b3eb3da8ea9f8731b6', 'match_2746d33035b8594766554787'),
    _m(SLOT1_ID, 'e2_repair_guard', 'v4_scout', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4510, 8000),
       (), 12510,
       '09d320a1c047d8cd4c46c7b1e29a5d8fd861fad31d15ff2f6c7ef7939caddaef', '719adb9e4136c7231a673db19a52ee9691701dc6197bd5fff1f3304bd56e0e09',
       '8a8f27b1ec2de5575f2204b8e7dda58bb17a01bc79d85876efe9046b178be70b', '373c24d29da6dd945115fe36b18b14599bec5174dd756fdabf908332cbd567c5',
       '60f3bf6050908e441c8e3c2a8a807dee29c8fd76827d712b35671ffcf55ddf3d', 'result_4856388698e9b2ec090a963a', 'match_d452a6e3881c952d129ae8bf'),
    _m(SLOT1_ID, 'e2_repair_guard', 'v4_scout', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4505, 8000),
       (), 12505,
       '14fedab8782613896bab9a33d442349e8d559d8c9a1eace9db5a70c4b64891b7', 'a572c53ecd5dbffce1ee772a6ca45b57008091295266d1f3515b932709f9ec54',
       '0fe32f09cd697981f556b6e9d4dde577f81ec75b6bbef4d3e8ee7d22322032ce', 'c5ccd5738577ce442eb9678833cd492a69a860074c01debc851198ef80c2391f',
       '23d4cad1cad7fafc65c7c2eddbe99f317b577826fc0c71c91fa855e47e9d902b', 'result_cfc9fb8409f67f411dcb7c2f', 'match_5493ddb27c3979cd14544e79'),
    _m(SLOT1_ID, 'v4_scout', 'e2_sniper', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (6973, 4538),
       (), 11511,
       '4ba48daf12f95d783633eac109e64e605e3b45443b50462abb4444867704fad9', 'cbf824116d72996b89b1fa1292213c4d8f43db54e414a2f5b6204378983634fd',
       '034725f667b8998d4f344ab26e1c9a61656a6ef3431157acdefc4268cb16e341', '6d83d3c96164837bec4d513c3d40830849f61d06ed077eecffe191d6a7814740',
       'f1a986ce8316ddb74591f32b9a350b30c84c384232afbf3e7d22de786053b50e', 'result_3941cf1c261ce1ffdca62380', 'match_43ca5229654cd2875e6cfe50'),
    _m(SLOT1_ID, 'v4_scout', 'e2_sniper', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (6978, 4532),
       (), 11510,
       'e722553e1355e66b865feef74a33f57acd605724b44768995847a4fa8769fed3', '6b795659c98a3f91baa57a2609cc0e3bbbb757e016acd1375761d5ac1340d3b2',
       '59c98ade9a1c519eeee425ad01f873b85bb1f87a5c612f697c91d1aa7c974534', 'ea849b7e56562f1b163a6dc08d685db7f896e7f98de708410542e986b9cc6a3c',
       '239f04d0fb146f04d5e8075a6d8acdde39ad3af3f0f41f254eef5f89a0e336d1', 'result_10a71b9cc8f75bbf08bc31fe', 'match_360098942a04c2076802c2dc'),
    _m(SLOT1_ID, 'v4_scout', 'e2_sniper', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (6973, 4539),
       (), 11512,
       '03dd6d280e64a09ec5247df8ba65d1af94c3f411942845b5428029eacf88e60b', '42b8379b8128dd30d50d589ae4164e77ed3884be3e1de696aaadc4737be19603',
       '06f108a49c1f9d7aa5be24c4836fe4ef919b1741b3b14ac72ac9dc01ba4e4739', '0591ddddbb6e5f4e733444b557c2f9ea863786fa903817d983985c0127c6ff50',
       '32c3f70118a51c556829d02446b7fec551ce6d8d9a389ce23257381cd8e42967', 'result_ceb4669abdbb6c28fd0552a9', 'match_1cc3856d5d21efed9848b973'),
    _m(SLOT1_ID, 'e2_sniper', 'v4_scout', 1, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4510, 6992),
       (), 11502,
       '2b52573bdcaf90088dfad03336a9d42087c47117dad53c18c624460301866833', '7b9e09a1d68281cc674b0a8ba726e6fa129ccc5f00adb42f9b0b8565517f6c90',
       '4a0dc4103f581ec5f1ed346255d0d7a46b9b7525b61a03bc032be1b12f954e21', '8859cfa48885d7a776370838e10173db190faec482452c9f0e209c9733267e0f',
       '5d138d7a42876e07187b51271a367ba663c8a4902b090ab7e82a6f6e3a9de929', 'result_00871219ab6ff0ff833a6caa', 'match_7cd9c719e7ed8e2f8bea9fcf'),
    _m(SLOT1_ID, 'e2_sniper', 'v4_scout', 2, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4517, 6987),
       (), 11504,
       '8d1bf3c40e143e67043e485676a3ca7c2ac9522f1359eb54d825f63f27185854', '096fa11573d094662f3e49841dec34dde833a612eab285509ee121472a84720d',
       'a99ab7604472fb6cfa82f964448a14085ee0f8e58a14d709d0f272e9a1e4c42f', '2136a99a8af0201ca1d1b8d4558326142e295a07ee1bcf2e994072be03378f21',
       '97999fd6dad5217419390e8c5acbfd8bc318a84b5d8b95a355538b1ec9680408', 'result_70cea973681e58561871bafc', 'match_325196f6f2e46dbb830399f4'),
    _m(SLOT1_ID, 'e2_sniper', 'v4_scout', 3, 'tie', 1000, 'tick_limit', (1000.0, 1000.0), (4510, 6992),
       (), 11502,
       '2b52573bdcaf90088dfad03336a9d42087c47117dad53c18c624460301866833', '05e391261102ca171b4257396f885a6c6120413ba25b15ab1cec0cf8a59c7162',
       '2539801f12589cff15dfc327deb270299ca744be3caee33e8e57f4b349ea4288', '648d90df3da3fc9683cb1b12b340728250d3d2bbd9bbe52c0151f231934a1d03',
       '9aa873273769ff0d78935f701a7a332537fec2e4d0c0759df039516cc6db6427', 'result_987c33dfe7978eeea8b0e009', 'match_014d241113c71c341a770696'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')), 656,
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       'e53a97a76f2541b7bac4ade43bffccc7661bdc915b92ab55c9fbfc956f3e1687', 'dff734c2f0fcdefbbcf11c98a0c3d2117b2283dba0f8f83749ff33e0ce514bb4',
       'f8a153c9b8d07f46cb2b84d07b1f453cf04a56dd701877457038cbe00c839bb9', 'result_b4613eb8208176c3a63d0e0e', 'match_d7f1abba6508a1ef09454aee'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')), 992,
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       '4fd048ee6ab760e00cf70dafdb95781dcd0747a30add6b43a0d9459b232e48d1', '696b21beb78df001d988172695cf6b5ceea90d8e994e8e8c4d1d378f62253a57',
       'd3a575687ce545e389cceabf047b5cc204ddd06cba912a75b565e1230a6eacca', 'result_04654a4f2cf9d91c20b9b597', 'match_3bfd127a97e81671ddcbc824'),
    _m(SLOT1_ID, 'e2_guarded_painter', 'e2_guarded_painter_twin', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301),
       ((43, 'kill', 'A', 'B'),), 601,
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       '0d43fafabb508d651717cb2f1ffc95fd23c0d59e2f26cd8278a59de80faf5cb6', '60d5cb95d7918a568d445113802d2ac086fad5f302c0cc8d950eedc1ea1b8ffc',
       '4078497fd283190add9d4aa64df87d16c860259792f8e542d81fd10e1e6900d5', 'result_dbcb6ac2b9f0292556ed23ae', 'match_92dbf63e8c4a522db47eb848'),
    _m(SLOT1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 1, 'tie', 47, 'all_agents_dead', (109.0, 109.0), (328, 328),
       ((47, 'kill', 'A', 'B'), (47, 'kill', 'B', 'A')), 656,
       'd6afe56dd5839206cfda018502ae92d9d792def6560892f7db094c4945390ab4', '8dd7b395780fc079917d46488e415a9a71710f00f106fbcae05225df68570cd1',
       'e53a97a76f2541b7bac4ade43bffccc7661bdc915b92ab55c9fbfc956f3e1687', 'dff734c2f0fcdefbbcf11c98a0c3d2117b2283dba0f8f83749ff33e0ce514bb4',
       '4679e074e00f32748194d835e24f917fda808e8a0dc92b1cdb7ffb4a5ad4f2eb', 'result_9137fa5119ee7df891a9f0dd', 'match_3fd22be4150ebee67cde298d'),
    _m(SLOT1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 2, 'tie', 71, 'all_agents_dead', (221.0, 217.0), (496, 496),
       ((71, 'kill', 'A', 'B'), (71, 'kill', 'B', 'A')), 992,
       '31f13673ccb6781cd657f898277e5591d38d18ca8c4fb43d0f0304312eeb18f8', 'd22959c97254bab69bd8ab4cb7013085da91ad0c4e11a68a7377c1eeca2d92e4',
       '4fd048ee6ab760e00cf70dafdb95781dcd0747a30add6b43a0d9459b232e48d1', '696b21beb78df001d988172695cf6b5ceea90d8e994e8e8c4d1d378f62253a57',
       'e86cf005d0076054bed3a22cd113c3b8f6e3f1fb67a46b63053419d62789b0b0', 'result_4f0fe460a7fc1f149d789943', 'match_6feddbcfe12eec1108c9040b'),
    _m(SLOT1_ID, 'e2_guarded_painter_twin', 'e2_guarded_painter', 3, 'B', 43, 'last_agent_standing', (90.0, 96.0), (300, 301),
       ((43, 'kill', 'A', 'B'),), 601,
       'e2d95dc0ef22013fbfbce1e200bbf2d32670c1c808198466b93762d9ec776530', 'fe44a9d9a8962e14de5ab9bd21de310f564f5111319e9fd6b874a79569811af1',
       '0d43fafabb508d651717cb2f1ffc95fd23c0d59e2f26cd8278a59de80faf5cb6', '60d5cb95d7918a568d445113802d2ac086fad5f302c0cc8d950eedc1ea1b8ffc',
       'ef68aa268bf5e39015cda419e33598c030b3f7a4ce685058d12239efbdb341af', 'result_f22fc7b5b214dc65bba474c5', 'match_b69b48183762ffc8d8db32db'),
)


def test_frozen_corpus_covers_the_declared_matrix() -> None:
    assert [
        (case.ruleset_id, case.seat_a, case.seat_b, case.seed) for case in FROZEN_E6_PARENT_CORPUS
    ] == list(corpus_cases())
    assert len(FROZEN_E6_PARENT_CORPUS) == len(RULESETS) * len(PAIRINGS) * 2 * len(SEEDS) == 84


def test_frozen_corpus_exercises_the_visibility_e6_changes() -> None:
    # Guard: the corpus must contain long matches and captures under both
    # parents, and the bounded-reach scout must actually search, or its
    # identity would say little about the ``None`` visibility path.
    for ruleset_id in RULESETS:
        rows = [case for case in FROZEN_E6_PARENT_CORPUS if case.ruleset_id == ruleset_id]
        assert any(case.reason == "tick_limit" and case.ticks == MAX_TICKS for case in rows), ruleset_id
        assert any(case.captures for case in rows), ruleset_id
        assert all(case.decisions > 0 for case in rows), ruleset_id


@pytest.mark.parametrize("frozen", FROZEN_E6_PARENT_CORPUS, ids=lambda case: case.label)
def test_parent_is_byte_identical_to_the_pre_e6_freeze(tmp_path: Path, frozen: FrozenMatch) -> None:
    observed = run_corpus_match(
        tmp_path, frozen.ruleset_id, frozen.seat_a, frozen.seat_b, frozen.seed
    )
    assert (observed.winner, observed.ticks, observed.reason, observed.score) == (
        frozen.winner,
        frozen.ticks,
        frozen.reason,
        frozen.score,
    )
    assert observed.actions == frozen.actions
    assert observed.captures == frozen.captures
    assert observed.decisions == frozen.decisions
    assert observed.anchors_sha256 == frozen.anchors_sha256
    assert observed.observations_sha256 == frozen.observations_sha256
    assert observed.cpu_sha256 == frozen.cpu_sha256
    assert observed.writes_sha256 == frozen.writes_sha256
    assert observed.match_id == frozen.match_id
    assert observed.result_id == frozen.result_id
    assert observed.replay_sha256 == frozen.replay_sha256
