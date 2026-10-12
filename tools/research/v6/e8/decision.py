"""E8 registered decision logic (pre-registration §4 to §8, revision 5).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md governs. Every
registered value used here (vocabularies, member sets, thresholds, rows,
readings, qualifier texts, label names and orders) is read from the frozen
transcription, which ``preregistration.load_preregistration`` verifies against
the markdown. Nothing registered is restated in this file; the code supplies
only the predicates, in the registered order, and checks at import that its
orders are the transcription's.

Every function fails closed (``DecisionInvariantError``) on a status outside
the registered vocabulary, on a combination the registration says cannot
occur, and on any mapping that would give no answer or two.

Contents:

* O-BOOT: the registered draws; stab(P) >= 9/10 as at least 900 of 1,000;
* hypothesis statuses: bootstrapped, H8-REPEAT with the census, H8-FL and
  H8-TAX;
* the seat criterion: O-NEUTRAL, PF8-4 and H8-SEAT, with every draw
  recomputing control and treatment from one seed-position tuple;
* §7: the rows, the qualifiers, the H8-REPEAT and H8-ADAPT readings and the
  core answer;
* §8: the kill criteria and their labels, and the disposition;
* §6.6: the companion reading;
* structure: the static census (§3.5), D8-3's matched pairs, the seat units
  and CQ8-4's control-against-control check.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from types import MappingProxyType
from typing import Any

from tools.research.v6.e8.preregistration import load_preregistration

REGISTRATION: Mapping[str, Any] = load_preregistration()


class DecisionInvariantError(RuntimeError):
    """A registered mapping gave no answer or two, or a registered impossibility occurred."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DecisionInvariantError(message)


# ---------------------------------------------------------------------------
# Vocabulary, sets and thresholds, all from the transcription
# ---------------------------------------------------------------------------

_hypotheses = REGISTRATION["hypotheses"]
STATUSES: tuple[str, ...] = tuple(_hypotheses["status_vocabulary"])
SUPPORTED, REFUTED, NEITHER = STATUSES
NOT_EVALUABLE: str = _hypotheses["extra_status"]["H8-REPEAT"][0]
NOT_INTERPRETABLE: str = _hypotheses["extra_status"]["H8-ADAPT"][1]
REPEAT_STATUSES: tuple[str, ...] = (*STATUSES, NOT_EVALUABLE)
PASS, FAIL = "PASS", "FAIL"
GATE_STATUSES: tuple[str, ...] = (PASS, FAIL)

_population = REGISTRATION["population"]
MEMBERS: tuple[str, ...] = tuple(_population["order"])
PI: tuple[str, ...] = tuple(_population["sets"]["pi"])
PI_F: tuple[str, ...] = tuple(_population["sets"]["pi_f"])
A8: tuple[str, ...] = tuple(_population["sets"]["a8"])
PHASE_SENSITIVE: tuple[str, ...] = tuple(_population["sets"]["phase_sensitive"])
PARAMETERS: Mapping[str, Mapping[str, Any]] = _population["members"]
ACQUIRE: Mapping[str, str] = MappingProxyType({m: PARAMETERS[m]["acquire"] for m in MEMBERS})
ATTACKERS: tuple[str, ...] = tuple(REGISTRATION["definitions"]["FL(a, d)"]["attackers"])
DEFENDERS: tuple[str, ...] = tuple(REGISTRATION["definitions"]["FL(a, d)"]["defenders"])

_thresholds = REGISTRATION["thresholds"]
_boot = REGISTRATION["operationalizations"]["O-BOOT"]
RESAMPLES: int = _thresholds["resamples"]
STABILITY: Fraction = Fraction(_thresholds["stability"])
STABILITY_COUNT: int = _thresholds["stability_count"]
EPSILON: Fraction = Fraction(_thresholds["epsilon"])
SEED_COUNT: int = _boot["draws"]
BOOTSTRAP_SEED: int = _boot["rng_seed"]
FL_SUPPORTED: Fraction = Fraction(_thresholds["fl_supported_min"])
FL_REFUTED: Fraction = Fraction(_thresholds["fl_refuted_max"])
TAX_KEEP: Fraction = Fraction(_thresholds["tax_keep_min"])
TAX_REFUTE: Fraction = Fraction(_thresholds["tax_refute_max"])
NEUTRAL_SDOM_LT: Fraction = Fraction(_thresholds["neutral_sdom_lt"])
NEUTRAL_ABS_GSB_LE: Fraction = Fraction(_thresholds["neutral_abs_gsb_le"])
QUANTILES: tuple[str, ...] = tuple(REGISTRATION["seat_criterion"]["reported"]["quantiles"]["q"])

_require(STATUSES == ("SUPPORTED", "REFUTED", "NEITHER"), f"status vocabulary {STATUSES}")
_require(STABILITY_COUNT == STABILITY * RESAMPLES, "the stability count is not 9/10 of the resamples")


# ---------------------------------------------------------------------------
# O-BOOT
# ---------------------------------------------------------------------------


def resample_positions(seed_count: int = SEED_COUNT, *, resamples: int = RESAMPLES,
                       seed: int = BOOTSTRAP_SEED) -> tuple[tuple[int, ...], ...]:
    """The O-BOOT draws: E6's ``payoff.resample_positions`` convention exactly (§4)."""
    rng = random.Random(seed)
    return tuple(tuple(rng.randrange(seed_count) for _ in range(seed_count)) for _ in range(resamples))


#: The 1,000 registered draws. Every stability in §5 to §6 uses exactly these.
DRAWS: tuple[tuple[int, ...], ...] = resample_positions()


def _check_count(count: int, resamples: int) -> None:
    _require(resamples == RESAMPLES, f"{resamples} resamples, not the registered {RESAMPLES}")
    _require(isinstance(count, int) and not isinstance(count, bool) and 0 <= count <= resamples,
             f"a stability count must be an integer in [0, {resamples}], not {count!r}")


def stable(count: int, resamples: int = RESAMPLES) -> bool:
    """stab(P) >= 9/10: P holds in at least 900 of the 1,000 registered resamples."""
    _check_count(count, resamples)
    return Fraction(count, resamples) >= STABILITY


def stability_count(predicate: Callable[[tuple[int, ...]], bool],
                    draws: Sequence[tuple[int, ...]] = DRAWS) -> int:
    """The number of registered draws in which ``predicate`` holds."""
    _require(len(draws) == RESAMPLES, f"{len(draws)} draws, not the registered {RESAMPLES}")
    return sum(1 for positions in draws if predicate(positions))


def quantile(values: Sequence[Fraction], q: str | Fraction | float) -> Fraction:
    """The registered quantile rule, ``sorted(xs)[int(q * (n - 1) + 0.5)]`` (§6.2)."""
    _require(len(values) == RESAMPLES, f"{len(values)} resampled values, not {RESAMPLES}")
    return sorted(values)[int(float(Fraction(q)) * (len(values) - 1) + 0.5)]


# ---------------------------------------------------------------------------
# Hypothesis statuses
# ---------------------------------------------------------------------------


def _check_status(name: str, value: object, allowed: Sequence[str]) -> None:
    _require(value in allowed, f"{name} status {value!r} is outside {list(allowed)}")


def bootstrap_status(point_for: bool, count_for: int, point_against: bool, count_against: int) -> str:
    """SUPPORTED iff P at the point and stab(P) >= 9/10; REFUTED iff Q likewise; else NEITHER.

    P and Q are the registered supporting and refuting predicates. They are
    mutually exclusive at the point estimate by construction; both holding is
    an invariant violation.
    """
    _check_count(count_for, RESAMPLES)
    _check_count(count_against, RESAMPLES)
    _require(not (point_for and point_against), "both the supporting and the refuting predicate hold at the point")
    if point_for and stable(count_for):
        return SUPPORTED
    if point_against and stable(count_against):
        return REFUTED
    return NEITHER


def complement_status(point: bool, count: int) -> str:
    """For H8-SUB, H8-PAR and H8-CHANNEL, whose refuting predicate is "not P"."""
    _check_count(count, RESAMPLES)
    return bootstrap_status(point, count, not point, RESAMPLES - count)


def repeat_status(census: Sequence[str], point_for: bool | None = None, count_for: int | None = None,
                  point_against: bool | None = None, count_against: int | None = None) -> str:
    """H8-REPEAT: NOT EVALUABLE if and only if the census is empty, else bootstrapped."""
    if not census:
        _require(point_for is None and count_for is None and point_against is None and count_against is None,
                 "H8-REPEAT has evidence but the census is empty")
        return NOT_EVALUABLE
    _require(point_for is not None and count_for is not None and point_against is not None
             and count_against is not None, "H8-REPEAT lacks evidence for a non-empty census")
    assert point_for is not None and count_for is not None and point_against is not None and count_against is not None
    _require(set(census) <= set(PI), f"census {list(census)} is not within Pi")
    return bootstrap_status(point_for, count_for, point_against, count_against)


def fl_status(fl: Mapping[tuple[str, str], Fraction]) -> str:
    """H8-FL, over the registered attackers and defenders (no bootstrap)."""
    _require(set(fl) == {(a, d) for a in ATTACKERS for d in DEFENDERS}, "FL is not over attackers x defenders")
    _require(all(0 <= value <= 1 for value in fl.values()), "an FL share lies outside [0, 1]")
    worst = [min(fl[(a, d)] for d in DEFENDERS) for a in ATTACKERS]
    supported = any(value >= FL_SUPPORTED for value in worst)
    refuted = all(value <= FL_REFUTED for value in worst)
    _require(not (supported and refuted), "H8-FL is both SUPPORTED and REFUTED")
    return SUPPORTED if supported else REFUTED if refuted else NEITHER


def tax_status(a: Fraction, b: Fraction | None) -> str:
    """H8-TAX, with B over exactly the cells A counts. B is None if and only if A = 0."""
    _require(0 <= a <= 1, f"A = {a} lies outside [0, 1]")
    _require((b is None) == (a == 0), "B must be undefined exactly when A counts no cells")
    if a <= TAX_REFUTE:
        return REFUTED
    assert b is not None
    _require(0 <= b <= 1, f"B = {b} lies outside [0, 1]")
    return SUPPORTED if a >= TAX_KEEP and b >= TAX_KEEP else NEITHER


# ---------------------------------------------------------------------------
# The seat criterion (§6.2)
# ---------------------------------------------------------------------------

SeatUnit = tuple[str, ...]


def seat_units(members: Sequence[str] = MEMBERS) -> tuple[SeatUnit, ...]:
    """The 66 units: the 55 F1 pairings ("pairing", a, b), then the 11 F2 mirrors ("mirror", m)."""
    return (*(("pairing", a, b) for a, b in combinations(members, 2)), *(("mirror", m) for m in members))


SEAT_UNITS: tuple[SeatUnit, ...] = seat_units()


def neutral(sdom: Fraction, gsb: Fraction) -> bool:
    """O-NEUTRAL: SDom < 9/10 and |GSB| <= 1/10."""
    return sdom < NEUTRAL_SDOM_LT and abs(gsb) <= NEUTRAL_ABS_GSB_LE


def delta_g(control_gsb: Mapping[SeatUnit, Fraction], treatment_gsb: Mapping[SeatUnit, Fraction],
            units: Sequence[SeatUnit] = SEAT_UNITS) -> Fraction:
    """ΔG: the mean over the units of |GSB_treatment(u)| - |GSB_control(u)|."""
    _require(len(units) > 0, "ΔG over no units")
    return sum((abs(treatment_gsb[u]) - abs(control_gsb[u]) for u in units), Fraction(0)) / len(units)


#: (condition, unit, seed positions or None for the point estimate) -> (SDom, GSB)
SeatSource = Callable[[str, SeatUnit, tuple[int, ...] | None], tuple[Fraction, Fraction]]


@dataclass(frozen=True)
class SeatReading:
    """PF8-4 (the unit layer) and H8-SEAT (the family layer) for one arm."""

    unit_stability: Mapping[SeatUnit, int]
    flagged: tuple[SeatUnit, ...]
    pf8_4_raised: bool
    delta_g: Fraction
    delta_g_positive_count: int
    delta_g_nonpositive_count: int
    h8_seat: str
    quantiles: Mapping[str, Fraction]


def seat_layers(source: SeatSource, *, control: str, treatment: str, units: Sequence[SeatUnit] = SEAT_UNITS,
                draws: Sequence[tuple[int, ...]] = DRAWS) -> SeatReading:
    """Both seat layers. Within every draw, one seed-position tuple recomputes control and treatment."""
    _require(len(draws) == RESAMPLES, f"{len(draws)} draws, not the registered {RESAMPLES}")
    point_c = {u: source(control, u, None) for u in units}
    point_t = {u: source(treatment, u, None) for u in units}
    candidates = [u for u in units if neutral(*point_c[u]) and not neutral(*point_t[u])]
    transitions = dict.fromkeys(candidates, 0)
    samples: list[Fraction] = []
    for positions in draws:
        drawn_c = {u: source(control, u, positions) for u in units}
        drawn_t = {u: source(treatment, u, positions) for u in units}
        for u in candidates:
            transitions[u] += neutral(*drawn_c[u]) and not neutral(*drawn_t[u])
        samples.append(delta_g({u: drawn_c[u][1] for u in units}, {u: drawn_t[u][1] for u in units}, units))
    flagged = tuple(u for u in candidates if stable(transitions[u]))
    point = delta_g({u: point_c[u][1] for u in units}, {u: point_t[u][1] for u in units}, units)
    positive = sum(1 for value in samples if value > 0)
    nonpositive = RESAMPLES - positive
    return SeatReading(
        unit_stability=MappingProxyType(dict(transitions)),
        flagged=flagged,
        pf8_4_raised=bool(flagged),
        delta_g=point,
        delta_g_positive_count=positive,
        delta_g_nonpositive_count=nonpositive,
        h8_seat=bootstrap_status(point > 0, positive, point <= 0, nonpositive),
        quantiles=MappingProxyType({q: quantile(samples, q) for q in QUANTILES}),
    )


# ---------------------------------------------------------------------------
# §7.1: the structural reading
# ---------------------------------------------------------------------------

_interpretation = REGISTRATION["interpretation"]


@dataclass(frozen=True)
class Row:
    row_id: str
    e8_d: str
    pairs: frozenset[tuple[str, str]]
    reading: str


ALL_PAIRS: frozenset[tuple[str, str]] = frozenset((s, p) for s in STATUSES for p in STATUSES)
ROWS: tuple[Row, ...] = tuple(
    Row(row["id"], row["e8_d"],
        ALL_PAIRS if row["combinations"] == "all nine" else frozenset(tuple(pair) for pair in row["combinations"]),
        row["reading"]["text"])
    for row in _interpretation["rows"])
ROW_IDS: tuple[str, ...] = tuple(row.row_id for row in ROWS)


def row_for(e8_d: str, h8_sub: str, h8_par: str) -> Row:
    """The one registered row for (E8-D, H8-SUB, H8-PAR); none or two fails closed."""
    _check_status("E8-D", e8_d, GATE_STATUSES)
    _check_status("H8-SUB", h8_sub, STATUSES)
    _check_status("H8-PAR", h8_par, STATUSES)
    matches = [row for row in ROWS if row.e8_d == e8_d and (h8_sub, h8_par) in row.pairs]
    _require(len(matches) == 1, f"({e8_d}, {h8_sub}, {h8_par}) maps to {[row.row_id for row in matches]}")
    return matches[0]


# ---------------------------------------------------------------------------
# §8's labels (used by §7.2's H8-CHANNEL qualifier and by KC8-1 and KC8-6)
# ---------------------------------------------------------------------------

_kills = REGISTRATION["kill_criteria"]
KILL_CRITERIA: tuple[str, ...] = tuple(k for k in _kills if k.startswith("KC8-"))


@dataclass(frozen=True)
class Label:
    label: str
    members: tuple[str, ...]
    names_members: bool


def _registered_order(members: Collection[str]) -> tuple[str, ...]:
    return tuple(m for m in MEMBERS if m in members)


def _label(criterion: str, rules: Sequence[tuple[str, Callable[[frozenset[str]], bool]]],
           universal: Collection[str], within: Sequence[str]) -> Label:
    registered = _kills[criterion]["label"]["rules"]
    _require([rule["label"] for rule in registered] == [name for name, _ in rules],
             f"{criterion}'s label order differs from the transcription")
    members = frozenset(universal)
    _require(bool(members), f"{criterion} fires only with at least one universal member")
    _require(members <= set(within), f"{criterion}'s universal members {sorted(members)} are outside {list(within)}")
    for rule, (name, predicate) in zip(registered, rules, strict=True):
        if predicate(members):
            return Label(name, _registered_order(members), bool(rule.get("names_members", False)))
    raise DecisionInvariantError(f"{criterion}'s labels do not cover {sorted(members)}")


def kc8_1_label(universal: Collection[str]) -> Label:
    """Search race, greed dominance, or other dominance naming the members (over Π_F)."""
    return _label("KC8-1", (
        ("search race", lambda s: all(ACQUIRE[m] != "none" for m in s)),
        ("greed dominance", lambda s: "GREED8" in s),
        ("other dominance", lambda s: True),
    ), universal, PI_F)


def kc8_6_label(universal_a8: Collection[str]) -> Label:
    """Channel race, information dominated, or mixed dominance naming every one (over A8)."""
    return _label("KC8-6", (
        ("channel race", lambda s: all(ACQUIRE[m] != "none" for m in s)),
        ("information dominated", lambda s: s == {"LURK8"}),
        ("mixed dominance", lambda s: True),
    ), universal_a8, A8)


# ---------------------------------------------------------------------------
# §7.1 to §7.2: qualifiers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Qualifier:
    hypothesis: str
    status: str
    text: str
    naming: str | None = None
    label: Label | None = None


def no_choice_qualifier(h8_tax: str) -> str:
    """R8-NO-CHOICE's H8-TAX qualifier text."""
    _check_status("H8-TAX", h8_tax, STATUSES)
    return str(_interpretation["no_choice_tax_qualifier"][h8_tax]["text"])


def qualifiers(row: Row, *, h8_channel: str, h8_less: str, h8_tax: str,
               universal_a8: Collection[str] = ()) -> tuple[Qualifier, ...]:
    """The registered qualifiers of a row: none on STOP; H8-CHANNEL and H8-LESS on every PASS row,
    plus H8-TAX on R8-NO-CHOICE."""
    _check_status("H8-CHANNEL", h8_channel, STATUSES)
    _check_status("H8-LESS", h8_less, STATUSES)
    _check_status("H8-TAX", h8_tax, STATUSES)
    if row.e8_d != PASS:
        return ()
    registered = _interpretation["qualifiers"]
    channel = registered["H8-CHANNEL"]
    if h8_channel == REFUTED:
        channel_qualifier = Qualifier("H8-CHANNEL", REFUTED, channel[REFUTED]["text"],
                                      channel["REFUTED_naming"]["text"], kc8_6_label(universal_a8))
    else:
        _require(not universal_a8 if h8_channel == SUPPORTED else True,
                 "H8-CHANNEL is SUPPORTED, but an A8 member is universal at the point")
        channel_qualifier = Qualifier("H8-CHANNEL", h8_channel, channel[h8_channel]["text"])
    out = [channel_qualifier, Qualifier("H8-LESS", h8_less, registered["H8-LESS"][h8_less]["text"])]
    if row.row_id == "R8-NO-CHOICE":
        out.append(Qualifier("H8-TAX", h8_tax, no_choice_qualifier(h8_tax)))
    return tuple(out)


# ---------------------------------------------------------------------------
# §7.3: the repeated-choice and requirement-C readings
# ---------------------------------------------------------------------------

SCOPE_SENTENCE: str = REGISTRATION["research_question"]["scope_sentence"]["text"]


def _census_text(census: Sequence[str]) -> str:
    return "{" + ", ".join(_registered_order(census)) + "}"


@dataclass(frozen=True)
class Reading:
    status: str
    text: str
    scope_sentence: str | None


def repeat_reading(h8_repeat: str, census: Sequence[str]) -> Reading:
    """H8-REPEAT's registered reading, with 𝒞 named, carrying §1's scope sentence verbatim."""
    _check_status("H8-REPEAT", h8_repeat, REPEAT_STATUSES)
    _require((h8_repeat == NOT_EVALUABLE) == (not census), "H8-REPEAT is NOT EVALUABLE if and only if 𝒞 is empty")
    text = str(_interpretation["repeat_readings"][h8_repeat]["text"]).replace("{𝒞}", _census_text(census))
    return Reading(h8_repeat, text, SCOPE_SENTENCE)


def static_set(census: Collection[str]) -> tuple[str, ...]:
    """S: the members of Π_F outside 𝒞 whose anchors do not move after being located (``evade`` off)."""
    rule = _interpretation["adapt"]["static_set_S"]["rule"]
    return tuple(m for m in PI_F if m not in census and PARAMETERS[m][rule["parameter"]] == rule["equals"])


def allocation_check(verification: Mapping[str, Fraction], census: Sequence[str]) -> bool:
    """min over Y in 𝒞 of V(Y) > max over j in S of V(j)."""
    _require(bool(census), "the allocation-variation check needs a non-empty census")
    static = static_set(census)
    _require(set(census) | set(static) <= set(verification), "V is missing a census or static opponent")
    return min(verification[y] for y in census) > max(verification[j] for j in static)


@dataclass(frozen=True)
class AdaptReading:
    interpretable: bool | None
    status: str
    text: str
    note: str | None


def adapt_reading(*, h8_sub: str, h8_repeat: str, check: bool | None, h8_adapt: str | None,
                  census: Sequence[str]) -> AdaptReading:
    """H8-ADAPT's interpretability and reading (§7.3). A status recorded while not
    interpretable, or any other inconsistent record, fails closed."""
    _check_status("H8-SUB", h8_sub, STATUSES)
    _check_status("H8-REPEAT", h8_repeat, REPEAT_STATUSES)
    readings = _interpretation["adapt"]["readings"]
    if h8_repeat == NOT_EVALUABLE:
        _require(not census, "H8-REPEAT is NOT EVALUABLE but 𝒞 is not empty")
        _require(check is None and h8_adapt is None, "no check or H8-ADAPT status exists when 𝒞 is empty")
        return AdaptReading(None, NOT_EVALUABLE, readings[NOT_EVALUABLE]["text"], None)
    _require(bool(census), "𝒞 is empty but H8-REPEAT has a status")
    _require(isinstance(check, bool), "the allocation-variation check is required when 𝒞 is not empty")
    preconditions = _interpretation["adapt"]["preconditions"]
    interpretable = (h8_sub == preconditions["H8-SUB"] and h8_repeat == preconditions["H8-REPEAT"]
                     and check is preconditions["allocation_variation_check"])
    if not interpretable:
        _require(h8_adapt is None, "a status is recorded for H8-ADAPT while it is not interpretable")
        return AdaptReading(False, NOT_INTERPRETABLE, readings[NOT_INTERPRETABLE]["text"],
                            _interpretation["adapt"]["not_interpretable_note"]["text"])
    _check_status("H8-ADAPT", h8_adapt, STATUSES)
    assert h8_adapt is not None
    return AdaptReading(True, h8_adapt, str(readings[h8_adapt]["text"]).replace("{𝒞}", _census_text(census)), None)


# ---------------------------------------------------------------------------
# §7.4: the answer to the research question
# ---------------------------------------------------------------------------

_core = _interpretation["core_answer"]
CORE_ORDER: tuple[str, ...] = tuple(item["outcome"] for item in _core["order"])
NOT_EVALUABLE_ANSWER, NO, YES, INDETERMINATE = CORE_ORDER


@dataclass(frozen=True)
class CoreAnswer:
    outcome: str
    scope_sentence: str | None


def core_answer(*, e8_d: str, h8_sub: str, h8_channel: str, h8_repeat: str) -> CoreAnswer:
    """The four outcomes, applied in the registered order; exactly one applies."""
    _check_status("E8-D", e8_d, GATE_STATUSES)
    _check_status("H8-SUB", h8_sub, STATUSES)
    _check_status("H8-CHANNEL", h8_channel, STATUSES)
    _check_status("H8-REPEAT", h8_repeat, REPEAT_STATUSES)
    components = (h8_sub, h8_channel, h8_repeat)
    refuted = REFUTED in components
    rules: tuple[tuple[str, bool], ...] = (
        (NOT_EVALUABLE_ANSWER, e8_d == FAIL or (not refuted and h8_repeat == NOT_EVALUABLE)),
        (NO, e8_d == PASS and refuted),
        (YES, all(status == SUPPORTED for status in components)),
        (INDETERMINATE, not refuted and NEITHER in components),
    )
    _require(tuple(name for name, _ in rules) == CORE_ORDER, "the core-answer order differs from the transcription")
    for name, holds in rules:
        if holds:
            return CoreAnswer(name, SCOPE_SENTENCE if name == YES else None)
    raise DecisionInvariantError(f"no core answer applies to {(e8_d, *components)}")


# ---------------------------------------------------------------------------
# §8: kill criteria and disposition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Kill:
    fires: bool
    label: Label | None = None
    detail: Mapping[str, Any] | None = None


def kill_criteria(*, h8_sub: str, universal: Collection[str], greed_universal_count: int,
                  pf8_1: bool, pf8_2: bool, h8_fl: str, pf8_4: bool, h8_seat: str,
                  h8_channel: str, universal_a8: Collection[str],
                  seat_detail: Mapping[str, Any] | None = None) -> Mapping[str, Kill]:
    """KC8-1 to KC8-6 on the primary arm. ``universal`` is Π_F's universal set and
    ``universal_a8`` A8's, both at the point estimate."""
    for name, value in (("H8-SUB", h8_sub), ("H8-FL", h8_fl), ("H8-SEAT", h8_seat), ("H8-CHANNEL", h8_channel)):
        _check_status(name, value, STATUSES)
    universal, universal_a8 = frozenset(universal), frozenset(universal_a8)
    _require(universal <= set(PI_F) and universal_a8 <= set(A8), "a universal set lies outside its candidates")
    _require(not (h8_sub == SUPPORTED and universal), "H8-SUB is SUPPORTED (P_none) but a member is universal")
    _require(not (h8_sub == REFUTED and not universal), "H8-SUB is REFUTED but no member is universal")
    _require(not (h8_channel == SUPPORTED and universal_a8), "H8-CHANNEL is SUPPORTED (Q_none) but an A8 member is universal")
    _require(not (h8_channel == REFUTED and not universal_a8), "H8-CHANNEL is REFUTED but no A8 member is universal")
    greed_point = "GREED8" in universal
    kills = {
        "KC8-1": Kill(h8_sub == REFUTED, kc8_1_label(universal) if h8_sub == REFUTED else None),
        "KC8-2": Kill(greed_point and stable(greed_universal_count),
                      detail=MappingProxyType({"greed_universal": greed_point, "count": greed_universal_count})),
        "KC8-3": Kill(pf8_1 or pf8_2),
        "KC8-4": Kill(h8_fl == SUPPORTED),
        "KC8-5": Kill(pf8_4 or h8_seat == SUPPORTED, detail=MappingProxyType({
            "layers": tuple(layer for layer, raised in (("unit", pf8_4), ("family", h8_seat == SUPPORTED)) if raised),
            **dict(seat_detail or {})})),
        "KC8-6": Kill(h8_channel == REFUTED, kc8_6_label(universal_a8) if h8_channel == REFUTED else None),
    }
    _require(tuple(kills) == KILL_CRITERIA, "the kill criteria differ from the transcription")
    return MappingProxyType(kills)


_disposition = REGISTRATION["disposition"]["order"]
DISPOSITIONS: tuple[str, ...] = tuple(item["outcome"] for item in _disposition)
VOID, REJECT, CANDIDATE, NOT_ESTABLISHED = DISPOSITIONS


def disposition(*, e8_d: str, fired: Collection[str], row: Row, h8_less: str, core: CoreAnswer) -> str:
    """VOID, then REJECT, then CANDIDATE, else NOT ESTABLISHED (§8, exhaustive)."""
    _check_status("E8-D", e8_d, GATE_STATUSES)
    _check_status("H8-LESS", h8_less, STATUSES)
    _require(set(fired) <= set(KILL_CRITERIA), f"unknown kill criteria {sorted(set(fired) - set(KILL_CRITERIA))}")
    _require(row in ROWS and core.outcome in CORE_ORDER, "an unregistered row or core answer")
    _require((e8_d == FAIL) == (row.row_id == "STOP"), "E8-D and the row disagree")
    _require(e8_d == PASS or core.outcome == NOT_EVALUABLE_ANSWER, "a failed gate must leave the question NOT EVALUABLE")
    candidate = _disposition[2]["if"]
    rules: tuple[tuple[str, bool], ...] = (
        (VOID, e8_d == FAIL),
        (REJECT, bool(fired)),
        (CANDIDATE, row.row_id in candidate["row_in"] and h8_less == candidate["H8-LESS"]
         and core.outcome == candidate["core_answer"]),
        (NOT_ESTABLISHED, True),
    )
    return next(name for name, holds in rules if holds)


# ---------------------------------------------------------------------------
# §6.6: the companion reading
# ---------------------------------------------------------------------------

COMPANION_HYPOTHESES: tuple[str, ...] = tuple(
    item for item in REGISTRATION["companion"]["agrees_when_same_status"] if item.startswith("H8-"))


@dataclass(frozen=True)
class CompanionReading:
    agrees: bool
    differences: tuple[str, ...]


def companion_reading(primary: Mapping[str, str], companion: Mapping[str, str],
                      primary_kills: Mapping[str, bool], companion_kills: Mapping[str, bool]) -> CompanionReading:
    """"agrees" when the registered hypotheses and every kill criterion match, else what differs."""
    _require(set(COMPANION_HYPOTHESES) <= set(primary) and set(COMPANION_HYPOTHESES) <= set(companion),
             "a compared hypothesis is missing")
    _require(set(primary_kills) == set(KILL_CRITERIA) == set(companion_kills), "a kill criterion is missing")
    differences = [f"{h}: {primary[h]} (primary) vs {companion[h]} (companion)"
                   for h in COMPANION_HYPOTHESES if primary[h] != companion[h]]
    differences += [f"{k}: {'fires' if primary_kills[k] else 'does not fire'} (primary) vs "
                    f"{'fires' if companion_kills[k] else 'does not fire'} (companion)"
                    for k in KILL_CRITERIA if primary_kills[k] != companion_kills[k]]
    return CompanionReading(not differences, tuple(differences))


# ---------------------------------------------------------------------------
# Structure: the census, D8-3, CQ8-4
# ---------------------------------------------------------------------------


def census(parameters: Mapping[str, Mapping[str, Any]] = PARAMETERS) -> tuple[str, ...]:
    """§3.5's static procedure: every opponent meeting E-1, E-2 and E-3 (no outcome enters it).

    At the family freeze it is applied to the frozen packages' parameters.
    """
    criteria = {c["id"]: c["decided_by"] for c in REGISTRATION["census"]["criteria"]}
    _require(tuple(criteria) == ("E-1", "E-2", "E-3"), "the census criteria differ from the transcription")
    _require(set(parameters) == set(MEMBERS), "the census needs every member's parameters")
    e1, e2, e3 = criteria["E-1"], criteria["E-2"], criteria["E-3"]
    e2_holds = int(e2["evasion_min"]) >= 1
    e3_holds = (all(parameters[m]["posture"] == e3["their_posture"] for m in e3["disrupting_attackers"])
                and int(e3["hit_cost_min_offers_primary"]) > int(e3["reacquisition_worst_case_sense"]))
    return tuple(m for m in MEMBERS if parameters[m][e1["parameter"]] == e1["equals"] and e2_holds and e3_holds)


@dataclass(frozen=True)
class MatchedPair:
    """D8-3: the LURK8 cell and the GREED8 cell against one opponent, in one seat, at one seed."""

    opponent: str
    seat: str
    seed_position: int


def d8_3_matched_pairs() -> tuple[MatchedPair, ...]:
    """Every matched pair of one T-condition: 9 opponents x 2 seats x 32 seeds."""
    clause = next(c for c in REGISTRATION["gates"]["E8-D"]["clauses"] if c["id"] == "D8-3")
    pairs = tuple(MatchedPair(opponent, seat, position) for opponent in clause["opponents"]
                  for seat in ("A", "B") for position in range(clause["seeds"]))
    _require(len(pairs) == clause["matched_pairs_per_condition"], "D8-3's matched-pair count")
    return pairs


def control_against_control(*, h8_sub: str, h8_par: str, h8_tax: str, a: Fraction, b: Fraction | None,
                            pf8_raised: Mapping[str, bool], flagged_units: int, h8_seat: str,
                            delta_g_point: Fraction, delta_g_draws: Sequence[Fraction], row: Row) -> Mapping[str, bool]:
    """CQ8-4, with C8 in the treatment slot: every registered expectation, and PASS only if all hold."""
    expects = REGISTRATION["gates"]["CQ8"]["checks"][3]["expects"]
    checks = {
        "H8-SUB = H8-PAR": h8_sub == h8_par,
        "H8-TAX SUPPORTED": h8_tax == expects["H8-TAX"],
        "A = B = 1": a == Fraction(expects["A"]) and b == Fraction(expects["B"]),
        "PF8-1 to PF8-4 not raised": set(pf8_raised) == {"PF8-1", "PF8-2", "PF8-3", "PF8-4"}
        and not any(pf8_raised.values()),
        "no unit flagged": flagged_units == expects["flagged_units"],
        "H8-SEAT REFUTED": h8_seat == expects["H8-SEAT"],
        "ΔG = 0 at the point and in every resample": delta_g_point == Fraction(expects["delta_g_point"])
        and len(delta_g_draws) == RESAMPLES and all(v == Fraction(expects["delta_g_every_resample"]) for v in delta_g_draws),
        "the row the equality implies": h8_sub == h8_par and row == row_for(PASS, h8_sub, h8_par),
    }
    return MappingProxyType({**checks, "PASS": all(checks.values())})
