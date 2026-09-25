"""E6 registered interpretation (PR Sec 7) and kill evaluation and disposition (Sec 8).

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 7-8, as tables.
A row applies if and only if E6-D has the row's status and (E6-H1T, E6-H1C)
is among its listed combinations. The rows cover every combination exactly
once. A triple that maps to no row or to two fails closed
(``InterpretationInvariantError``), as does any status outside the
registered vocabulary. A negated hypothesis is never written: NEITHER and
REFUTED are listed separately.

Recorded alongside every row, never inputs to it: E6-H3, PF-1 to PF-4, the
ADAPT reading and the companion reading.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from itertools import product

SUPPORTED = "SUPPORTED"
REFUTED = "REFUTED"
NEITHER = "NEITHER"
STATUSES: tuple[str, ...] = (SUPPORTED, REFUTED, NEITHER)
PASS = "PASS"
FAIL = "FAIL"
GATE_STATUSES: tuple[str, ...] = (PASS, FAIL)

VOID = "VOID"
REJECT = "REJECT as a gameplay candidate"
CANDIDATE = "CANDIDATE"
NOT_ESTABLISHED = "NOT ESTABLISHED"
KILL_CRITERIA: tuple[str, ...] = ("KC-1", "KC-2", "KC-3", "KC-4", "KC-5")


class InterpretationInvariantError(RuntimeError):
    """A combination maps to no registered row, or to more than one: fail closed."""


@dataclass(frozen=True)
class Row:
    row_id: str
    e6d: str
    pairs: frozenset[tuple[str, str]]
    reading: str


ALL_PAIRS = frozenset(product(STATUSES, STATUSES))

ROWS: tuple[Row, ...] = (
    Row("STOP", FAIL, ALL_PAIRS,
        "STOP. No gameplay reading: the treatment, the family or the protocol is defective."),
    Row("R-CREATES", PASS, frozenset({(SUPPORTED, REFUTED)}),
        "Under the parent, one fixed policy is a best response to every opponent. Under priced sensing, none "
        "is: priced sensing creates an opponent-dependent choice of how to allocate actions."),
    Row("R-PREEXISTING", PASS, frozenset({(SUPPORTED, SUPPORTED)}),
        "An opponent-dependent choice exists under both the parent and priced sensing. Priced sensing is not "
        "necessary for it. Recorded as relevant to Branch A. The E6-H2 status is recorded alongside."),
    Row("R-TREATMENT-ONLY", PASS, frozenset({(SUPPORTED, NEITHER)}),
        "No fixed policy is a best response to every opponent under priced sensing. Under the parent the "
        "evidence is indeterminate, so creation is not established."),
    Row("R-REMOVES", PASS, frozenset({(REFUTED, SUPPORTED)}),
        "Priced sensing removes an opponent-dependent choice present under the parent."),
    Row("R-NO-CHOICE", PASS, frozenset({(REFUTED, REFUTED)}),
        "A fixed policy is a best response to every opponent under both."),
    Row("R-TREATMENT-DOMINANT", PASS, frozenset({(REFUTED, NEITHER)}),
        "A fixed policy is a best response to every opponent under priced sensing. Under the parent the "
        "evidence is indeterminate."),
    Row("NONE", PASS, frozenset({(NEITHER, SUPPORTED), (NEITHER, REFUTED), (NEITHER, NEITHER)}),
        '"No registered interpretation row applies" is itself the registered outcome. The tables in Sec 6.4 '
        "are reported."),
)

#: R-CREATES is qualified by E6-H2 (NEITHER and REFUTED share one qualifier).
H2_QUALIFIER: dict[str, str] = {
    SUPPORTED: "and spending less on information beats spending more against at least one opponent: an "
               "information/action tradeoff, not a discovery tax",
    NEITHER: "but the registered lower-information contrast does not show less information winning, so the "
             "choice is not shown to be an information-cost tradeoff",
    REFUTED: "but the registered lower-information contrast does not show less information winning, so the "
             "choice is not shown to be an information-cost tradeoff",
}
#: R-NO-CHOICE is qualified by E6-H0.
H0_QUALIFIER: dict[str, str] = {
    SUPPORTED: "priced sensing acts as a discovery tax: outcomes are preserved and delayed",
    REFUTED: "a dominant policy under both, with outcomes restructured",
    NEITHER: "a dominant policy under both; delay-only is neither established nor excluded",
}


def _check_status(name: str, value: str, allowed: Sequence[str]) -> None:
    if value not in allowed:
        raise InterpretationInvariantError(f"{name} status {value!r} is outside {list(allowed)}")


def row_for(e6d: str, h1t: str, h1c: str, rows: Sequence[Row] = ROWS) -> Row:
    """The one registered row for (E6-D, E6-H1T, E6-H1C); fails closed otherwise."""

    _check_status("E6-D", e6d, GATE_STATUSES)
    _check_status("E6-H1T", h1t, STATUSES)
    _check_status("E6-H1C", h1c, STATUSES)
    matches = [row for row in rows if row.e6d == e6d and (h1t, h1c) in row.pairs]
    if len(matches) != 1:
        raise InterpretationInvariantError(
            f"(E6-D, E6-H1T, E6-H1C) = ({e6d}, {h1t}, {h1c}) maps to {[row.row_id for row in matches]}")
    return matches[0]


def qualifier(row: Row, *, h2: str, h0: str) -> str | None:
    """The registered qualifier of R-CREATES (by E6-H2) or R-NO-CHOICE (by E6-H0)."""
    _check_status("E6-H2", h2, STATUSES)
    _check_status("E6-H0", h0, STATUSES)
    if row.row_id == "R-CREATES":
        return H2_QUALIFIER[h2]
    if row.row_id == "R-NO-CHOICE":
        return H0_QUALIFIER[h0]
    return None


def disposition(e6d: str, fired: Collection[str], row: Row, *, h2: str) -> str:
    """PR Sec 8, exhaustive: VOID, then REJECT, then CANDIDATE, else NOT ESTABLISHED."""
    _check_status("E6-D", e6d, GATE_STATUSES)
    _check_status("E6-H2", h2, STATUSES)
    unknown = set(fired) - set(KILL_CRITERIA)
    if unknown:
        raise InterpretationInvariantError(f"unknown kill criteria {sorted(unknown)}")
    if e6d == FAIL:
        return VOID
    if fired:
        return REJECT
    if row.row_id == "R-CREATES" and h2 == SUPPORTED:
        return CANDIDATE
    return NOT_ESTABLISHED


def kc1_label(universal: Collection[str], search_of: dict[str, str]) -> str:
    """KC-1's label, from the universal set at the point estimate (PR Sec 8)."""
    if not universal:
        raise InterpretationInvariantError("KC-1 fires only with a universal member")
    if all(search_of[member] != "none" for member in universal):
        return "search race"
    if "GREED" in universal:
        return "greed dominance"
    return "other dominance: " + ", ".join(sorted(universal))


def interpret(*, e6d: str, h1t: str, h1c: str, h2: str, h0: str, fired: Collection[str]) -> dict[str, object]:
    row = row_for(e6d, h1t, h1c)
    return {
        "row": row.row_id,
        "reading": row.reading,
        "qualifier": qualifier(row, h2=h2, h0=h0),
        "disposition": disposition(e6d, fired, row, h2=h2),
    }
