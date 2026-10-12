"""The V6 E6 matched family: members, packages and opaque package IDs.

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 3 and
docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 5.1. Nine
members, each a parameter setting of the one shared policy source
(``fixtures/agents/<package>/agent.py``, byte-identical in every package), and
each shipped as a primary package and a twin used only in mirrors.

Package IDs are opaque (``e6_q01`` .. ``e6_q18``; design review Sec M,
decision 8). The assignment below is a fixed, documented shuffle --
``random.Random("v6-e6-package-ids").shuffle`` of the (member, role) slots in
member order -- recorded here as a literal so it can never drift, and
checked against that derivation by a test. At runtime every entrant is its
seat label, so no package ID ever reaches a match (PR Sec 3.2).
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import MappingProxyType

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "agents"

#: The nine members in PR Sec 3.1 order, as parameter settings.
MEMBERS: Mapping[str, Mapping[str, bool | int | str]] = MappingProxyType(
    {
        "RUSH": {"search": "fast", "posture": "attack", "evade": False, "processes": 1, "adaptive": False},
        "PACED": {"search": "paced", "posture": "attack", "evade": False, "processes": 1, "adaptive": False},
        "SPLIT": {"search": "fast", "posture": "attack", "evade": False, "processes": 2, "adaptive": False},
        "STEALTH": {"search": "read", "posture": "attack", "evade": False, "processes": 1, "adaptive": False},
        "LURK": {"search": "none", "posture": "attack", "evade": False, "processes": 1, "adaptive": False},
        "GUARD": {"search": "none", "posture": "guard", "evade": False, "processes": 1, "adaptive": False},
        "EVADER": {"search": "none", "posture": "guard", "evade": True, "processes": 1, "adaptive": False},
        "GREED": {"search": "none", "posture": "paint", "evade": False, "processes": 1, "adaptive": False},
        # ADAPT's own rules override search, posture and evade; it starts as
        # GREED (paint), so its manifest carries GREED's values for them.
        "ADAPT": {"search": "none", "posture": "paint", "evade": False, "processes": 1, "adaptive": True},
    }
)
#: Pi: every member, the opponent set (PR Sec 3.1).
OPPONENTS: tuple[str, ...] = tuple(MEMBERS)
#: Pi_F: every member but ADAPT, the candidate best responses (PR Sec 3.1).
FIXED_MEMBERS: tuple[str, ...] = tuple(member for member in MEMBERS if member != "ADAPT")
ROLES: tuple[str, ...] = ("primary", "twin")

#: Package ID -> (member, role).
PACKAGES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "e6_q01": ("PACED", "primary"),
        "e6_q02": ("EVADER", "primary"),
        "e6_q03": ("GREED", "primary"),
        "e6_q04": ("GREED", "twin"),
        "e6_q05": ("SPLIT", "twin"),
        "e6_q06": ("ADAPT", "primary"),
        "e6_q07": ("STEALTH", "primary"),
        "e6_q08": ("GUARD", "twin"),
        "e6_q09": ("PACED", "twin"),
        "e6_q10": ("RUSH", "primary"),
        "e6_q11": ("GUARD", "primary"),
        "e6_q12": ("STEALTH", "twin"),
        "e6_q13": ("ADAPT", "twin"),
        "e6_q14": ("LURK", "twin"),
        "e6_q15": ("EVADER", "twin"),
        "e6_q16": ("RUSH", "twin"),
        "e6_q17": ("SPLIT", "primary"),
        "e6_q18": ("LURK", "primary"),
    }
)
PACKAGE_ID_SHUFFLE_SEED = "v6-e6-package-ids"


def package_id(member: str, role: str = "primary") -> str:
    """The opaque package ID of ``member``'s ``role`` package."""

    (found,) = [pid for pid, slot in PACKAGES.items() if slot == (member, role)]
    return found


def manifest_text(pid: str) -> str:
    """The exact ``agent.yaml`` of package ``pid``: its member's values as defaults."""

    member, _role = PACKAGES[pid]
    values = MEMBERS[member]

    def flag(value: bool | int | str) -> str:
        return "true" if value is True else "false" if value is False else str(value)

    return (
        f"name: {pid}\n"
        f"display: E6 family package {pid}\n"
        "description: Research-only V6 E6 matched-family package (implementation plan Sec 5). "
        "Not a product starter agent.\n"
        "kind: python\n"
        "api_version: 2\n"
        "entrypoint: agent.py:create_agent\n"
        'version: "1.0.0"\n'
        "parameters:\n"
        "  search:\n"
        "    type: choice\n"
        "    choices: [none, fast, paced, read]\n"
        f"    default: {values['search']}\n"
        "  posture:\n"
        "    type: choice\n"
        "    choices: [attack, guard, paint]\n"
        f"    default: {values['posture']}\n"
        "  evade:\n"
        "    type: boolean\n"
        f"    default: {flag(values['evade'])}\n"
        "  processes:\n"
        "    type: integer\n"
        "    minimum: 1\n"
        "    maximum: 2\n"
        f"    default: {flag(values['processes'])}\n"
        "  adaptive:\n"
        "    type: boolean\n"
        f"    default: {flag(values['adaptive'])}\n"
    )


def fingerprints() -> dict[str, dict[str, str]]:
    """Each package's member, role and file digests, as recorded at the family freeze."""

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
    """Copy each named package into ``root/agents/<package>`` for a match or evaluation."""

    for pid in package_ids:
        if pid not in PACKAGES:
            raise KeyError(f"not an E6 family package: {pid!r}")
        target = root / "agents" / pid
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(FIXTURE_DIR / pid, target)
