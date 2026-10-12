"""The E8 pre-match compatibility gate (PR8 Sec 13, A1 containment; plan Sec 4.5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 2.3,
3.3 and 13. Each package is classified statically (``discipline.classify``):

* a **context-gated SENSE** package passes only on C8, T8, C8L or T8L;
* an **ungated SENSE** package passes only on T8 or T8L;
* every other SENSE pairing is refused **before the match starts**.

A package that references no SENSE at all is not a SENSE pairing, and this
gate does not refuse it. The four condition Rulesets are read from the frozen
transcription, so the gate cannot drift from the registration.

This module is the harness-layer check only. Calling it before every match is
the runner's job (phase I8-5, ``run_e8.py``); nothing here runs a match.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from types import MappingProxyType

from tools.research.v6.e8 import discipline
from tools.research.v6.e8.preregistration import load_preregistration

_CONDITIONS: Mapping[str, str] = MappingProxyType(
    {condition["id"]: condition["ruleset_id"] for condition in load_preregistration()["conditions"]}
)
#: The Ruleset of each registered condition: C8, T8, C8L and T8L.
CONDITION_RULESETS: Mapping[str, str] = _CONDITIONS
#: Where each static class may play.
ACCEPTED: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        discipline.CONTEXT_GATED: frozenset(_CONDITIONS[c] for c in ("C8", "T8", "C8L", "T8L")),
        discipline.UNGATED: frozenset(_CONDITIONS[c] for c in ("T8", "T8L")),
    }
)


class IncompatiblePairing(ValueError):
    """A package and a Ruleset that A1 containment refuses before the match."""


def compatible(static_class: str, ruleset_id: str) -> bool:
    """Whether a package of ``static_class`` may play under ``ruleset_id``."""

    if static_class not in discipline.CLASSES:
        raise ValueError(f"unknown static class {static_class!r}")
    if static_class == discipline.NONE:
        return True
    return ruleset_id in ACCEPTED[static_class]


def require_compatible(package_dirs: Iterable[Path], ruleset_id: str) -> dict[str, str]:
    """Classify every package and refuse the pairing unless each may play under ``ruleset_id``.

    Returns each package's name mapped to its static class. Raises
    :class:`IncompatiblePairing`, naming every refused package, before any
    match exists.
    """

    classes = {package.name: discipline.classify_package(package) for package in package_dirs}
    refused = sorted(name for name, static_class in classes.items() if not compatible(static_class, ruleset_id))
    if refused:
        raise IncompatiblePairing(
            f"Ruleset {ruleset_id!r} refuses "
            + ", ".join(f"{name} ({classes[name]} SENSE)" for name in refused)
            + " before the match (PR8 Sec 13)"
        )
    return classes
