"""Display names for the Rulesets Bytefray offers for new matches.

A display name is a label for people -- "Active Sensing (Alpha)" -- and
nothing else. The canonical Ruleset identity (``battle_engine.rules``)
remains the only machine identity: it is what ``--ruleset`` accepts, what
result/replay/trace artifacts record, what capability checks compare and
what diagnostics show. A display name is therefore:

* never persisted in any artifact, cache or manifest;
* never accepted as input (``--ruleset Classic`` is rejected, and
  ``resolve_ruleset_policy``/``normalize_ruleset_id`` know nothing of it);
* never used to decide compatibility; and
* free to be refined in a later application release, because nothing
  depends on its spelling.

Only the product-offered identities (the public stable and public
experimental lifecycle sets in ``ruleset_policy``) have display names.
Historical, retired and research identities deliberately have none -- since
its retirement that includes ``bytefray-rules-4``, formerly "Classic" -- so
a retired identity never reads like a current product choice. Readers show
those by their exact ID or by the ID's own shape. See
``docs/COMPONENT_VERSIONING.md``.

Standard library only, like ``battle_engine.rules``, so every layer (CLI,
client, Designer) can share this one table.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID

# The stability marker belongs to the name of an experimental Ruleset, so it
# is visible wherever the name is. It describes the Ruleset's maturity, not
# the application's prerelease state.
RULESET_DISPLAY_NAMES: Mapping[str, str] = MappingProxyType(
    {
        BYTEFRAY_RULESET_V6_ALPHA1_ID: "Active Sensing (Alpha)",
    }
)

ACTIVE_SENSING_DISPLAY_NAME = RULESET_DISPLAY_NAMES[BYTEFRAY_RULESET_V6_ALPHA1_ID]


def ruleset_display_name(ruleset_id: str) -> str | None:
    """The display name for ``ruleset_id``, or ``None`` when it has none.

    An exact lookup, never prefix or pattern matching.
    """

    return RULESET_DISPLAY_NAMES.get(ruleset_id)


def ruleset_name_with_id(ruleset_id: str) -> str:
    """``Active Sensing (Alpha) (bytefray-rules-6-alpha1)``; the bare ID when there is no display name."""

    name = ruleset_display_name(ruleset_id)
    return ruleset_id if name is None else f"{name} ({ruleset_id})"


__all__ = [
    "ACTIVE_SENSING_DISPLAY_NAME",
    "RULESET_DISPLAY_NAMES",
    "ruleset_display_name",
    "ruleset_name_with_id",
]
