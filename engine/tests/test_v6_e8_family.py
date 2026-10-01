"""V6 E8: the frozen family -- packages, manifests, the census, the D8-9 gate, the
pre-match compatibility gate, randomness and identities (phase I8-3).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 3,
5.1 (D8-9) and 13, and the implementation plan Sec 4.5 and 5. Nothing here
plays a match: the policy is driven with constructed observations, and the
package checks are static. The state-machine tests are in
``test_v6_e8_family_policy.py`` and the engine-level behavior tests in
``test_v6_e8_family_engine.py``.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import pytest
from _e8_family_harness import (
    ACTIVE,
    MODES,
    PASSIVE,
    POLICY,
    frozen,
    load_policy,
    make,
    obs,
)
from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.ruleset_policy import (
    _RULESET_POLICIES,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID,
    BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID,
)

from tools.research.v6.e8 import compatibility, decision, discipline, family
from tools.research.v6.e8.family import (
    A8,
    FINGERPRINTS_PATH,
    FIXED_MEMBERS,
    FIXTURE_DIR,
    MEMBERS,
    OPPONENTS,
    PACKAGE_ID_SHUFFLE_SEED,
    PACKAGES,
    REGISTERED_ENCODING,
    ROLES,
    manifest_text,
    package_id,
    prepare_data_root,
)

PARAMETERS = ("acquire", "reacquire", "posture", "evade", "processes", "stress")


# ---------------------------------------------------------------------------
# The members, the sets and the registered parameter table
# ---------------------------------------------------------------------------


def test_the_family_is_the_registered_eleven_members_and_sets() -> None:
    assert OPPONENTS == decision.MEMBERS == decision.PI
    assert len(OPPONENTS) == 11
    assert FIXED_MEMBERS == decision.PI_F
    assert A8 == decision.A8 == ("RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8")
    assert not set(MEMBERS) - set(decision.MEMBERS)  # no purpose-built twelfth member (B-4)


@pytest.mark.parametrize("member", OPPONENTS)
def test_the_member_table_is_the_transcription_under_the_documented_encoding(member: str) -> None:
    registered = decision.PARAMETERS[member]
    for parameter in PARAMETERS:
        value = registered.get(parameter)
        assert MEMBERS[member][parameter] == REGISTERED_ENCODING.get((parameter, value), value), parameter
    # Every registered key is either a manifest parameter or encoded in the
    # policy source (SPLIT8's sensor and shares, checked by the declarations).
    assert set(registered) - set(PARAMETERS) <= {"role", "acquire_process", "shares"}


def test_split8s_registered_sensor_and_shares_are_the_sources() -> None:
    registered = decision.PARAMETERS["SPLIT8"]
    assert registered["acquire_process"] == "sensor"
    assert registered["shares"] == {"sensor": "1/4", "striker": "3/4"}
    assert (POLICY.SENSOR_SHARE, POLICY.STRIKER_SHARE) == (0.25, 0.75)


def test_a8_is_the_comparable_single_process_attack_policies() -> None:
    comparable = tuple(m for m in FIXED_MEMBERS if MEMBERS[m]["posture"] == "attack" and MEMBERS[m]["processes"] == 1
                       and MEMBERS[m]["evade"] == "off" and not MEMBERS[m]["stress"])
    assert comparable == A8
    # Posture, processes and evasion are fixed across them: they differ only
    # in how and when they acquire (PR8 Sec 3.1).
    for member in A8:
        fixed = {key: MEMBERS[member][key] for key in ("posture", "evade", "processes", "stress")}
        assert fixed == {"posture": "attack", "evade": "off", "processes": 1, "stress": False}


# ---------------------------------------------------------------------------
# Packages, manifests, IDs and fingerprints
# ---------------------------------------------------------------------------


def test_package_ids_are_opaque_and_the_documented_shuffle() -> None:
    assert sorted(PACKAGES) == [f"e8_q{i:02d}" for i in range(1, 23)]
    slots = [(member, role) for member in OPPONENTS for role in ROLES]
    random.Random(PACKAGE_ID_SHUFFLE_SEED).shuffle(slots)
    assert dict(PACKAGES) == {f"e8_q{i:02d}": slot for i, slot in enumerate(slots, start=1)}
    assert sorted(PACKAGES.values()) == sorted((member, role) for member in OPPONENTS for role in ROLES)
    for member in OPPONENTS:
        assert package_id(member, "primary") != package_id(member, "twin")


def test_the_package_directories_are_exactly_the_twenty_two() -> None:
    assert sorted(path.name for path in FIXTURE_DIR.iterdir()) == sorted(PACKAGES)
    for pid in PACKAGES:
        assert sorted(path.name for path in (FIXTURE_DIR / pid).iterdir() if path.name != "__pycache__") == [
            "agent.py", "agent.yaml"]


def test_every_package_shares_one_byte_identical_policy_source() -> None:
    sources = {(FIXTURE_DIR / pid / "agent.py").read_bytes() for pid in PACKAGES}
    assert len(sources) == 1
    (source,) = sources
    assert b"\r" not in source


@pytest.mark.parametrize("pid", sorted(PACKAGES))
def test_each_manifest_is_its_members_parameters_as_defaults(pid: str) -> None:
    member, _role = PACKAGES[pid]
    assert (FIXTURE_DIR / pid / "agent.yaml").read_bytes() == manifest_text(pid).encode("utf-8")
    assert frozen(pid) == dict(MEMBERS[member])


@pytest.mark.parametrize("member", OPPONENTS)
def test_primary_and_twin_differ_only_in_their_identity_lines(member: str) -> None:
    primary, twin = package_id(member, "primary"), package_id(member, "twin")
    assert (FIXTURE_DIR / primary / "agent.py").read_bytes() == (FIXTURE_DIR / twin / "agent.py").read_bytes()
    lines = [(FIXTURE_DIR / pid / "agent.yaml").read_text(encoding="utf-8").splitlines() for pid in (primary, twin)]
    changed = [line for line in difflib.ndiff(*lines) if line[:2] in ("- ", "+ ")]
    assert changed == [f"- name: {primary}", f"- display: E8 family package {primary}",
                       f"+ name: {twin}", f"+ display: E8 family package {twin}"] or sorted(changed) == sorted(
        [f"- name: {primary}", f"+ name: {twin}", f"- display: E8 family package {primary}",
         f"+ display: E8 family package {twin}"])
    assert frozen(primary) == frozen(twin)


def test_family_fingerprints_are_recorded_and_current() -> None:
    recorded = json.loads(FINGERPRINTS_PATH.read_text(encoding="utf-8"))
    assert recorded == family.fingerprints()
    assert recorded == {
        pid: {
            "member": PACKAGES[pid][0],
            "role": PACKAGES[pid][1],
            "agent_py_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.py").read_bytes()).hexdigest(),
            "agent_yaml_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.yaml").read_bytes()).hexdigest(),
        }
        for pid in sorted(PACKAGES)
    }
    assert len({entry["agent_py_sha256"] for entry in recorded.values()}) == 1
    assert len({entry["agent_yaml_sha256"] for entry in recorded.values()}) == 22


def test_prepare_data_root_copies_packages_byte_for_byte(tmp_path: Path) -> None:
    prepare_data_root(tmp_path, ["e8_q03", "e8_q15"])
    for pid in ("e8_q03", "e8_q15"):
        assert sorted(path.name for path in (tmp_path / "agents" / pid).iterdir()) == ["agent.py", "agent.yaml"]
        for name in ("agent.py", "agent.yaml"):
            assert (tmp_path / "agents" / pid / name).read_bytes() == (FIXTURE_DIR / pid / name).read_bytes()
    with pytest.raises(KeyError):
        prepare_data_root(tmp_path, ["e6_q01"])


# ---------------------------------------------------------------------------
# The H8-REPEAT census (PR8 Sec 3.5): re-derived from the implemented family
# ---------------------------------------------------------------------------


def test_the_census_from_the_frozen_manifests_is_the_registered_one() -> None:
    # The registered static procedure, fed what the 22 manifests on disk
    # declare (not the transcription's own table). A mismatch is a stop.
    registered = tuple(decision.REGISTRATION["census"]["predicted"])
    assert registered == ("EVADE8",)
    assert family.census("primary") == registered
    assert family.census("twin") == registered
    assert decision.census() == registered


def test_the_census_reads_the_parameters_it_is_given() -> None:
    # The procedure is not a constant: an on-hit GUARD8 would join it.
    parameters = family.frozen_parameters()
    parameters["GUARD8"] = {**parameters["GUARD8"], "evade": "on-hit"}
    assert decision.census(parameters) == ("GUARD8", "EVADE8")


# ---------------------------------------------------------------------------
# D8-9: the static discipline and containment gate
# ---------------------------------------------------------------------------


def test_every_package_passes_the_discipline_gate() -> None:
    assert discipline.check_packages(FIXTURE_DIR / pid for pid in PACKAGES) == {pid: [] for pid in sorted(PACKAGES)}
    assert discipline.passes(FIXTURE_DIR / pid for pid in PACKAGES)


GUARDED = "if self.sensing_window is not None:\n    x = AgentAction(ActionKindV2.SENSE, 1)\n"
PLANTED = {
    # E6's D-5 rules, unchanged.
    "imports placement": ("from battle_engine.placement import seeded_seat_starts\n", "import"),
    "imports python_runtime": ("from battle_engine.python_runtime import derive_agent_seed\n", "import"),
    "imports random": ("import random\n", "import"),
    "relative import": ("from . import helper\n", "import"),
    "reads context.seed": ("def reset(self, context):\n    self.s = context.seed\n", "attribute"),
    "calls open": ("def f():\n    return open('x')\n", "name"),
    "calls exec": ("exec('1')\n", "name"),
    "calls __import__": ("__import__('os')\n", "name"),
    # E8's package IDs.
    "contains a package id": ('ME = "e8_q03"\n', "package-id"),
    "package id in a comment": ("# I am e8_q19\n", "package-id"),
    # The added SENSE guard rule.
    "an unguarded SENSE": ("def f():\n    return AgentAction(ActionKindV2.SENSE, 1)\n", "sense-guard"),
    "SENSE by its wire value": ("def f():\n    return AgentAction(ActionKindV2('sense'), 1)\n", "sense-guard"),
    "SENSE in the else branch": (("if self.sensing_window is not None:\n    pass\nelse:\n"
                                  "    x = AgentAction(ActionKindV2.SENSE, 1)\n"), "sense-guard"),
    "guarded by is None": ("if self.sensing_window is None:\n    x = AgentAction(ActionKindV2.SENSE, 1)\n",
                           "sense-guard"),
    "guarded on another attribute": (("if self.detection_radius is not None:\n"
                                      "    x = AgentAction(ActionKindV2.SENSE, 1)\n"), "sense-guard"),
    "guarded by an or": ("if self.sensing_window is not None or True:\n    x = AgentAction(ActionKindV2.SENSE, 1)\n",
                         "sense-guard"),
    "the guard set to a constant": ("def reset(self, context):\n    self.sensing_window = 27\n", "sense-guard"),
    "the guard unpacked": ("def reset(self, context):\n    self.sensing_window, y = 27, 1\n", "sense-guard"),
    "the guard augmented": ("def reset(self, context):\n    self.sensing_window += 1\n", "sense-guard"),
}


@pytest.mark.parametrize("name", sorted(PLANTED))
def test_the_gate_fails_every_planted_negative_control(name: str, tmp_path: Path) -> None:
    source, rule = PLANTED[name]
    found = discipline.violations(source)
    assert found and {violation.rule for violation in found} == {rule}
    package = tmp_path / "planted"
    package.mkdir()
    (package / "agent.py").write_text(
        (FIXTURE_DIR / "e8_q01" / "agent.py").read_text(encoding="utf-8") + "\n" + source, encoding="utf-8")
    assert not discipline.passes([package])


def test_the_gate_accepts_the_whitelist_and_grounded_guards() -> None:
    allowed = (
        "from __future__ import annotations\nimport math\nimport collections.abc\nfrom typing import Any\n"
        "from battle_engine.agent_api import AgentAction, ActionKindV2\nx = context.rng.random()\n"
        "def reset(self, context):\n    self.sensing_window = context.sensing_window\n    self.other = None\n"
        "def init(self):\n    self.sensing_window: int | None = None\n"
        "def act(self, obs):\n"
        "    if self.sensing_window is not None and obs.current_tick > 1:\n"
        "        return AgentAction(ActionKindV2.SENSE, 1)\n"
        "    if sensing_window is not None:\n"
        "        if obs.current_tick:\n"
        "            return AgentAction(ActionKindV2.SENSE, 2)\n"
    )
    assert discipline.violations(allowed) == []
    assert discipline.classify(allowed) == discipline.CONTEXT_GATED


def test_the_static_classes() -> None:
    plain = "from battle_engine.agent_api import AgentAction, ActionKindV2\nx = AgentAction(ActionKindV2.READ, 1)\n"
    assert discipline.classify(plain) == discipline.NONE
    assert discipline.classify(GUARDED) == discipline.CONTEXT_GATED
    for name in ("an unguarded SENSE", "SENSE by its wire value", "SENSE in the else branch", "guarded by is None",
                 "guarded on another attribute", "guarded by an or"):
        assert discipline.classify(PLANTED[name][0]) == discipline.UNGATED, name
    # A sensing guard that is not grounded in the context makes a guarded SENSE ungated.
    assert discipline.classify(GUARDED + PLANTED["the guard set to a constant"][0]) == discipline.UNGATED
    for pid in PACKAGES:
        assert discipline.classify_package(FIXTURE_DIR / pid) == discipline.CONTEXT_GATED


# ---------------------------------------------------------------------------
# The pre-match compatibility gate (PR8 Sec 13)
# ---------------------------------------------------------------------------

C8, T8 = BYTEFRAY_RULESET_V6_RESEARCH_SENSING_R32_ID, BYTEFRAY_RULESET_V6_RESEARCH_SENSING_ACTIVE_W27_ID
C8L = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32_ID
T8L = BYTEFRAY_RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27_ID
EVERY_RULESET = tuple(sorted(_RULESET_POLICIES))


def test_the_gate_reads_the_registered_condition_rulesets() -> None:
    assert dict(compatibility.CONDITION_RULESETS) == {"C8": C8, "T8": T8, "C8L": C8L, "T8L": T8L}
    # The ungated class's Rulesets are exactly the registered Rulesets with active sensing.
    assert compatibility.ACCEPTED[discipline.UNGATED] == {
        ruleset_id for ruleset_id, policy in _RULESET_POLICIES.items() if policy.sensing_mode == "active"}


@pytest.mark.parametrize("static_class", discipline.CLASSES)
def test_the_accept_reject_matrix_over_every_registered_ruleset(static_class: str) -> None:
    expected = {
        discipline.NONE: set(EVERY_RULESET),
        discipline.CONTEXT_GATED: {C8, T8, C8L, T8L},
        discipline.UNGATED: {T8, T8L},
    }[static_class]
    assert {r for r in EVERY_RULESET if compatibility.compatible(static_class, r)} == expected
    assert len(EVERY_RULESET) > 4
    with pytest.raises(ValueError):
        compatibility.compatible("gated-ish", T8)


def _planted_package(root: Path, name: str, source: str) -> Path:
    package = root / name
    package.mkdir(parents=True)
    (package / "agent.py").write_text(source, encoding="utf-8")
    return package


@pytest.mark.parametrize("ruleset_id", EVERY_RULESET)
def test_require_compatible_refuses_before_the_match(tmp_path: Path, ruleset_id: str) -> None:
    family_packages = [FIXTURE_DIR / pid for pid in sorted(PACKAGES)]
    ungated = _planted_package(tmp_path, "ungated", PLANTED["an unguarded SENSE"][0])
    plain = _planted_package(tmp_path, "plain", "x = 1\n")
    # The family: context-gated, so accepted exactly on the four conditions.
    if ruleset_id in (C8, T8, C8L, T8L):
        assert compatibility.require_compatible(family_packages, ruleset_id) == {
            pid: discipline.CONTEXT_GATED for pid in sorted(PACKAGES)}
    else:
        with pytest.raises(compatibility.IncompatiblePairing, match="context-gated SENSE"):
            compatibility.require_compatible(family_packages, ruleset_id)
    # An ungated SENSE package: only T8 and T8L.
    if ruleset_id in (T8, T8L):
        assert compatibility.require_compatible([ungated, plain], ruleset_id) == {
            "ungated": discipline.UNGATED, "plain": discipline.NONE}
    else:
        with pytest.raises(compatibility.IncompatiblePairing, match=r"ungated \(ungated SENSE\)"):
            compatibility.require_compatible([ungated, plain], ruleset_id)
    # A package with no SENSE is never refused by this gate.
    assert compatibility.require_compatible([plain], ruleset_id) == {"plain": discipline.NONE}


# ---------------------------------------------------------------------------
# Declarations and the fixed draw order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("member", OPPONENTS)
def test_declarations(member: str, mode: str) -> None:
    declared = [(d.id, d.reach, d.share) for d in make(member, mode=mode).declare_processes()]
    if member == "SPLIT8":
        assert declared == [("sensor", 256, 0.25), ("striker", 256, 0.75)]
    else:
        assert declared == [("main", 256, 1.0)]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rng_seed", [0, 1, 2, 3, 99, 12345])
def test_reset_draws_exactly_sigma_then_the_paint_side(rng_seed: int, mode: str) -> None:
    expected = random.Random(rng_seed)
    sigma, side = (-1, 1)[expected.randrange(2)], expected.randrange(2)
    for member in OPPONENTS:
        rng = random.Random(rng_seed)
        agent = make(member, mode=mode, rng=rng)
        assert (agent.direction, agent.paint_side) == (sigma, side)
        assert rng.getstate() == expected.getstate()  # nothing else was drawn (P8-1)


def _rich_script(mode: str, pids: tuple[str, ...]) -> list[ObservationV2]:
    """A long, deterministic script: anchors appearing, moving and vanishing, damaged own cells, and gaps."""

    script: list[ObservationV2] = []
    anchors = [None, 300, 300, 320, None, None, 310, 310, 450, None, 455, 455, None, 300, 300]
    tick = 0
    for step, anchor in enumerate(anchors):
        tick += 2 if step in (5, 11) else 1  # two whole ticks with no callback
        count = 6 if step in (3, 8) else 8   # two ticks with fewer than 8 callbacks
        for index in range(count):
            pid = pids[index % len(pids)]
            seen = () if anchor is None else (anchor,)
            if mode == PASSIVE:
                script.append(obs(tick, pid=pid, visible=seen, value=0xCE if index % 3 else 1,
                                  owner="B" if index % 4 == 1 else "A"))
            else:
                script.append(obs(tick, pid=pid, sensed=seen if index % 2 else None,
                                  value=0xCE if index % 3 else 1, owner="B" if index % 4 == 1 else "A"))
    return script


def _drive(agent: Any, script: list[ObservationV2]) -> list[AgentAction]:
    actions = []
    for observation in script:
        actions.append(agent.act(observation))
    return actions


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("member", OPPONENTS)
def test_primary_and_twin_packages_draw_and_act_identically(member: str, mode: str) -> None:
    pids = ("sensor", "striker") if member == "SPLIT8" else ("main",)
    runs = []
    for pid in (package_id(member, "primary"), package_id(member, "twin")):
        rng = random.Random(4)
        agent = make(mode=mode, module=load_policy(pid), parameters=frozen(pid), rng=rng)
        runs.append((_drive(agent, _rich_script(mode, pids)), rng.getstate()))
    assert runs[0] == runs[1]
    assert runs[0][0]


@pytest.mark.parametrize("member", OPPONENTS)
def test_no_member_ever_returns_sense_without_a_sensing_window(member: str) -> None:
    pids = ("sensor", "striker") if member == "SPLIT8" else ("main",)
    actions = _drive(make(member, mode=PASSIVE, rng_seed=6), _rich_script(PASSIVE, pids))
    assert actions
    assert all(action.kind is not ActionKindV2.SENSE for action in actions)


def test_the_sense_helper_refuses_without_a_window() -> None:
    agent = make("RUSH8", mode=PASSIVE)
    with pytest.raises(RuntimeError, match="no SENSE without a sensing window"):
        agent._sense(obs(1), "discover", 200)
    assert agent.pending == {}


@pytest.mark.parametrize("member", OPPONENTS)
def test_under_active_only_an_inferred_hit_moves_an_anchor(member: str) -> None:
    # The census's E-1 is decided statically by `evade` = on-hit (PR8 Sec 3.5).
    # Its premise in the source: under "active", acquisition, verification and
    # re-acquisition are SENSE actions, so only an evasion is a MOVE.
    pids = ("sensor", "striker") if member == "SPLIT8" else ("main",)
    script = _rich_script(ACTIVE, pids)
    agent = make(member, mode=ACTIVE, rng_seed=6)
    moves = [(o.current_tick, agent.callback_index) for o, action in
             ((o, agent.act(o)) for o in script) if action.kind is ActionKindV2.MOVE]
    if member == "EVADE8":
        assert moves and {index for _, index in moves} == {1}
        assert len(moves) == 4  # two skipped ticks and two short ticks
    else:
        assert moves == []
