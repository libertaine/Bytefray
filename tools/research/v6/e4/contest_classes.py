"""The a-priori E4 contest-class table (design review Sec D.1, Sec N "Contest class").

Every E4 pairing is assigned MULTI-PASS, OPENING-ONLY or INCIDENTAL from the
fixtures' *source roles* alone -- what each fixture's code writes, per the
review's Sec D.1 table -- never from any match outcome, control or treatment.
The classification function takes two agent names and nothing else.

Source roles (Sec D.1; a twin has its primary's roles):

* ``writes_enemy_anchor`` -- writes the enemy anchor, which is enemy core
  cell 0 because every process spawns on its core base;
* ``repairs_own_base`` -- writes its own core cell 0 as a repair;
* ``repairs_own_non_base`` -- writes its own non-base core cells as repairs;
* ``writes_enemy_non_base`` -- writes the enemy's non-base core cells.

Derivation (Sec D.1 "Contest classes, derived from the table alone"):

* **MULTI-PASS** -- one side writes the other's non-base core cells and the
  other repairs non-base core cells, so the same cells are fought in every
  pass;
* **OPENING-ONLY** -- no multi-pass contest exists, but one side writes the
  other's anchor (its core cell 0) and the other repairs its base, so the
  fight happens once per tick, in pass 1;
* **INCIDENTAL** -- neither: core cells change hands only incidentally (a
  painting front crossing a core, or an attack nobody repairs).

One role needs a reading, recorded here and in the pre-registration
(O-CONTEST-ROLES): Sec D.1 gives ``e2_repair_guard`` no *base-only* repair,
but its cyclic cursor writes every own core cell, cell 0 included, across
ticks. Sec D.2 files "repair guard v guarded painter" under OPENING-ONLY
because "the guard's cursor sets whether its base repair comes before or
after" the painter's hit, so the repair guard counts as repairing its base.

``CONTEST_CLASSES_SHA256`` pins the committed ``contest_classes.json``; the
matrix digest includes it, so the table is frozen with the matrix.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTEST_CLASSES_PATH = Path(__file__).with_name("contest_classes.json")
CONTEST_CLASSES_SCHEMA = "bytefray.v6.e4.contest_classes"
CONTEST_CLASSES_VERSION = 1
CONTEST_CLASSES_SHA256 = "47097041e36189e4a92c837080055cacd40ab53c4203f699564550d6507f7969"

MULTI_PASS = "MULTI-PASS"
OPENING_ONLY = "OPENING-ONLY"
INCIDENTAL = "INCIDENTAL"
CLASSES: tuple[str, ...] = (MULTI_PASS, OPENING_ONLY, INCIDENTAL)
TWIN_SUFFIX = "_twin"


@dataclass(frozen=True)
class SourceRoles:
    writes_enemy_anchor: bool
    repairs_own_base: bool
    repairs_own_non_base: bool
    writes_enemy_non_base: bool
    # The review's Sec D.1 cell texts, kept verbatim for the record.
    table_row: tuple[str, str, str, str]


# Review Sec D.1, row by row. The four booleans are the table's columns;
# ``repairs_own_base`` for the repair guard is O-CONTEST-ROLES (see above).
SOURCE_ROLES: dict[str, SourceRoles] = {
    "e2_sniper": SourceRoles(True, False, False, True, ("first action", "—", "—", "yes (sweep)")),
    "v4_probe": SourceRoles(True, False, False, True, ("first action", "—", "—", "yes (sweep)")),
    "e2_disrupt_guard": SourceRoles(True, True, True, False, ("first action", "(cell 0 as part of 0–6)", "yes (0–6)", "—")),
    "e2_min_guard": SourceRoles(True, True, False, True, ("first action", "yes", "—", "yes")),
    "e2_repair_guard": SourceRoles(False, True, True, False, ("—", "—", "yes (cyclic cursor across ticks)", "—")),
    "e2_guarded_painter": SourceRoles(True, True, False, False, ("first action", "yes", "—", "— (paints outward)")),
    "e2_greedy_painter": SourceRoles(False, False, False, False, ("—", "—", "—", "— (paints outward)")),
    "e2_spread_sniper": SourceRoles(True, False, False, True, ("each visible anchor", "—", "—", "yes")),
    "e2_spread_defender": SourceRoles(True, True, False, True, ("each visible anchor", "yes", "—", "yes")),
    "e3_jam_sniper": SourceRoles(True, False, False, True, ("on every even action", "—", "—", "yes (odd actions)")),
}


class ContestClassError(RuntimeError):
    """The contest-class table is missing, altered, or does not derive from the source roles."""


def primary_name(agent: str) -> str:
    return agent.removesuffix(TWIN_SUFFIX)


def roles_of(agent: str) -> SourceRoles:
    try:
        return SOURCE_ROLES[primary_name(agent)]
    except KeyError:
        raise ContestClassError(f"{agent!r} has no Sec D.1 source roles") from None


def classify(first: str, second: str) -> str:
    """The contest class of one pairing, from the two fixtures' source roles alone."""
    a, b = roles_of(first), roles_of(second)
    if (a.writes_enemy_non_base and b.repairs_own_non_base) or (b.writes_enemy_non_base and a.repairs_own_non_base):
        return MULTI_PASS
    if (a.writes_enemy_anchor and b.repairs_own_base) or (b.writes_enemy_anchor and a.repairs_own_base):
        return OPENING_ONLY
    return INCIDENTAL


def pair_key(first: str, second: str) -> str:
    return f"{first}|{second}"


def build_table(fields: Mapping[str, Iterable[tuple[str, str]]]) -> dict[str, Any]:
    """The canonical table for the given ``{field_id: pairs}``."""
    return {
        "schema": CONTEST_CLASSES_SCHEMA,
        "version": CONTEST_CLASSES_VERSION,
        "authority": "docs/research/v6/V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md Sec D.1, Sec N",
        "rule": (
            "MULTI-PASS: one side writes the other's non-base core cells and the other repairs non-base core "
            "cells. OPENING-ONLY: no multi-pass contest, but one side writes the other's anchor (its core cell 0) "
            "and the other repairs its base. INCIDENTAL: neither. Assigned from source roles alone, before any "
            "treatment data exists; a twin has its primary's roles."
        ),
        "source_roles": {
            name: {
                "writes_enemy_anchor": roles.writes_enemy_anchor,
                "repairs_own_base": roles.repairs_own_base,
                "repairs_own_non_base": roles.repairs_own_non_base,
                "writes_enemy_non_base": roles.writes_enemy_non_base,
                "review_sec_d1_row": list(roles.table_row),
            }
            for name, roles in sorted(SOURCE_ROLES.items())
        },
        "classes": {
            field_id: {pair_key(a, b): classify(a, b) for a, b in pairs}
            for field_id, pairs in fields.items()
        },
    }


def canonical_bytes(table: Mapping[str, Any]) -> bytes:
    return (json.dumps(table, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def table_sha256(path: Path = CONTEST_CLASSES_PATH) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_table(path: Path = CONTEST_CLASSES_PATH, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """The committed table; fails closed if its bytes changed or it no longer
    derives from the source roles."""
    if not path.is_file():
        raise ContestClassError(f"No contest-class table at {path}.")
    digest = table_sha256(path)
    expected = CONTEST_CLASSES_SHA256 if expected_sha256 is None else expected_sha256
    if digest != expected:
        raise ContestClassError(f"contest_classes.json SHA-256 {digest} != the frozen {expected}")
    table: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    problems = [
        f"{field_id}/{key}"
        for field_id, rows in table["classes"].items()
        for key, value in rows.items()
        if classify(*key.split("|")) != value
    ]
    if problems:
        raise ContestClassError(f"contest classes no longer derive from the source roles: {problems}")
    return table


def class_of(table: Mapping[str, Any], field_id: str, first: str, second: str) -> str:
    """The frozen class of one pairing (either orientation) in one field."""
    rows = table["classes"][field_id]
    for key in (pair_key(first, second), pair_key(second, first)):
        if key in rows:
            value: str = rows[key]
            return value
    raise ContestClassError(f"{field_id}: no frozen contest class for {first!r} v {second!r}")
