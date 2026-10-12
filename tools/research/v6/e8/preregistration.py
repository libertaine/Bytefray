"""Loader for the frozen E8 pre-registration transcription (``preregistration.json``).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md, revision 5
(registered at ``59190b7``), is the authoritative wording. The JSON transcribes
it without reinterpretation. Loading fails closed unless all of these hold:

* the JSON's digest is ``PREREGISTRATION_SHA256``, so the transcription is the
  frozen one;
* the markdown's digest is the one the JSON records, so the wording it
  transcribes is the registered revision;
* the JSON is internally consistent (``internal_problems``): its sets, counts,
  thresholds and arithmetic agree with one another and recompute;
* the JSON agrees with the markdown (``markdown_problems``): every value under
  a key named ``text`` occurs verbatim in the markdown, with only emphasis
  removed, and every registered table and set is equal to the markdown's.

The loaded registration is deeply immutable: mappings are read-only views and
sequences are tuples, so no registered set can be changed after the freeze.
Digests normalize CRLF to LF, the E6 convention.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator, Mapping, Sequence
from fractions import Fraction
from itertools import product
from pathlib import Path
from types import MappingProxyType
from typing import Any

PREREGISTRATION_PATH = Path(__file__).with_name("preregistration.json")
PREREGISTRATION_SHA256 = "6d4ffb4b43bfadebdad9aea1481a52c5ea119ed9c05aae21337931d2c84c7a5b"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "bytefray.v6.e8.preregistration"


class PreregistrationError(RuntimeError):
    """The E8 transcription is not the frozen one, or disagrees with itself or the markdown."""


# ---------------------------------------------------------------------------
# Digests, parsing and immutability
# ---------------------------------------------------------------------------


def file_digest(path: Path) -> str:
    """SHA-256 of a file's bytes with CRLF normalized to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def preregistration_digest(path: Path = PREREGISTRATION_PATH) -> str:
    return file_digest(path)


def markdown_path(data: Mapping[str, Any]) -> Path:
    return REPOSITORY_ROOT / str(data["authority"]["document"])


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    duplicated = sorted({key for key in keys if keys.count(key) > 1})
    if duplicated:
        raise PreregistrationError(f"duplicate JSON keys {duplicated}")
    return dict(pairs)


def parse(text: str) -> dict[str, Any]:
    """Parse the transcription, refusing duplicate keys (which JSON would silently collapse)."""
    parsed: dict[str, Any] = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    return parsed


def freeze(value: Any) -> Any:
    """A deeply immutable copy: mappings become read-only views, lists become tuples."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


# ---------------------------------------------------------------------------
# Markdown normalization
# ---------------------------------------------------------------------------

_CODE_SPAN = re.compile(r"(`[^`]*`)")
_PIPE = re.compile(r"(?<!\\)\|")
_SEPARATOR = re.compile(r"^\|[-| :]+\|$")


def plain(text: str) -> str:
    """Registered wording with markdown emphasis removed and whitespace collapsed.

    Outside code spans, ``**`` and ``*`` (emphasis markers) are removed. Everywhere,
    an escaped table pipe becomes a pipe. Runs of whitespace become one space.
    """
    parts = _CODE_SPAN.split(text)
    kept = [part if index % 2 else part.replace("**", "").replace("*", "") for index, part in enumerate(parts)]
    return " ".join("".join(kept).replace("\\|", "|").split())


def verbatim_texts(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Every (JSON path, text) under a key named ``text``, including each item of a list of texts."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            here = f"{path}/{key}"
            if key == "text":
                if isinstance(item, str):
                    yield here, item
                else:
                    for index, sentence in enumerate(item):
                        yield f"{here}/{index}", sentence
            else:
                yield from verbatim_texts(item, here)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from verbatim_texts(item, f"{path}/{index}")


def tables(markdown: str) -> list[tuple[tuple[str, ...], list[tuple[str, ...]]]]:
    """Every markdown table as (header cells, row cells), each cell in ``plain`` form."""

    def cells(line: str) -> tuple[str, ...]:
        return tuple(plain(cell) for cell in _PIPE.split(line.strip())[1:-1])

    lines = markdown.split("\n")
    found: list[tuple[tuple[str, ...], list[tuple[str, ...]]]] = []
    index = 0
    while index < len(lines):
        if lines[index].startswith("|") and index + 1 < len(lines) and _SEPARATOR.match(lines[index + 1]):
            header = cells(lines[index])
            rows: list[tuple[str, ...]] = []
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].startswith("|"):
                rows.append(cells(lines[cursor]))
                cursor += 1
            found.append((header, rows))
            index = cursor
        else:
            index += 1
    return found


# ---------------------------------------------------------------------------
# Internal consistency
# ---------------------------------------------------------------------------

_STATUSES = ("SUPPORTED", "REFUTED", "NEITHER")


def discovery_arc(data: Mapping[str, Any]) -> tuple[frozenset[int], list[int]]:
    """Appendix A.1, recomputed: the arc's offsets from the own core base, and each window's size."""
    discovery = data["traversal"]["discovery"]
    w = int(data["decisions"]["R-2"]["value"])
    sizes: list[int] = []
    covered: set[int] = set()
    for k in range(int(discovery["k_first"]), int(discovery["k_last"]) + 1):
        center = int(discovery["center_offset"]) + int(discovery["step"]) * k
        window = set(range(center - w, center + w + 1))
        sizes.append(len(window - covered))
        covered |= window
    return frozenset(covered), sizes


def verification_window_worst_case(data: Mapping[str, Any]) -> tuple[int, list[int]]:
    """Appendix A.2, recomputed: the most READs E6's verification window takes to hit a moved anchor's core.

    Also returns the displacements of the core above the anchor for which that worst case occurs.
    """
    a2 = data["arithmetic"]["A.2"]
    order = a2["window_order"]
    first, stride, k_max = int(order["first_offset"]), int(order["stride"]), int(order["k_max"])
    reads = [first] + [first + sign * stride * k for k in range(1, k_max + 1) for sign in (-1, 1)]
    low, high = int(data["decisions"]["R-11"]["m_min"]), int(data["decisions"]["R-11"]["m_max"])
    needed: dict[int, int] = {}
    for m in range(low, high + 1):
        for base in (-m, m):  # the anchor moved up by m (core below it) or down by m (core above it)
            cells = set(range(base, base + int(a2["core_cells"])))
            needed[base] = next(index + 1 for index, read in enumerate(reads) if read in cells)
    worst = max(needed.values())
    return worst, sorted(base for base, count in needed.items() if count == worst and base > 0)


def reacquisition_coverage(data: Mapping[str, Any]) -> tuple[int, list[int]]:
    """Appendix A.3, recomputed: the post-evasion positions, and each window's new coverage."""
    w = int(data["decisions"]["R-2"]["value"])
    low, high = int(data["decisions"]["R-11"]["m_min"]), int(data["decisions"]["R-11"]["m_max"])
    positions = {sign * m for m in range(low, high + 1) for sign in (1, -1)}
    offset = int(data["traversal"]["reacquisition"]["offset_magnitude"])
    covered: set[int] = set()
    new: list[int] = []
    for center in (0, offset, -offset):
        window = {p for p in positions if abs(p - center) <= w}
        new.append(len(window - covered))
        covered |= window
    return len(positions), new


def quantile_index(q: Fraction | float, n: int) -> int:
    """The registered quantile index rule: ``int(q * (n - 1) + 0.5)`` (§6.2)."""
    return int(float(q) * (n - 1) + 0.5)


def static_census(data: Mapping[str, Any]) -> tuple[str, ...]:
    """§3.5's static procedure, applied to the transcribed parameters: E-1, E-2 and E-3 per opponent."""
    members = data["population"]["members"]
    criteria = {criterion["id"]: criterion["decided_by"] for criterion in data["census"]["criteria"]}
    e1 = criteria["E-1"]
    e2 = int(criteria["E-2"]["evasion_min"]) >= 1
    e3 = criteria["E-3"]
    attackers_disrupt = all(members[name]["posture"] == e3["their_posture"] for name in e3["disrupting_attackers"])
    e3_holds = attackers_disrupt and int(e3["hit_cost_min_offers_primary"]) > int(e3["reacquisition_worst_case_sense"])
    return tuple(name for name in data["population"]["order"]
                 if members[name][e1["parameter"]] == e1["equals"] and e2 and e3_holds)


def internal_problems(data: Mapping[str, Any]) -> list[str]:
    """Every place the transcription disagrees with itself (empty when it agrees)."""
    problems: list[str] = []

    def expect(name: str, actual: Any, wanted: Any) -> None:
        if actual != wanted:
            problems.append(f"{name}: {actual!r} != {wanted!r}")

    expect("schema", data.get("schema"), SCHEMA)
    authority = data["authority"]
    expect("revision", authority["revision"], 5)
    expect("document", authority["document"], "docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md")
    expect("document digest form", bool(re.fullmatch(r"[0-9a-f]{64}", authority["document_sha256"])), True)

    population = data["population"]
    order = list(population["order"])
    members = population["members"]
    sets = population["sets"]
    expect("members", list(members), order)
    expect("member count", len(order), data["decisions"]["R-10"]["value"])
    expect("Pi", list(sets["pi"]), order)
    expect("Pi_F", list(sets["pi_f"]), [m for m in order if m != "ADAPT8"])
    for name in sets["a8"]:
        values = members[name]
        expect(f"A8 {name}", (name in sets["pi_f"], values["posture"], values["processes"], values["evade"]),
               (True, "attack", 1, "off"))
    definitions = data["definitions"]
    expect("attackers", list(definitions["FL(a, d)"]["attackers"]),
           [m for m in sets["pi_f"] if members[m]["posture"] == "attack"])
    expect("defenders", list(definitions["FL(a, d)"]["defenders"]),
           [m for m in sets["pi_f"] if members[m]["posture"] == "guard"])
    expect("phase-sensitive stratum", list(data["registered_reporting"]["phase_sensitive_stratum"]["members"]),
           list(sets["phase_sensitive"]))
    for pair in definitions["L8"]["pairs"]:
        expect(f"L8 {pair}", all(m in sets["pi_f"] for m in pair), True)

    clauses = data["gates"]["E8-D"]["clauses"]
    expect("E8-D clause ids", [c["id"] for c in clauses], [f"D8-{n}" for n in range(1, 16)])
    d83 = clauses[2]
    expect("D8-3 opponents", list(d83["opponents"]), [m for m in order if m not in d83["members"]])
    expect("D8-3 matched pairs", d83["matched_pairs_per_condition"],
           len(d83["opponents"]) * d83["orientations"] * d83["seeds"])
    expect("CQ8 ids", [c["id"] for c in data["gates"]["CQ8"]["checks"]], [f"CQ8-{n}" for n in range(1, 6)])
    expect("PF8 ids", list(data["pathology"]["flags"]), [f"PF8-{n}" for n in range(1, 6)])
    expect("KC8 ids", [k for k in data["kill_criteria"] if k.startswith("KC8-")], [f"KC8-{n}" for n in range(1, 7)])
    expect("hypothesis ids", [k for k in data["hypotheses"] if k.startswith("H8-")],
           ["H8-SUB", "H8-PAR", "H8-CHANNEL", "H8-LESS", "H8-REPEAT", "H8-ADAPT", "H8-FL", "H8-TAX", "H8-SEAT"])

    seeds = data["decisions"]["R-7"]["value"]
    fields = data["fields"]
    n = len(order)
    expect("F1 ordered pairs", fields["F1"]["ordered_pairs"], n * (n - 1))
    expect("F1 cells", fields["F1"]["cells_per_condition"], n * (n - 1) * seeds)
    expect("F2 mirrors", fields["F2"]["mirrors"], n)
    expect("F2 cells", fields["F2"]["cells_per_condition"], n * fields["F2"]["orientations"] * seeds)
    expect("cells per condition", fields["cells_per_condition"],
           fields["F1"]["cells_per_condition"] + fields["F2"]["cells_per_condition"])
    expect("condition count", fields["conditions"], len(data["conditions"]))
    expect("cells total", fields["cells_total"], fields["cells_per_condition"] * fields["conditions"])
    for name, value in (("F1 seeds", fields["F1"]["seeds"]), ("F2 seeds", fields["F2"]["seeds"]),
                        ("O-BOOT draws", data["operationalizations"]["O-BOOT"]["draws"]),
                        ("seed count", data["seed_protocol"]["count"]), ("D8-3 seeds", d83["seeds"])):
        expect(name, value, seeds)

    thresholds = data["thresholds"]
    boot = data["operationalizations"]["O-BOOT"]
    expect("epsilon", Fraction(thresholds["epsilon"]), Fraction(data["decisions"]["R-4"]["value"]))
    expect("O-EPS", Fraction(data["operationalizations"]["O-EPS"]["epsilon"]), Fraction(thresholds["epsilon"]))
    expect("stability", Fraction(thresholds["stability"]), Fraction(data["decisions"]["R-5"]["stability"]))
    expect("O-BOOT stability", Fraction(boot["stability_min"]), Fraction(thresholds["stability"]))
    expect("resamples", thresholds["resamples"], data["decisions"]["R-5"]["resamples"])
    expect("O-BOOT resamples", boot["resamples"], thresholds["resamples"])
    expect("stability count", Fraction(thresholds["stability_count"]),
           Fraction(thresholds["stability"]) * thresholds["resamples"])
    expect("O-BOOT stability count", boot["stability_count_min"], thresholds["stability_count"])
    expect("O-BOOT rng", boot["rng"], f"random.Random({boot['rng_seed']})")
    expect("R-5 rng", data["decisions"]["R-5"]["rng"], boot["rng"])
    expect("forced-line tick", thresholds["forced_line_tick_max"], data["decisions"]["R-6"]["value"])
    expect("O-EARLY", data["operationalizations"]["O-EARLY"]["forced_line_tick_max"], thresholds["forced_line_tick_max"])
    expect("k", thresholds["adapt_k"], data["decisions"]["R-8"]["value"])
    expect("adaptive k", data["member_semantics"]["parameters"]["reacquire=adaptive"]["k"], thresholds["adapt_k"])
    expect("O-NEUTRAL SDom", data["operationalizations"]["O-NEUTRAL"]["sdom_lt"], thresholds["neutral_sdom_lt"])
    expect("O-NEUTRAL GSB", data["operationalizations"]["O-NEUTRAL"]["abs_gsb_le"], thresholds["neutral_abs_gsb_le"])
    expect("seat magnitude floor", thresholds["seat_magnitude_floor"], None)
    expect("R-9 floor", data["decisions"]["R-9"]["magnitude_floor"], None)
    expect("rate n_distinct", data["operationalizations"]["O-EVIDENCE"]["rate_min_n_distinct"],
           thresholds["rate_min_n_distinct"])

    w = data["decisions"]["R-2"]["value"]
    for name, value in (("treatment half-width", data["treatment"]["active"]["half_width"]),
                        ("coverage half-width", data["coverage"]["half_width"]),
                        ("D8-1 half-width", clauses[0]["half_width"]),
                        ("D8-15 active window", clauses[14]["active_window"]),
                        ("context window", data["member_semantics"]["parameters"]["condition_detection"]["active"]
                         ["sensing_window"])):
        expect(name, value, w)
    expect("window cells", data["coverage"]["cells"], 2 * w + 1)

    # Revision 4: each E8 trace field's presence, the gate that checks it both ways, and on which conditions.
    presence = data["traces"]["presence"]
    by_id = {clause["id"]: clause for clause in clauses}
    traced = {f["field"] for f in data["traces"]["fields"] if f["surface"] in ("TraceObservationV2", "TraceResultV2", "ResetRecord")}
    expect("presence fields", {row["field"].split(".")[-1] for row in presence["table"]}, traced)
    expect("presence gates", [row["gate"] for row in presence["table"]], ["D8-15", "D8-1", "D8-13"])
    for row in presence["table"]:
        expect(f"{row['gate']} checks presence on every cell",
               str(by_id.get(row["gate"], {}).get("evaluated_on", "")).lower().split("; for presence, ")[-1]
               .removesuffix(" [revision 4]"), "all four conditions")
    window = presence["table"][0]
    expect("presence window", (window["value"], window["absence_read_as"]),
           (w, by_id["D8-15"]["passive_window"]))
    expect("presence conditions", (window["present_under"], window["absent_under"]),
           ([c["id"] for c in data["conditions"] if c["sensing_mode"] == "active"],
            [c["id"] for c in data["conditions"] if c["sensing_mode"] == "passive"]))
    expect("D8-15 presence", (by_id["D8-15"]["active_presence"], by_id["D8-15"]["passive_presence"]),
           ("required", "absent, read as null"))
    expect("a refused SENSE is an explicit null", dict(presence["refused"]),
           {"sensed_anchors": None, "previous_sense_anchors": None})
    expect("refused fact", data["traces"]["facts"]["refused"]["applied_result.sensed_anchors"],
           presence["refused"]["sensed_anchors"])
    expect("delivery obligation", presence["delivery_obligation"]["callbacks_per_sense"], 1)
    expect("presence checked", dict(presence["checked"]), {"both_ways": True, "every_cell": True, "fails_closed": True})
    expect("compatibility gate", presence["compatibility"]["checked_by"], "D8-6")

    # Revision 5: a SENSE record's status mapping, and D8-14's coverage of every other status.
    mapping = data["traces"]["status_mapping"]["rows"]
    facts = data["traces"]["facts"]
    expect("status mapping", [row["status"] for row in mapping],
           ["APPLIED", "REJECTED_OUT_OF_REACH", "REJECTED_INVALID", "any other"])
    expect("the catch-all includes EXCEPTION", "EXCEPTION" in mapping[-1].get("includes", []), True)
    expect("applied status", mapping[0]["status"], facts["applied"]["applied_result.status"])
    expect("the only ordinary refusal", [row["status"] for row in mapping if row["ordinary_refusal"]],
           [facts["refused"]["applied_result.status"]])
    expect("null unless applied", [row["sensed_anchors"] is None for row in mapping], [False, True, True, True])
    expect("a refusal's null", mapping[1]["sensed_anchors"], presence["refused"]["sensed_anchors"])
    expect("D8-14 allowed statuses", list(by_id["D8-14"]["allowed_statuses"]),
           [row["status"] for row in mapping if not row["d8_14_fires"]])
    expect("D8-14 fires on every other status", [row["d8_14_fires"] for row in mapping], [False, False, True, True])
    expect("D8-14 missing status", by_id["D8-14"]["missing_status_fails"], True)

    arc, sizes = discovery_arc(data)
    discovery = data["traversal"]["discovery"]
    expect("discovery windows", len(sizes), discovery["windows"])
    expect("discovery arc", arc, frozenset(range(discovery["arc"]["from_offset"], discovery["arc"]["to_offset"] + 1)))
    expect("arc cells", len(arc), discovery["arc"]["cells"])
    expect("tiling", sizes, [data["coverage"]["cells"]] * discovery["windows"])
    arithmetic = data["arithmetic"]
    expect("A.1 expectation", Fraction(sum(size * (k + 1) for k, size in enumerate(sizes)), len(arc)),
           Fraction(arithmetic["A.1"]["expectation"]))
    expect("A.1 worst case", len(sizes), arithmetic["A.1"]["worst_case"])
    positions, coverage = reacquisition_coverage(data)
    worst, above = verification_window_worst_case(data)
    expect("A.2 worst case", worst, arithmetic["A.2"]["reads_at_most"])
    expect("A.2 worst-case displacements", [above[0], above[-1]] if above else [],
           list(arithmetic["A.2"]["worst_case_core_above_anchor"]))
    expect("A.3 positions", positions, arithmetic["A.3"]["positions"])
    expect("A.3 coverage", coverage, list(arithmetic["A.3"]["window_new_coverage"]))
    expect("A.3 worst case", len([c for c in coverage if c]), arithmetic["A.3"]["worst_case"])
    expect("A.3 windows cover every position", sum(coverage), positions)
    expect("A.3 expectation", Fraction(sum(c * (k + 1) for k, c in enumerate(coverage)), positions),
           Fraction(arithmetic["A.3"]["expectation"]))
    e3 = data["census"]["criteria"][2]["decided_by"]
    expect("E-3 worst case", e3["reacquisition_worst_case_sense"], arithmetic["A.3"]["worst_case"])
    expect("E-3 hit cost", e3["hit_cost_min_offers_primary"], min(arithmetic["A.3"]["hit_cost_offers"]["whole-tick"]))
    companion = data["census"]["economics"]["companion"]
    expect("E-3 fails under the companion",
           companion["hit_cost_offers"] < Fraction(companion["reacquisition_expectation"]), True)
    expect("E-2 evasion minimum", data["census"]["criteria"][1]["decided_by"]["evasion_min"],
           data["decisions"]["R-11"]["m_min"])
    expect("census", list(static_census(data)), list(data["census"]["predicted"]))

    reported = data["seat_criterion"]["reported"]["quantiles"]
    expect("quantile indices", [quantile_index(Fraction(q), reported["n"]) for q in reported["q"]],
           list(reported["indices"]))
    expect("quantile n", reported["n"], thresholds["resamples"])
    units = data["seat_criterion"]["units"]
    expect("seat units", (units["f1_pairings"], units["f2_mirrors"], units["total"]),
           (n * (n - 1) // 2, n, n * (n - 1) // 2 + n))

    rows = data["interpretation"]["rows"]
    seen: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        pairs = list(product(_STATUSES, _STATUSES)) if row["combinations"] == "all nine" else \
            [tuple(pair) for pair in row["combinations"]]
        for sub, par in pairs:
            seen.setdefault((row["e8_d"], sub, par), []).append(row["id"])
    for triple in product(("PASS", "FAIL"), _STATUSES, _STATUSES):
        expect(f"row coverage {triple}", len(seen.get(triple, [])), 1)
    expect("row triples", len(seen), 18)
    expect("core answer order", [item["outcome"] for item in data["interpretation"]["core_answer"]["order"]],
           ["NOT EVALUABLE", "NO", "YES", "INDETERMINATE"])
    expect("core components", sorted(data["interpretation"]["core_answer"]["components"]),
           sorted(data["research_question"]["registered_form"]["conjunction"]))
    expect("disposition order", [item["outcome"] for item in data["disposition"]["order"]],
           ["VOID", "REJECT as a gameplay candidate", "CANDIDATE, for a further design phase", "NOT ESTABLISHED"])
    expect("arms", (list(data["arms"]["primary"]), list(data["arms"]["companion"])),
           ([c["id"] for c in data["conditions"] if c["arm"] == "primary"],
            [c["id"] for c in data["conditions"] if c["arm"] == "companion"]))
    for condition in data["conditions"]:
        if condition["parent"] is not None:
            parent = next(c for c in data["conditions"] if c["id"] == condition["parent"])
            expect(f"{condition['id']} differs from its parent only in sensing_mode",
                   (parent["arm"], parent["disruption"], parent["sensing_mode"], condition["sensing_mode"]),
                   (condition["arm"], condition["disruption"], "passive", "active"))
    return problems


# ---------------------------------------------------------------------------
# Agreement with the markdown
# ---------------------------------------------------------------------------

_QUOTED = re.compile(r'^"([^"]*)"')
_PAIR = re.compile(r"\((\w+), (\w+)\)")


def _braced(markdown: str, anchor: str) -> list[str]:
    """The comma-separated names in the first {...} after ``anchor`` (a missing anchor is reported)."""
    start = markdown.find(anchor)
    if start < 0:
        return [f"<missing anchor {anchor!r}>"]
    open_brace = markdown.index("{", start)
    return [name.strip() for name in markdown[open_brace + 1:markdown.index("}", open_brace)].split(",")]


def _table(found: Sequence[tuple[tuple[str, ...], list[tuple[str, ...]]]], header: tuple[str, ...],
           problems: list[str]) -> list[tuple[str, ...]]:
    matches = [rows for head, rows in found if head == header]
    if len(matches) != 1:
        problems.append(f"markdown table {header!r} found {len(matches)} times")
        return []
    return matches[0]


def _code(cell: str) -> str:
    """The first code span's content in a cell, or the cell itself."""
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else cell


def _quoted(cell: str) -> str:
    match = _QUOTED.match(cell)
    return match.group(1) if match else cell


def markdown_problems(data: Mapping[str, Any], markdown: str) -> list[str]:
    """Every place the transcription and the markdown disagree (empty when they agree)."""
    problems: list[str] = []

    def expect(name: str, actual: Any, wanted: Any) -> None:
        if actual != wanted:
            problems.append(f"{name}: markdown {actual!r} != transcription {wanted!r}")

    source = plain(markdown)
    for path, text in verbatim_texts(data):
        if plain(text) not in source:
            problems.append(f"{path}: not verbatim in the markdown: {text[:80]!r}")
    found = tables(markdown)

    rows = _table(found, ("#", "Boundary", "Where"), problems)
    expect("boundaries", {r[0]: (r[1], r[2].split(", ")) for r in rows},
           {k: (v["text"], list(v["where"])) for k, v in data["boundaries"].items()})

    rows = _table(found, ("#", "Decision", "Drafted value", "Rationale"), problems)
    expect("decision ids", [r[0] for r in rows], list(data["decisions"]))
    for r in rows:
        decision = data["decisions"].get(r[0], {})
        if not r[1].startswith(str(decision.get("decision", "\0"))):
            problems.append(f"{r[0]} decision name {decision.get('decision')!r} is not the markdown's {r[1]!r}")
    values = {r[0]: r[2] for r in rows}
    decisions = data["decisions"]
    for key, value in (("R-2", str(decisions["R-2"]["value"])), ("R-4", decisions["R-4"]["value"]),
                       ("R-5", str(decisions["R-5"]["resamples"])), ("R-5", decisions["R-5"]["stability"]),
                       ("R-6", f"≤ {decisions['R-6']['value']}"), ("R-7", str(decisions["R-7"]["value"])),
                       ("R-8", f"k = {decisions['R-8']['value']}"),
                       ("R-11", f"[{decisions['R-11']['m_min']}, {decisions['R-11']['m_max']}]"),
                       ("R-5", f"`{decisions['R-5']['rng']}`"), ("R-10", "Eleven.")):
        if value not in values.get(key, ""):
            problems.append(f"{key}'s transcribed value {value!r} is not in the markdown's {values.get(key)!r}")

    rows = _table(found, ("Condition", "Ruleset", "Parent", "Only difference"), problems)
    expect("conditions", [(r[0], _code(r[1]), r[1].startswith("provisional"), None if r[2] == "—" else r[2])
                          for r in rows],
           [(c["id"], c["ruleset_id"], c["provisional"], c["parent"]) for c in data["conditions"]])

    rows = _table(found, ("Member", "`acquire`", "`reacquire`", "`posture`", "`evade`", "`processes`", "Role"),
                  problems)
    transcribed: dict[str, dict[str, Any]] = {}
    for r in rows:
        acquire = r[1].split(" (")[0]
        processes = int(r[5].split(" ")[0])
        member: dict[str, Any] = {"acquire": acquire, "reacquire": None if r[2] == "—" else r[2], "posture": r[3],
                                  "evade": r[4], "processes": processes, "role": r[6]}
        if "(" in r[1]:
            member["acquire_process"] = r[1].split("(")[1].rstrip(")")
        if processes == 2:
            member["shares"] = dict(part.split(" ") for part in r[5].split("(")[1].rstrip(")").split(", "))
        transcribed[r[0]] = member
    expect("member order", list(transcribed), list(data["population"]["order"]))
    for name, member in data["population"]["members"].items():
        expect(f"member {name}", transcribed.get(name), {k: v for k, v in member.items() if k != "stress"})

    sets = data["population"]["sets"]
    expect("A8", _braced(markdown, "the frozen acquisition-policy candidate set**, is"), list(sets["a8"]))
    expect("Pi_F rule", "every member except ADAPT8" in source, True)
    expect("attackers", _braced(markdown, "The attackers are the attack-posture members of Π_F:"),
           list(data["definitions"]["FL(a, d)"]["attackers"]))
    expect("defenders", _braced(markdown, "The defenders are"), list(data["definitions"]["FL(a, d)"]["defenders"]))
    expect("L8", [list(pair) for pair in _PAIR.findall(source[source.index("L8 = {"):source.index("}", source.index("L8 = {"))])],
           [list(pair) for pair in data["definitions"]["L8"]["pairs"]])
    expect("phase-sensitive", "(PACED8, EVADE8, ADAPT8, STRESS8)" in source, True)
    expect("phase-sensitive list", ["PACED8", "EVADE8", "ADAPT8", "STRESS8"], list(sets["phase_sensitive"]))
    expect("predicted census", _braced(markdown, "re-derived from §3.1's table under Revisions 2 and 3:"),
           list(data["census"]["predicted"]))
    expect("companion agreement list",
           "when H8-SUB, H8-CHANNEL, H8-LESS, H8-REPEAT, H8-FL and every kill criterion (§8)" in source, True)
    expect("companion agreement", ["H8-SUB", "H8-CHANNEL", "H8-LESS", "H8-REPEAT", "H8-FL", "every kill criterion"],
           list(data["companion"]["agrees_when_same_status"]))
    quantiles = data["seat_criterion"]["reported"]["quantiles"]
    expect("quantile rule", f"`{quantiles['rule']}`" in markdown, True)
    expect("quantile indices", f"indices {quantiles['indices'][0]}, {quantiles['indices'][1]} and "
                               f"{quantiles['indices'][2]}" in source, True)
    expect("O-BOOT draw form", f"`{data['operationalizations']['O-BOOT']['draw_form']}`" in markdown, True)
    expect("D8-3 count", "9 × 2 orientations × 32 seeds = 576 matched pairs" in source, True)
    expect("components", "H8-SUB, H8-CHANNEL and H8-REPEAT" in source, True)

    rows = _table(found, ("Parameter", 'Under `"passive"` (C8, C8L)', 'Under `"active"` (T8, T8L)'), problems)
    keys = []
    for r in rows:
        key = r[0].replace("`", "").replace(" = ", "=").split(" (")[0]
        keys.append("condition_detection" if key == "Condition detection" else key)
    parameters = data["member_semantics"]["parameters"]
    expect("parameter rows", keys, list(parameters))
    for r, key in zip(rows, keys, strict=False):
        expect(f"{key} active is 'The same'", r[2] == "The same",
               bool(parameters.get(key, {}).get("active", {}).get("same_as_passive")))

    rows = _table(found, ("Members", "F1 cells per condition", "F2 cells per condition", "Per condition",
                          "All four conditions"), problems)
    fields = data["fields"]
    expect("counts", [int(cell.split("= ")[-1].replace(",", "")) for cell in rows[0]] if rows else [],
           [len(data["population"]["order"]), fields["F1"]["cells_per_condition"],
            fields["F2"]["cells_per_condition"], fields["cells_per_condition"], fields["cells_total"]])

    rows = _table(found, ("#", "Criterion", "How it is decided (statically)"), problems)
    expect("census criteria", [(r[0], r[1]) for r in rows],
           [(c["id"], c["criterion"]["text"]) for c in data["census"]["criteria"]])

    rows = _table(found, ("Clause", "Kind", "Condition", "Evaluated on"), problems)
    expect("E8-D clauses", [(r[0].split(" ", 1)[0], r[0].split(" ", 1)[1], r[1], r[3]) for r in rows],
           [(c["id"], c["name"], c["kind"], c["evaluated_on"]) for c in data["gates"]["E8-D"]["clauses"]])

    rows = _table(found, ("#", "Check", "Condition"), problems)
    expect("CQ8 checks", [(r[0], r[1]) for r in rows], [(c["id"], c["name"]) for c in data["gates"]["CQ8"]["checks"]])

    rows = _table(found, ("ID", "Statement", "SUPPORTED if and only if", "REFUTED if and only if"), problems)
    hypotheses = data["hypotheses"]
    expect("hypotheses", [tuple(r) for r in rows],
           [(k, plain(hypotheses[k]["statement"]["text"]), plain(hypotheses[k]["supported"]["text"]),
             plain(hypotheses[k]["refuted"]["text"])) for k in hypotheses if k.startswith("H8-")])

    rows = _table(found, ("Flag", "Raised if and only if"), problems)
    flags = data["pathology"]["flags"]
    expect("flags", [(r[0].split(" ", 1)[0], r[0].split(" ", 1)[1]) for r in rows],
           [(k, v["name"]) for k, v in flags.items()])
    for r in rows:
        flag = flags.get(r[0].split(" ", 1)[0], {})
        if "text" in flag:
            expect(f"{r[0]} text", r[1], flag["text"])

    interpretation = data["interpretation"]
    rows = _table(found, ("Row", "E8-D", "(H8-SUB, H8-PAR)", "Registered reading"), problems)
    expect("rows", [(r[0], r[1], "all nine" if r[2] == "all nine" else [list(p) for p in _PAIR.findall(r[2])])
                    for r in rows],
           [(row["id"], row["e8_d"], row["combinations"] if row["combinations"] == "all nine"
             else [list(pair) for pair in row["combinations"]]) for row in interpretation["rows"]])
    for r, row in zip(rows, interpretation["rows"], strict=False):
        if not r[3].startswith(plain(row["reading"]["text"])):
            problems.append(f"row {row['id']} reading is not the markdown's")

    rows = _table(found, ("H8-TAX", "Qualifier"), problems)
    tax = interpretation["no_choice_tax_qualifier"]
    expect("H8-TAX qualifiers", {r[0]: _quoted(r[1]) for r in rows}, {s: tax[s]["text"] for s in _STATUSES})

    rows = _table(found, ("Hypothesis", "Status", "Qualifier"), problems)
    qualifiers: dict[str, dict[str, str]] = {}
    hypothesis = ""
    for r in rows:
        hypothesis = r[0] or hypothesis
        qualifiers.setdefault(hypothesis, {})[r[1]] = _quoted(r[2])
        if r[2] != f'"{_quoted(r[2])}"':
            qualifiers[hypothesis][f"{r[1]}_naming"] = r[2][len(_quoted(r[2])) + 4:].split(" [Revision 2]")[0]
    expect("qualifiers", qualifiers,
           {h: {s: v["text"] for s, v in q.items()} for h, q in interpretation["qualifiers"].items() if h != "apply_to"})

    rows = _table(found, ("H8-REPEAT", "Registered reading"), problems)
    expect("H8-REPEAT readings", {r[0]: _quoted(r[1]) for r in rows},
           {s: v["text"] for s, v in interpretation["repeat_readings"].items() if isinstance(v, Mapping)})

    rows = _table(found, ("Interpretable?", "H8-ADAPT", "Registered reading, scoped to 𝒞's stratum"), problems)
    readings = interpretation["adapt"]["readings"]
    keyed = {("Yes", s): s for s in _STATUSES} | {("No", "—"): "NOT INTERPRETABLE", ("𝒞 empty", "—"): "NOT EVALUABLE"}
    expect("H8-ADAPT table", {keyed.get((r[0], r[1]), repr(r[:2])): _quoted(r[2]) for r in rows},
           {key: value["text"] for key, value in readings.items()})

    rows = _table(found, ("Core answer", "Definition"), problems)
    expect("core answer", [(r[0], r[1]) for r in rows],
           [(item["outcome"], item["definition"]["text"]) for item in interpretation["core_answer"]["order"]])

    rows = _table(found, ("ID", "Fires if and only if", "Label"), problems)
    kills = data["kill_criteria"]
    expect("kill criteria", [(r[0].split(" ", 1)[0], r[0].split(" ", 1)[1], r[1]) for r in rows],
           [(k, v["name"], v["fires"]["text"]) for k, v in kills.items() if k.startswith("KC8-")])

    rows = _table(found, ("Surface", "Field", "Type, and its JSON form"), problems)
    expect("trace fields", [(r[0].strip("`"), r[1].strip("`")) for r in rows],
           [(f["surface"], f["field"]) for f in data["traces"]["fields"]])

    rows = _table(found, ("Field", "Present, with its value", "Absent"), problems)
    expect("presence table", [(r[0].strip("`"), r[1], r[2]) for r in rows],
           [(row["field"], plain(row["present"]["text"]), plain(row["absent"]["text"]))
            for row in data["traces"]["presence"]["table"]])

    rows = _table(found, ("`applied_result.status`", "`sensed_anchors`", "What the record is"), problems)
    expect("status mapping table", rows,
           [tuple(plain(cell) for cell in row["row"]["text"]) for row in data["traces"]["status_mapping"]["rows"]])

    rows = _table(found, ("Requirement", "Verified by"), problems)
    expect("containment", [r[0] for r in rows], [c["requirement"]["text"] for c in data["containment"]["requirements"]])

    rows = _table(found, ("Property", "Registered semantics"), problems)
    expect("SENSE properties", len(rows), 11)
    expect("SENSE normalization", {r[0]: r[1] for r in rows}.get("Normalization"),
           data["sense_action"]["normalization"])

    for name, reference in data["references"].items():
        document = reference["document"] if isinstance(reference, Mapping) else reference
        if f"[`{Path(document).name}`]" not in markdown:
            problems.append(f"reference {name} ({document}) is not a governing record of the markdown")
    return problems


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_preregistration(path: Path = PREREGISTRATION_PATH, *, markdown: Path | None = None,
                         expected_sha256: str | None = None) -> Mapping[str, Any]:
    """The frozen registration, deeply immutable; fails closed on any disagreement."""
    wanted = PREREGISTRATION_SHA256 if expected_sha256 is None else expected_sha256
    digest = preregistration_digest(path)
    if digest != wanted:
        raise PreregistrationError(
            f"E8 pre-registration digest {digest} does not match the frozen {wanted}; the transcription changed.")
    data = parse(path.read_text(encoding="utf-8"))
    document = markdown if markdown is not None else markdown_path(data)
    document_digest = file_digest(document)
    if document_digest != data["authority"]["document_sha256"]:
        raise PreregistrationError(
            f"the markdown's digest {document_digest} is not the registered revision's "
            f"{data['authority']['document_sha256']}")
    problems = internal_problems(data) + markdown_problems(data, document.read_text(encoding="utf-8"))
    if problems:
        raise PreregistrationError("E8 pre-registration disagrees: " + "; ".join(problems))
    frozen: Mapping[str, Any] = freeze(data)
    return frozen
