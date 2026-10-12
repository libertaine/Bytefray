"""The V6 E8 family: members, packages and opaque package IDs (phase I8-3).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 3.1
and 3.3, and the implementation plan Sec 5.1. Eleven members, each a parameter
setting of the one shared policy source (``fixtures/agents/<package>/agent.py``,
byte-identical in every package), and each shipped as a primary package and a
twin used only in mirrors.

Package IDs are opaque (``e8_q01`` .. ``e8_q22``; plan decision P8-10). The
assignment below is a fixed, documented shuffle --
``random.Random("v6-e8-package-ids").shuffle`` of the (member, role) slots in
member order, E6's convention -- recorded here as a literal so it can never
drift, and checked against that derivation by a test. At runtime every entrant
is its seat label, so no package ID ever reaches a match (PR8 Sec 3.3).

The member table is the manifest form of PR8 Sec 3.1's parameter table. The
manifest's scalar parameters cannot hold the registration's ``null``, so a
registered ``reacquire`` of "--" (``null`` in the transcription) is the choice
``none``, and a member the table gives no ``stress`` has ``stress: false``
(:data:`REGISTERED_ENCODING`). A test checks the table against the frozen
transcription under exactly that encoding.

Nothing here generates a seed, builds a matrix identity or runs a match.
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from battle_engine.agent_parameters import resolve_parameters
from battle_engine.agents import resolve_agent

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"
FINGERPRINTS_PATH = Path(__file__).resolve().parent / "family_fingerprints.json"

ParameterSetting = Mapping[str, bool | int | str]


def _member(acquire: str, reacquire: str, posture: str, evade: str, processes: int,
            stress: bool = False) -> ParameterSetting:
    return MappingProxyType({"acquire": acquire, "reacquire": reacquire, "posture": posture, "evade": evade,
                             "processes": processes, "stress": stress})


#: The eleven members in PR8 Sec 3.1 order, as manifest parameter settings.
MEMBERS: Mapping[str, ParameterSetting] = MappingProxyType(
    {
        "RUSH8": _member("spatial-fast", "once", "attack", "off", 1),
        "REACQ8": _member("spatial-fast", "repeat", "attack", "off", 1),
        "PACED8": _member("spatial-paced", "once", "attack", "off", 1),
        "STEALTH8": _member("ownership", "once", "attack", "off", 1),
        "LURK8": _member("none", "none", "attack", "off", 1),
        "SPLIT8": _member("spatial-fast", "once", "attack", "off", 2),
        "GUARD8": _member("spatial-fast", "once", "guard", "off", 1),
        "EVADE8": _member("spatial-fast", "once", "guard", "on-hit", 1),
        "GREED8": _member("none", "none", "paint", "off", 1),
        "ADAPT8": _member("spatial-fast", "adaptive", "attack", "off", 1),
        "STRESS8": _member("none", "none", "guard", "off", 1, stress=True),
    }
)
#: How a registered value that a manifest scalar cannot hold is written in a
#: manifest: (parameter, registered value) -> manifest value.
REGISTERED_ENCODING: Mapping[tuple[str, Any], Any] = MappingProxyType(
    {("reacquire", None): "none", ("stress", None): False}
)
#: Pi: every member, the opponent set (PR8 Sec 3.1).
OPPONENTS: tuple[str, ...] = tuple(MEMBERS)
#: Pi_F: every member but ADAPT8, the candidate best responses (PR8 Sec 3.1).
FIXED_MEMBERS: tuple[str, ...] = tuple(member for member in MEMBERS if member != "ADAPT8")
#: A8: the frozen five-member acquisition-policy candidate set of H8-CHANNEL
#: (PR8 Sec 3.1), frozen with the family.
A8: tuple[str, ...] = ("RUSH8", "REACQ8", "PACED8", "STEALTH8", "LURK8")
ROLES: tuple[str, ...] = ("primary", "twin")

#: Package ID -> (member, role).
PACKAGES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "e8_q01": ("GREED8", "primary"),
        "e8_q02": ("EVADE8", "twin"),
        "e8_q03": ("REACQ8", "twin"),
        "e8_q04": ("STEALTH8", "primary"),
        "e8_q05": ("PACED8", "twin"),
        "e8_q06": ("GREED8", "twin"),
        "e8_q07": ("SPLIT8", "primary"),
        "e8_q08": ("LURK8", "primary"),
        "e8_q09": ("PACED8", "primary"),
        "e8_q10": ("RUSH8", "twin"),
        "e8_q11": ("LURK8", "twin"),
        "e8_q12": ("STRESS8", "twin"),
        "e8_q13": ("GUARD8", "primary"),
        "e8_q14": ("ADAPT8", "twin"),
        "e8_q15": ("EVADE8", "primary"),
        "e8_q16": ("ADAPT8", "primary"),
        "e8_q17": ("SPLIT8", "twin"),
        "e8_q18": ("GUARD8", "twin"),
        "e8_q19": ("REACQ8", "primary"),
        "e8_q20": ("STEALTH8", "twin"),
        "e8_q21": ("RUSH8", "primary"),
        "e8_q22": ("STRESS8", "primary"),
    }
)
PACKAGE_ID_SHUFFLE_SEED = "v6-e8-package-ids"


def package_id(member: str, role: str = "primary") -> str:
    """The opaque package ID of ``member``'s ``role`` package."""

    (found,) = [pid for pid, slot in PACKAGES.items() if slot == (member, role)]
    return found


def manifest_text(pid: str) -> str:
    """The exact ``agent.yaml`` of package ``pid``: its member's values as defaults.

    Every string value is quoted: YAML 1.1 would otherwise read ``off`` as a
    boolean.
    """

    member, _role = PACKAGES[pid]
    values = MEMBERS[member]
    return (
        f"name: {pid}\n"
        f"display: E8 family package {pid}\n"
        "description: Research-only V6 E8 family package (implementation plan Sec 5). "
        "Not a product starter agent.\n"
        "kind: python\n"
        "api_version: 2\n"
        "entrypoint: agent.py:create_agent\n"
        'version: "1.0.0"\n'
        "parameters:\n"
        "  acquire:\n"
        "    type: choice\n"
        '    choices: ["none", "spatial-fast", "spatial-paced", "ownership"]\n'
        f'    default: "{values["acquire"]}"\n'
        "  reacquire:\n"
        "    type: choice\n"
        '    choices: ["none", "once", "repeat", "adaptive"]\n'
        f'    default: "{values["reacquire"]}"\n'
        "  posture:\n"
        "    type: choice\n"
        '    choices: ["attack", "guard", "paint"]\n'
        f'    default: "{values["posture"]}"\n'
        "  evade:\n"
        "    type: choice\n"
        '    choices: ["off", "on-hit"]\n'
        f'    default: "{values["evade"]}"\n'
        "  processes:\n"
        "    type: integer\n"
        "    minimum: 1\n"
        "    maximum: 2\n"
        f"    default: {values['processes']}\n"
        "  stress:\n"
        "    type: boolean\n"
        f"    default: {'true' if values['stress'] else 'false'}\n"
    )


def resolved_parameters(pid: str) -> dict[str, Any]:
    """Package ``pid``'s parameters as a match resolves them from its manifest (no overrides)."""

    return dict(resolve_parameters(resolve_agent(FIXTURE_DIR.parent, pid).parameter_schema))


def frozen_parameters(role: str = "primary") -> dict[str, dict[str, Any]]:
    """Each member's parameters, read from its ``role`` package's manifest on disk."""

    return {member: resolved_parameters(package_id(member, role)) for member in MEMBERS}


def census(role: str = "primary") -> tuple[str, ...]:
    """PR8 Sec 3.5's static census, applied to the frozen manifests' parameters.

    ``decision.census`` is the registered static procedure (phase I8-0); this
    feeds it what the packages on disk actually declare, never the
    transcription's own table.
    """

    from tools.research.v6.e8 import decision

    return decision.census(frozen_parameters(role))


def fingerprints() -> dict[str, dict[str, str]]:
    """Each package's member, role and file digests."""

    return {
        pid: {
            "member": PACKAGES[pid][0],
            "role": PACKAGES[pid][1],
            "agent_py_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.py").read_bytes()).hexdigest(),
            "agent_yaml_sha256": hashlib.sha256((FIXTURE_DIR / pid / "agent.yaml").read_bytes()).hexdigest(),
        }
        for pid in sorted(PACKAGES)
    }


def prepare_data_root(root: Path, package_ids: Iterable[str]) -> None:
    """Copy each named package into ``root/agents/<package>`` for a match."""

    for pid in package_ids:
        if pid not in PACKAGES:
            raise KeyError(f"not an E8 family package: {pid!r}")
        target = root / "agents" / pid
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(FIXTURE_DIR / pid, target, ignore=shutil.ignore_patterns("__pycache__"))
