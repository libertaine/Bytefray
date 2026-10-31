"""Passive preservation of the 23 original Classic promotion goldens.

Recovered unchanged from f127be70e7ed88449c1b737f4675e1453ec8de45.
Per-scenario hashes pin every digest and outcome field without running Classic.
This preserves evidence, not live equivalence qualification.

Original live-guard provenance follows (historical):

Frozen-golden characterization of ``bytefray-rules-4``, pinning the
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
from typing import Any

import pytest

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


FROZEN_RECORD_SHA256 = {
    "grid-256-0": "be98104e8a1595c47286e4bc108f941ddfa7cfa303d19198b4e18df437bc8746",
    "grid-256-1": "f9e2b49240d61bd5c00ec8f069fc5bfaf91fb717d8ac0603445cf34897f77bcb",
    "grid-256-3": "a7fccffc68ce54d7a57e1aa7edc2ebcad78896ed76995f3c114da66c233b1b91",
    "grid-256-7": "837305d129d2785314b22a486c47450b20625bfcc08cf1c5813138b868bc1571",
    "grid-256-42": "0cf6b9b7c2ef1f46900f38a66024c60cdf33cce34cb74a5b0bce737729a6ddd6",
    "grid-512-0": "a3006b5fd89f791a49c9585567a5b1a6bed587d3290facd314738b4499a72af5",
    "grid-512-1": "68adbd97ed658bcdbfe2ab0419392e9d1894f8ad53e003f2c2594d3e4313566a",
    "grid-512-3": "c413ee825d6b0e90f9291b946ef98b377e536e9c59e506bdb519ec0866cb6baa",
    "grid-512-7": "751b38487ccd3292036338f810554caf194da39e07a8d14bc5cdcb6f0d466db8",
    "grid-512-42": "1a130ff1bf5e51588ba85bdfaac93bc46af7f6fc065cf139536438468af433db",
    "grid-1024-0": "b0794ca6ec4a8b54089990da5fe42fabadad8e961526f68411b7222ad3fb8bc3",
    "grid-1024-1": "b4d96cae5cc6b969cc5a05149993fdeb9935b800ffa8711302d061c53f54e0e5",
    "grid-1024-3": "df1f3c817725559bc5c155e9839ad80ac8f2d5599f008b9339fa9d16019d76dd",
    "grid-1024-7": "575a87f45dc33f99b3a3e38209e0a9320afc8f8d2d09edb2c653e34739fccaa6",
    "grid-1024-42": "2448a50685c9a2801a54bf74fd5fd0fe02a1d833887a4bb5ae9d0a872048002e",
    "three-entrant": "18e7d161c016090b46382a9c21a0cb722a285ce6f769306972e7f0fbf102ebbc",
    "four-entrant": "1f6620164b17faa2c07c0ba0659eb9bb973966d6edbed331d4cf63de763b23bf",
    "hydra-nemesis-512-0": "60437a4952f7b83c6b25fc3d65cae3194fb4e5a65ae0d804e64158692b4f8657",
    "hydra-nemesis-512-7": "2beb3fb8de0cfeb1ec5b5b62472f8c6665110ac340c31d4a27834daeb3d47070",
    "hydra-nemesis-1024-0": "da920f89a04ad755b8251a97e0eacb01531587806d813241e81e9eb9fd335f97",
    "hydra-nemesis-1024-7": "cae688cae3416aa00ee775390ee0b354d6d6e79b0b45be8d1b08adf2aa7ba876",
    "multiproc-vs-singleproc": "ea9a24e5f2701dc39cc0e5d0b7173d3c81ad3069e4bd3af6f610a22680761e1f",
    "ticklimit": "08703575e23f081efe726f57b6b2cf1f20c0e66175bd287161f3e5d3cfdafce4"
}


@pytest.mark.parametrize("scenario", tuple(EXPECTED))
def test_original_promotion_record_is_preserved(scenario: str) -> None:
    assert len(EXPECTED) == 23
    encoded = json.dumps(EXPECTED[scenario], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == FROZEN_RECORD_SHA256[scenario]
