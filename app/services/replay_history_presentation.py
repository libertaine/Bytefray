"""Qt-free presentation rules for the Replay History browser (V5 Phase 7C).

Everything the browser *decides* about how a history occurrence reads lives
here: column text, the approximate-timestamp marker, source and replay-state
labels, detail-pane grouping, and the mapping from filter controls to a
:class:`~battle_engine.replay_history.HistoryQuery`. The widgets in
``app/views/replay_history.py`` render these answers; they do not compute them.

Two rules this module exists to hold:

**It formats already-normalized backend data and nothing else.** No artifact
is opened, no health state is re-derived, no timestamp fallback is re-decided,
and no identity is computed. Those are Phase 7B's answers, arriving as typed
:class:`~battle_engine.replay_history.HistoryRow` /
:class:`~battle_engine.replay_history.HistoryDetail` values.

**A fallback timestamp is never presented as authoritative.** Phase 7B records
*where* a time came from alongside the time itself
(:class:`~battle_engine.replay_history.TimestampConfidence`); anything other
than a recorded ``completed_at`` is prefixed ``≈`` in text -- not styled, so
the distinction survives a screen reader, a copied cell, and a monochrome
display.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from typing import Any

from battle_engine.replay_history import (
    EntryHealth,
    HistoryDetail,
    HistoryEntrant,
    HistoryQuery,
    HistoryRow,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayResolution,
    ReplayState,
    ResultHealth,
    RulesetFacet,
    TimestampConfidence,
    WorkflowSource,
)

# ----------------------------------------------------------------------
# Columns
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class HistoryColumn:
    """One MVP history column (Phase 6 Section O fixes this exact set)."""

    key: str
    title: str
    #: Starting width in pixels. The user may resize; nothing is persisted,
    #: because Bytefray has no table-state persistence mechanism to reuse.
    width: int


COLUMN_DATE = "date"
COLUMN_ENTRANTS = "entrants"
COLUMN_RESULT = "result"
COLUMN_RULESET = "ruleset"
COLUMN_SEED = "seed"
COLUMN_SOURCE = "source"
COLUMN_REPLAY = "replay"

# Widths measured against real rendered content in the shipped UI font rather
# than guessed: the longest value each column can actually hold (a marked
# approximate timestamp, ``Ruleset v5 r1 alpha1``, ``No result recorded``,
# ``Not produced``) plus padding. Entrants is the one column whose content is
# unbounded, so it takes the leftover width instead of a fixed size.
HISTORY_COLUMNS: tuple[HistoryColumn, ...] = (
    HistoryColumn(COLUMN_DATE, "Date", 165),
    HistoryColumn(COLUMN_ENTRANTS, "Entrants", 260),
    HistoryColumn(COLUMN_RESULT, "Result", 120),
    HistoryColumn(COLUMN_RULESET, "Ruleset", 130),
    HistoryColumn(COLUMN_SEED, "Seed", 105),
    HistoryColumn(COLUMN_SOURCE, "Source", 95),
    HistoryColumn(COLUMN_REPLAY, "Replay", 100),
)

UNKNOWN_TEXT = "Unknown"
UNAVAILABLE_TEXT = "—"

# ----------------------------------------------------------------------
# Stable-identifier -> label maps
#
# The backend stores stable internal identifiers and deliberately stores no
# display string (Phase 7B Section G). These maps are the whole translation,
# and they live in presentation code so a label change is never a data change.
# ----------------------------------------------------------------------

WORKFLOW_LABELS: Mapping[WorkflowSource, str] = {
    WorkflowSource.DESIGNER: "Designer",
    WorkflowSource.DEVELOPMENT: "Agent Test",
    WorkflowSource.TOURNAMENT: "Tournament",
    WorkflowSource.EVALUATION: "Evaluation",
    WorkflowSource.CLI_LATEST: "CLI Latest",
    WorkflowSource.OTHER_RUN: "Other Run",
    WorkflowSource.UNKNOWN: UNKNOWN_TEXT,
}

REPLAY_STATE_LABELS: Mapping[ReplayState, str] = {
    ReplayState.AVAILABLE: "Available",
    ReplayState.MISSING: "Missing",
    ReplayState.NOT_PRODUCED: "Not produced",
    ReplayState.INVALID: "Invalid",
    ReplayState.INACCESSIBLE: "Inaccessible",
    ReplayState.UNCHECKED: "Unchecked",
}

REPLAY_STATE_TOOLTIPS: Mapping[ReplayState, str] = {
    ReplayState.AVAILABLE: "A replay for this match is present on disk.",
    ReplayState.MISSING: "This match referenced a replay that is no longer on disk.",
    ReplayState.NOT_PRODUCED: "This workflow did not produce a Bytefray replay.",
    ReplayState.INVALID: "The recorded replay reference could not be resolved safely.",
    ReplayState.INACCESSIBLE: "The replay could not be read when history was last refreshed.",
    ReplayState.UNCHECKED: "Replay availability has not been determined yet.",
}

ENTRY_HEALTH_LABELS: Mapping[EntryHealth, str] = {
    EntryHealth.HEALTHY: "Complete",
    EntryHealth.DEGRADED: "Replay unavailable",
    EntryHealth.INCOMPLETE: "Replay only",
    EntryHealth.INVALID: "Unreadable result",
}

ENTRY_HEALTH_TOOLTIPS: Mapping[EntryHealth, str] = {
    EntryHealth.HEALTHY: "Match details are complete.",
    EntryHealth.DEGRADED: (
        "Match details are complete, but the replay is not available for playback."
    ),
    EntryHealth.INCOMPLETE: (
        "Only a replay was found here. There is no result file, so outcome "
        "details are unknown."
    ),
    EntryHealth.INVALID: (
        "A result file exists here but could not be interpreted. Some details "
        "are unavailable."
    ),
}

# Text markers, so health never depends on color or an icon alone (Section 21).
ENTRY_HEALTH_MARKERS: Mapping[EntryHealth, str] = {
    EntryHealth.HEALTHY: "",
    EntryHealth.DEGRADED: "!",
    EntryHealth.INCOMPLETE: "?",
    EntryHealth.INVALID: "×",
}

RESULT_HEALTH_LABELS: Mapping[ResultHealth, str] = {
    ResultHealth.VALID: "Valid",
    ResultHealth.MALFORMED: "Malformed",
    ResultHealth.UNSUPPORTED: "Unsupported version",
    ResultHealth.INACCESSIBLE: "Unreadable",
    ResultHealth.MISSING: "Not present",
}

TIMESTAMP_CONFIDENCE_TOOLTIPS: Mapping[TimestampConfidence, str] = {
    TimestampConfidence.RECORDED: "Completion time recorded by the match itself.",
    TimestampConfidence.DIRECTORY_INFERRED: (
        "Approximate time inferred from historical artifact metadata."
    ),
    TimestampConfidence.FILESYSTEM_FALLBACK: (
        "Approximate time inferred from historical artifact metadata."
    ),
    TimestampConfidence.UNKNOWN: "No completion time could be determined for this match.",
}

TIMESTAMP_CONFIDENCE_LABELS: Mapping[TimestampConfidence, str] = {
    TimestampConfidence.RECORDED: "Recorded by the match",
    TimestampConfidence.DIRECTORY_INFERRED: "Approximate — inferred from the run folder name",
    TimestampConfidence.FILESYSTEM_FALLBACK: "Approximate — file modification time",
    TimestampConfidence.UNKNOWN: "Unavailable",
}

#: Prefix marking any timestamp that is not the match's own recorded time.
APPROXIMATE_PREFIX = "≈ "

APPROXIMATE_TOOLTIP = "Approximate time inferred from historical artifact metadata."

#: Shown for a ``runs/_loose`` occurrence. Informational, never an error: the
#: match is real and current, the *slot* just keeps no history depth.
LOOSE_NON_DURABLE_NOTE = (
    "CLI Latest is overwritten by the next loose CLI run. This entry is not "
    "durable history."
)

RULESET_CONFIDENCE_LABELS: Mapping[str, str] = {
    "recorded": "Recorded by the match",
    "recovered": "Recovered from match metadata",
    "not_applicable": "Not applicable to this match type",
    "unknown": "Not recorded",
}

_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


# ----------------------------------------------------------------------
# Timestamps
# ----------------------------------------------------------------------


def local_moment(row_or_ns: HistoryRow | int) -> datetime:
    """The effective timestamp as an aware local datetime.

    Always derived from ``effective_timestamp_ns``, never from the stored
    string: a recorded ``completed_at`` keeps whatever offset the writer used,
    while a fallback value is normalized UTC, and the epoch field is the one
    representation that is uniform across both.
    """

    nanoseconds = row_or_ns if isinstance(row_or_ns, int) else row_or_ns.effective_timestamp_ns
    return datetime.fromtimestamp(nanoseconds / 1_000_000_000, tz=timezone.utc).astimezone()


def format_local_datetime(moment: datetime) -> str:
    """``Sep 11, 2026 3:42 PM`` -- no platform-specific strftime padding flags."""

    hour = moment.hour % 12 or 12
    meridiem = "AM" if moment.hour < 12 else "PM"
    return (
        f"{_MONTHS[moment.month - 1]} {moment.day}, {moment.year} "
        f"{hour}:{moment.minute:02d} {meridiem}"
    )


def is_approximate(row: HistoryRow) -> bool:
    """Whether this row's time is anything other than the match's own record."""

    return (
        row.timestamp_known
        and row.timestamp_confidence is not TimestampConfidence.RECORDED
    )


def format_timestamp(row: HistoryRow) -> str:
    """Date cell text, with ``≈`` for any inferred time and ``Unknown`` for none."""

    if not row.timestamp_known:
        return UNKNOWN_TEXT
    text = format_local_datetime(local_moment(row))
    return f"{APPROXIMATE_PREFIX}{text}" if is_approximate(row) else text


def timestamp_tooltip(row: HistoryRow) -> str:
    return TIMESTAMP_CONFIDENCE_TOOLTIPS[row.timestamp_confidence]


# ----------------------------------------------------------------------
# Row cells
# ----------------------------------------------------------------------


def format_entrants(row: HistoryRow) -> str:
    """``Nemesis vs Viper`` for a pair; a bounded summary beyond three.

    Beyond three names the cell would stop being readable long before it
    stopped being long, so it collapses to a count. Every name stays visible
    in the detail pane, which is where an exhaustive list belongs.
    """

    summary = row.entrant_summary.strip()
    if not summary:
        return UNKNOWN_TEXT if row.entrant_count == 0 else f"{row.entrant_count} entrants"
    if row.entrant_count > 3:
        first = summary.split(" vs ")[0]
        return f"{first} and {row.entrant_count - 1} others"
    return summary


def format_result(row: HistoryRow) -> str:
    """Winner name, ``Tie``, ``Unknown``, or the reason the outcome is unusable.

    The GUI never infers a winner: an unreadable or result-less entry reports
    that fact instead of guessing one from replay content.
    """

    if row.entry_health is EntryHealth.INVALID:
        return "Invalid metadata"
    if row.entry_health is EntryHealth.INCOMPLETE:
        return "No result recorded"
    if row.outcome_state is OutcomeState.TIE:
        return "Tie"
    if row.outcome_state is OutcomeState.WINNER:
        if row.winner_display_name and row.winner:
            return f"{row.winner_display_name} ({row.winner})"
        return row.winner or UNKNOWN_TEXT
    return UNKNOWN_TEXT


def format_ruleset(row: HistoryRow) -> str:
    """A readable Ruleset label; the exact ID stays in the tooltip and details."""

    return ruleset_label(row.ruleset_id, row.ruleset_confidence)


def ruleset_label(ruleset_id: str | None, confidence: str) -> str:
    if ruleset_id:
        return _readable_ruleset(ruleset_id)
    return "N/A" if confidence == "not_applicable" else UNKNOWN_TEXT


def _readable_ruleset(ruleset_id: str) -> str:
    """``bytefray-rules-4-alpha1`` -> ``Ruleset v4 alpha1``.

    Derived from the identifier's own shape rather than a fixed table, so a
    historical or research Ruleset the current product no longer offers still
    reads correctly. Anything that does not match falls back to the exact ID,
    which is never wrong -- only less friendly.
    """

    prefix = "bytefray-rules-"
    if not ruleset_id.startswith(prefix):
        return ruleset_id
    remainder = ruleset_id[len(prefix) :]
    if not remainder:
        return ruleset_id
    parts = remainder.split("-")
    if not parts[0].isdigit():
        return ruleset_id
    label = f"Ruleset v{parts[0]}"
    return f"{label} {' '.join(parts[1:])}" if len(parts) > 1 else label


def format_seed(row: HistoryRow) -> str:
    return UNAVAILABLE_TEXT if row.seed is None else str(row.seed)


def format_source(row: HistoryRow) -> str:
    return WORKFLOW_LABELS.get(row.workflow, UNKNOWN_TEXT)


def format_replay(row: HistoryRow) -> str:
    return REPLAY_STATE_LABELS.get(row.replay_state, UNKNOWN_TEXT)


def row_text(row: HistoryRow, column_key: str) -> str:
    """Display text for one cell."""

    if column_key == COLUMN_DATE:
        return format_timestamp(row)
    if column_key == COLUMN_ENTRANTS:
        return format_entrants(row)
    if column_key == COLUMN_RESULT:
        return format_result(row)
    if column_key == COLUMN_RULESET:
        return format_ruleset(row)
    if column_key == COLUMN_SEED:
        return format_seed(row)
    if column_key == COLUMN_SOURCE:
        return format_source(row)
    if column_key == COLUMN_REPLAY:
        return format_replay(row)
    return ""


def row_tooltip(row: HistoryRow, column_key: str) -> str:
    """Per-cell tooltip. Health and non-durability are appended everywhere.

    Health reaches the user as words in every column's tooltip and as a text
    marker in the Date cell, so it is never carried by color alone.
    """

    parts: list[str] = []
    if column_key == COLUMN_DATE:
        parts.append(timestamp_tooltip(row))
    elif column_key == COLUMN_ENTRANTS and row.entrant_count:
        parts.append(row.entrant_summary)
    elif column_key == COLUMN_RULESET and row.ruleset_id:
        parts.append(f"Ruleset ID: {row.ruleset_id}")
        parts.append(RULESET_CONFIDENCE_LABELS.get(row.ruleset_confidence, row.ruleset_confidence))
    elif column_key == COLUMN_REPLAY:
        parts.append(REPLAY_STATE_TOOLTIPS.get(row.replay_state, ""))
    elif column_key == COLUMN_RESULT:
        parts.append(format_result(row))
    elif column_key == COLUMN_SEED and row.seed is not None:
        parts.append("The match seed. Reproducing a match also needs its agents and Ruleset.")

    if row.entry_health is not EntryHealth.HEALTHY:
        parts.append(ENTRY_HEALTH_TOOLTIPS[row.entry_health])
    if not row.durable_location:
        parts.append(LOOSE_NON_DURABLE_NOTE)
    return "\n".join(part for part in parts if part)


def row_accessible_text(row: HistoryRow) -> str:
    """One spoken summary of a row, health included as words."""

    parts = [
        format_timestamp(row),
        format_entrants(row),
        format_result(row),
        f"Replay {format_replay(row).lower()}",
        ENTRY_HEALTH_LABELS[row.entry_health],
    ]
    if not row.durable_location:
        parts.append("not durable history")
    return ", ".join(parts)


def health_marker(row: HistoryRow) -> str:
    """Short textual health marker shown beside the Date cell."""

    return ENTRY_HEALTH_MARKERS.get(row.entry_health, "")


def is_non_durable(row: HistoryRow) -> bool:
    return not row.durable_location


# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------

#: Result/winner filter choices. Backed by ``outcome_states``, which is the
#: indexed, enumerable dimension. An exact-winner control is deliberately not
#: offered: the backend's ``winner`` filter is exact-match and there is no
#: winner-discovery facet, so the control would demand a string the user
#: cannot see. Entrant search already covers "matches involving X".
RESULT_FILTER_ANY = "any"
RESULT_FILTER_WINNER = "winner"
RESULT_FILTER_TIE = "tie"
RESULT_FILTER_UNKNOWN = "unknown"

RESULT_FILTER_CHOICES: tuple[tuple[str, str], ...] = (
    (RESULT_FILTER_ANY, "All results"),
    (RESULT_FILTER_WINNER, "Has a winner"),
    (RESULT_FILTER_TIE, "Tie"),
    (RESULT_FILTER_UNKNOWN, "Unknown / no winner"),
)

_RESULT_FILTER_STATES: Mapping[str, tuple[OutcomeState, ...]] = {
    RESULT_FILTER_WINNER: (OutcomeState.WINNER,),
    RESULT_FILTER_TIE: (OutcomeState.TIE,),
    RESULT_FILTER_UNKNOWN: (OutcomeState.UNKNOWN,),
}

#: Replay-state filter choices, mapped straight onto the backend enum.
REPLAY_FILTER_ANY = "any"

REPLAY_FILTER_CHOICES: tuple[tuple[str, str], ...] = (
    (REPLAY_FILTER_ANY, "All replays"),
    (ReplayState.AVAILABLE.value, REPLAY_STATE_LABELS[ReplayState.AVAILABLE]),
    (ReplayState.MISSING.value, REPLAY_STATE_LABELS[ReplayState.MISSING]),
    (ReplayState.NOT_PRODUCED.value, REPLAY_STATE_LABELS[ReplayState.NOT_PRODUCED]),
    (ReplayState.INVALID.value, REPLAY_STATE_LABELS[ReplayState.INVALID]),
    (ReplayState.INACCESSIBLE.value, REPLAY_STATE_LABELS[ReplayState.INACCESSIBLE]),
    (ReplayState.UNCHECKED.value, REPLAY_STATE_LABELS[ReplayState.UNCHECKED]),
)

#: Workflow/source filter choices in product-meaningful order.
SOURCE_FILTER_ANY = "any"

SOURCE_FILTER_CHOICES: tuple[tuple[str, str], ...] = (
    (SOURCE_FILTER_ANY, "All sources"),
    *(
        (workflow.value, WORKFLOW_LABELS[workflow])
        for workflow in (
            WorkflowSource.DESIGNER,
            WorkflowSource.DEVELOPMENT,
            WorkflowSource.TOURNAMENT,
            WorkflowSource.EVALUATION,
            WorkflowSource.CLI_LATEST,
            WorkflowSource.OTHER_RUN,
            WorkflowSource.UNKNOWN,
        )
    ),
)

#: Sentinel filter values for the two Ruleset cases that are not an ID.
RULESET_FILTER_ANY = "any"
RULESET_FILTER_NONE = "__none__"


@dataclass(frozen=True)
class RulesetChoice:
    """One Ruleset filter entry: a label plus the query value it selects."""

    value: str
    label: str


def ruleset_filter_choices(facets: Sequence[RulesetFacet]) -> tuple[RulesetChoice, ...]:
    """Ruleset choices built from what the index actually holds.

    Fed by ``ReplayHistoryService.ruleset_facets()`` rather than the Designer's
    new-match Ruleset list, because history legitimately contains identities
    the current product no longer offers; offering only the latter would make
    those matches unfilterable.
    """

    named: list[RulesetChoice] = []
    unnamed_count = 0
    for facet in facets:
        if facet.ruleset_id is None:
            unnamed_count += facet.count
            continue
        named.append(
            RulesetChoice(
                facet.ruleset_id,
                f"{_readable_ruleset(facet.ruleset_id)}  ({facet.count:,})",
            )
        )
    choices = [RulesetChoice(RULESET_FILTER_ANY, "All Rulesets"), *named]
    if unnamed_count:
        choices.append(
            RulesetChoice(RULESET_FILTER_NONE, f"No Ruleset recorded  ({unnamed_count:,})")
        )
    return tuple(choices)


def parse_seed_text(text: str) -> tuple[int | None, bool]:
    """``(seed, valid)`` for the Seed field, tolerant of partial typing.

    An empty or whitespace-only field means "no seed filter" and is valid.
    Anything that is not a plain integer is invalid, and the caller marks the
    field rather than raising a dialog at every keystroke.
    """

    candidate = text.strip()
    if not candidate:
        return None, True
    try:
        return int(candidate, 10), True
    except ValueError:
        return None, False


@dataclass(frozen=True)
class HistoryFilterState:
    """The browser's complete filter state, independent of any widget.

    Frozen so a query generation can hold onto exactly the state it was built
    from, and so a late worker response can be compared against the state that
    is current now.
    """

    entrant_text: str = ""
    ruleset_value: str = RULESET_FILTER_ANY
    result_value: str = RESULT_FILTER_ANY
    source_value: str = SOURCE_FILTER_ANY
    replay_value: str = REPLAY_FILTER_ANY
    seed_text: str = ""
    start_date: datetime | None = None
    end_date: datetime | None = None

    @property
    def is_unfiltered(self) -> bool:
        return self == HistoryFilterState()

    @property
    def seed_is_valid(self) -> bool:
        return parse_seed_text(self.seed_text)[1]

    def to_query(self) -> HistoryQuery:
        """Map filter state onto the typed backend query.

        An invalid partial seed constrains nothing rather than matching
        nothing: the user is mid-typing, and an empty table would be a
        misleading answer to an unfinished question.
        """

        seed, _valid = parse_seed_text(self.seed_text)
        entrant = self.entrant_text.strip()

        ruleset_ids: tuple[str | None, ...] | None = None
        if self.ruleset_value == RULESET_FILTER_NONE:
            ruleset_ids = (None,)
        elif self.ruleset_value != RULESET_FILTER_ANY:
            ruleset_ids = (self.ruleset_value,)

        workflows: tuple[WorkflowSource, ...] | None = None
        if self.source_value != SOURCE_FILTER_ANY:
            workflows = (WorkflowSource(self.source_value),)

        replay_states: tuple[ReplayState, ...] | None = None
        if self.replay_value != REPLAY_FILTER_ANY:
            replay_states = (ReplayState(self.replay_value),)

        return HistoryQuery(
            entrant_text=entrant or None,
            ruleset_ids=ruleset_ids,
            outcome_states=_RESULT_FILTER_STATES.get(self.result_value),
            start=self.start_date,
            end=self.end_date,
            seed=seed,
            workflows=workflows,
            replay_states=replay_states,
        )


def day_bounds(year: int, month: int, day: int) -> tuple[datetime, datetime]:
    """Local start-of-day and end-of-day for an inclusive date-range bound.

    Aware local datetimes, so the backend's epoch conversion means the day the
    user picked in their own timezone rather than a UTC day that straddles it.
    """

    start = datetime(year, month, day, tzinfo=None).astimezone()
    end = datetime.combine(start.date(), time(23, 59, 59, 999_999)).astimezone()
    return start, end


# ----------------------------------------------------------------------
# Detail pane
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class DetailField:
    label: str
    value: str
    tooltip: str = ""


@dataclass(frozen=True)
class DetailSection:
    title: str
    fields: tuple[DetailField, ...] = ()
    #: Rendered collapsed/secondary: exact identifiers and paths, useful when
    #: diagnosing an artifact and noise the rest of the time.
    advanced: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)


def _text(value: object) -> str:
    if value is None:
        return UNAVAILABLE_TEXT
    rendered = str(value).strip()
    return rendered or UNAVAILABLE_TEXT


def _entrant_line(entrant: HistoryEntrant) -> str:
    """One entrant's identity line; every optional field may legitimately be None."""

    pieces = [f"{entrant.ordinal + 1}. {entrant.label}"]
    qualifiers: list[str] = []
    if entrant.agent_id and entrant.agent_id != entrant.label:
        qualifiers.append(entrant.agent_id)
    if entrant.runtime_kind:
        qualifiers.append(str(entrant.runtime_kind))
    if entrant.api_version is not None:
        qualifiers.append(f"Agent API v{entrant.api_version}")
    if entrant.agent_version:
        qualifiers.append(f"version {entrant.agent_version}")
    if qualifiers:
        pieces.append(f"({', '.join(qualifiers)})")
    return " ".join(pieces)


def _parameters_text(parameters: Mapping[str, Any] | None) -> str:
    if not parameters:
        return UNAVAILABLE_TEXT
    return ", ".join(f"{key}={value}" for key, value in sorted(parameters.items()))


def _score_text(score: Mapping[str, Any]) -> str:
    if not score:
        return UNAVAILABLE_TEXT
    return ", ".join(f"{key}: {value}" for key, value in score.items())


def _configuration_fields(configuration: Mapping[str, Any]) -> tuple[DetailField, ...]:
    """Arena/config facts, shown only where the artifact actually recorded them."""

    if not configuration:
        return ()
    interesting = ("arena_size", "grid_size", "ticks", "tick_limit", "mode", "win_mode")
    fields = [
        DetailField(key.replace("_", " ").capitalize(), _text(configuration[key]))
        for key in interesting
        if key in configuration and configuration[key] is not None
    ]
    return tuple(fields)


def _other_configuration_field(configuration: Mapping[str, Any]) -> tuple[DetailField, ...]:
    """Whatever the artifact recorded beyond the curated Match facts.

    Kept out of the Match summary and shown with the technical details: it is
    a useful record when diagnosing an artifact and undifferentiated noise the
    rest of the time.
    """

    interesting = ("arena_size", "grid_size", "ticks", "tick_limit", "mode", "win_mode")
    remaining = sorted(set(configuration) - set(interesting))
    if not remaining:
        return ()
    return (
        DetailField(
            "Other configuration",
            ", ".join(f"{key}={configuration[key]}" for key in remaining),
        ),
    )


def _bytes_text(size: int | None) -> str:
    if size is None:
        return UNAVAILABLE_TEXT
    if size < 1024:
        return f"{size} bytes"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def non_durable_note(detail: HistoryDetail) -> str:
    """The non-durability notice for this occurrence, or ``""`` if it is durable.

    The single place that decides whether a selected occurrence is warned
    about, so the window and any test agree without the sentence being
    rendered twice in one pane.
    """

    return "" if detail.occurrence.durable_location else LOOSE_NON_DURABLE_NOTE


def detail_title(detail: HistoryDetail) -> str:
    occurrence = detail.occurrence
    names = occurrence.entrant_summary or UNKNOWN_TEXT
    return names


def build_detail_sections(detail: HistoryDetail) -> tuple[DetailSection, ...]:
    """Group one occurrence's normalized metadata for the detail pane.

    Deliberately a curated grouping rather than a field dump: everything here
    comes from the backend model, but not everything in that model belongs in
    front of a user. Every value tolerates ``None`` -- a legacy v1 artifact
    legitimately has no occurrence UUID, product version, or recorded time.
    """

    occurrence = detail.occurrence
    sections: list[DetailSection] = []

    # -- Match ---------------------------------------------------------
    if occurrence.timestamp_known:
        moment = local_moment(occurrence.effective_timestamp_ns)
        when = format_local_datetime(moment)
        if occurrence.timestamp_confidence is not TimestampConfidence.RECORDED:
            when = f"{APPROXIMATE_PREFIX}{when}"
    else:
        when = UNKNOWN_TEXT
    match_fields = [
        DetailField(
            "Time",
            when,
            TIMESTAMP_CONFIDENCE_TOOLTIPS[occurrence.timestamp_confidence],
        ),
        DetailField(
            "Time source",
            TIMESTAMP_CONFIDENCE_LABELS[occurrence.timestamp_confidence],
        ),
        DetailField(
            "Status",
            ENTRY_HEALTH_LABELS[occurrence.entry_health],
            ENTRY_HEALTH_TOOLTIPS[occurrence.entry_health],
        ),
        DetailField("Source", WORKFLOW_LABELS.get(occurrence.workflow, UNKNOWN_TEXT)),
        DetailField(
            "Ruleset",
            ruleset_label(occurrence.ruleset_id, occurrence.ruleset_confidence),
            f"Ruleset ID: {occurrence.ruleset_id}" if occurrence.ruleset_id else "",
        ),
        DetailField(
            "Ruleset provenance",
            RULESET_CONFIDENCE_LABELS.get(
                occurrence.ruleset_confidence, occurrence.ruleset_confidence
            ),
        ),
        DetailField("Seed", _text(occurrence.seed)),
        DetailField("Mode", _text(occurrence.mode)),
        *_configuration_fields(occurrence.configuration),
    ]
    sections.append(DetailSection("Match", tuple(match_fields)))

    # -- Entrants ------------------------------------------------------
    entrant_fields: list[DetailField] = []
    for entrant in occurrence.entrants:
        entrant_fields.append(
            DetailField(
                f"Entrant {entrant.ordinal + 1}",
                _entrant_line(entrant),
                f"Content hash: {entrant.content_hash}" if entrant.content_hash else "",
            )
        )
        if entrant.parameters:
            entrant_fields.append(
                DetailField("  Agent Params", _parameters_text(entrant.parameters))
            )
    if not entrant_fields:
        entrant_fields.append(DetailField("Entrants", UNKNOWN_TEXT))
    sections.append(DetailSection("Entrants", tuple(entrant_fields)))

    # -- Result --------------------------------------------------------
    sections.append(
        DetailSection(
            "Result",
            (
                DetailField("Outcome", _outcome_text(occurrence)),
                *(
                    ()
                    if occurrence.outcome_state is not OutcomeState.WINNER
                    else (
                        DetailField(
                            "Winner", winner_label(occurrence.winner, occurrence.entrants)
                        ),
                    )
                ),
                DetailField("Score", _score_text(occurrence.score)),
                DetailField("Termination", _text(occurrence.termination_reason)),
                DetailField("Ticks", _text(occurrence.ticks)),
            ),
        )
    )

    # -- Replay --------------------------------------------------------
    replay_fields = [
        DetailField(
            "Replay",
            REPLAY_STATE_LABELS.get(occurrence.replay_state, UNKNOWN_TEXT),
            REPLAY_STATE_TOOLTIPS.get(occurrence.replay_state, ""),
        ),
    ]
    if occurrence.diagnostic_message:
        replay_fields.append(DetailField("Note", occurrence.diagnostic_message))
    sections.append(DetailSection("Replay", tuple(replay_fields)))

    # -- Identity (advanced) -------------------------------------------
    sections.append(
        DetailSection(
            "Identity",
            (
                DetailField("Occurrence", _occurrence_identity_text(occurrence)),
                DetailField(
                    "Identity source",
                    _identity_source_text(occurrence.occurrence_source),
                ),
                DetailField("Match ID", _text(occurrence.match_id)),
                DetailField("Result ID", _text(occurrence.result_id)),
            ),
            advanced=True,
        )
    )

    # -- Artifact (advanced) -------------------------------------------
    artifact_fields = [
        DetailField("Result file", _text(detail.result_path)),
        DetailField("Result state", RESULT_HEALTH_LABELS[occurrence.result_health]),
        DetailField(
            "Result schema",
            UNAVAILABLE_TEXT
            if occurrence.result_schema_version is None
            else f"battle2.result v{occurrence.result_schema_version}",
        ),
        DetailField("Product version", _text(occurrence.product_version)),
        DetailField("Result size", _bytes_text(occurrence.result_fingerprint.size)),
        DetailField("Replay file", _text(detail.replay_path)),
        DetailField(
            "Replay schema",
            UNAVAILABLE_TEXT
            if occurrence.replay_schema_version is None
            else f"battle2.replay v{occurrence.replay_schema_version}",
        ),
        DetailField("Replay size", _bytes_text(occurrence.replay_fingerprint.size)),
        DetailField("First indexed", _text(detail.first_seen_at)),
        *_other_configuration_field(occurrence.configuration),
    ]
    if detail.duplicate_occurrence_location:
        artifact_fields.append(
            DetailField(
                "Duplicate",
                "Another indexed location records this same occurrence.",
            )
        )
    sections.append(DetailSection("Artifact", tuple(artifact_fields), advanced=True))

    return tuple(sections)


def _outcome_text(occurrence: Any) -> str:
    if occurrence.outcome_state is OutcomeState.TIE:
        return "Tie"
    if occurrence.outcome_state is OutcomeState.WINNER:
        winner = winner_label(occurrence.winner, occurrence.entrants)
        return f"Winner: {winner}" if occurrence.winner else "Winner recorded"
    return UNKNOWN_TEXT


def winner_label(winner: str | None, entrants: Sequence[HistoryEntrant]) -> str:
    """Resolve a recorded winner value to the entrant's display name.

    ``result.json`` records the winner as an ``agent_id`` (``"A"``), which on
    its own tells a reader nothing when the rest of the row shows real agent
    names. This detail helper resolves the entrant mapping; the compact row
    uses the index's separately projected, unambiguous winner display name.

    The recorded value is never discarded -- an unmatched winner string is
    returned as-is rather than replaced by a guess.
    """

    if not winner:
        return UNAVAILABLE_TEXT
    for entrant in entrants:
        if entrant.agent_id == winner and entrant.display_name:
            return f"{entrant.display_name} ({winner})"
    return winner


def _occurrence_identity_text(occurrence: Any) -> str:
    """Never present a synthetic key as if it were a persisted UUID."""

    if occurrence.occurrence_source is OccurrenceIdentitySource.RECORDED:
        return _text(occurrence.occurrence_id)
    return f"{occurrence.occurrence_key} (synthetic legacy identifier)"


def _identity_source_text(source: OccurrenceIdentitySource) -> str:
    if source is OccurrenceIdentitySource.RECORDED:
        return "Recorded by the match (battle2.result v2)"
    return (
        "Synthetic legacy identifier — this artifact predates recorded "
        "occurrence identity and has no persisted UUID."
    )


# ----------------------------------------------------------------------
# Status / summary text
# ----------------------------------------------------------------------


def describe_cache_state(created: bool, rebuild_required: bool, persistent: bool) -> str:
    """What to say while history is being prepared.

    Never says the user's *history* is damaged when only the disposable index
    is: a lost cache costs a rescan and nothing else.
    """

    if not persistent:
        return (
            "Preparing Replay History for this session. The history index could "
            "not be saved, so it will be rebuilt next time."
        )
    if created:
        return "Preparing Replay History for the first time…"
    if rebuild_required:
        return "Rebuilding Replay History index…"
    return "Checking for new matches…"


def describe_refresh(summary: Any) -> str:
    """One concise sentence about what a completed refresh changed."""

    if not getattr(summary, "committed", False):
        return "Refresh cancelled — existing history is unchanged."

    inserted = getattr(summary, "inserted", None)
    if inserted is not None:  # RebuildSummary
        return f"History rebuilt — {inserted:,} {_matches(inserted)} indexed."

    added = getattr(summary, "added", 0)
    updated = getattr(summary, "updated", 0) + getattr(summary, "replaced", 0)
    removed = getattr(summary, "removed", 0)
    if not (added or updated or removed):
        return "History refreshed — no changes."
    parts = []
    if added:
        parts.append(f"{added:,} added")
    if updated:
        parts.append(f"{updated:,} updated")
    if removed:
        parts.append(f"{removed:,} removed")
    return "History refreshed — " + ", ".join(parts) + "."


def describe_incomplete_scan(summary: Any) -> str:
    """Say so when part of the tree could not be read, rather than implying completeness."""

    if getattr(summary, "scan_complete", True):
        return ""
    return (
        "Some folders could not be read, so this list may be incomplete. "
        "Existing entries were kept."
    )


def _matches(count: int) -> str:
    return "match" if count == 1 else "matches"


def describe_count(loaded: int, total: int) -> str:
    """``Showing 500 of 53,458 matches`` -- loaded versus matching, never a cap."""

    if total == 0:
        return "No matches"
    if loaded >= total:
        return f"{total:,} {_matches(total)}"
    return f"Showing {loaded:,} of {total:,} {_matches(total)}"


def describe_progress(phase: str, seen: int) -> str:
    """User-facing progress text; never exposes the storage engine."""

    label = "Rebuilding history" if phase == "rebuild" else "Checking for new matches"
    return f"{label} — {seen:,} artifacts scanned…"


# ----------------------------------------------------------------------
# Empty states
# ----------------------------------------------------------------------

EMPTY_NO_HISTORY_TITLE = "No match history yet"
EMPTY_NO_HISTORY_BODY = (
    "Completed Bytefray matches will appear here. A match is listed once it "
    "has written a result file under the Bytefray runs folder."
)
EMPTY_FILTERED_TITLE = "No history matches the current filters"
EMPTY_FILTERED_BODY = "Adjust or clear the filters to see more matches."
EMPTY_PREPARING_TITLE = "Preparing Replay History…"
EMPTY_PREPARING_BODY = (
    "Bytefray is indexing your match history. Matches will appear as soon as "
    "they are ready."
)
EMPTY_ERROR_TITLE = "Replay History is unavailable"


# ----------------------------------------------------------------------
# Replay actions (Phase 7D): Open Replay / Copy Seed
#
# Enablement decisions live here, same as every other Replay History rule --
# the view asks these functions, it never inspects a ``ReplayState`` or
# ``HistoryRow`` field itself to decide whether an action is offered.
# ----------------------------------------------------------------------

OPEN_REPLAY_TOOLTIP = "Open this match's replay in Replay Viewer."
COPY_SEED_TOOLTIP = (
    "Copies the match seed. Reproducing the exact match also requires the "
    "same agents, ruleset, parameters, and configuration."
)
CHECKING_REPLAY_TEXT = "Checking replay…"
REPLAY_OPENED_TEXT = "Opened replay in Replay Viewer."
REPLAY_NO_LONGER_AVAILABLE_TEXT = "Replay file is no longer available."
REPLAY_MISMATCH_TITLE = "Replay Changed"
REPLAY_MISMATCH_BODY = (
    "This replay no longer matches the match record it was indexed with. It "
    "may have been modified or replaced since then, so Bytefray has not "
    "opened it.\n\nRefresh Replay History if you expect this file to be correct."
)

#: Why a click-time preflight declined to open a replay -- phrased as the
#: outcome of the action just taken, not the static column description in
#: ``REPLAY_STATE_TOOLTIPS`` (those describe a row; this describes a result).
OPEN_REPLAY_FAILURE_TEXT: Mapping[ReplayState, str] = {
    ReplayState.MISSING: REPLAY_NO_LONGER_AVAILABLE_TEXT,
    ReplayState.NOT_PRODUCED: "This workflow did not produce a Bytefray replay.",
    ReplayState.INVALID: "The replay path could not be resolved safely.",
    ReplayState.INACCESSIBLE: "Replay exists but cannot be read.",
    ReplayState.UNCHECKED: "Replay availability could not be determined.",
}
OPEN_REPLAY_FAILURE_FALLBACK_TEXT = "This replay is not available to open."


def open_replay_enabled(replay_state: ReplayState) -> bool:
    """Whether a row's *cached* replay state makes Open Replay worth offering.

    This is an offer, not an authorization: click-time verification
    (``resolve_replay`` plus digest preflight, run on the worker thread) is
    the actual authority and always re-runs before anything launches.
    ``UNCHECKED`` stays disabled here -- the one place discovery currently
    assigns it to a real row (an unreadable/invalid result with no
    discovered replay file) never has a file to open, so offering the button
    would only ever fail at click time.
    """

    return replay_state is ReplayState.AVAILABLE


def copy_seed_enabled(seed: int | None) -> bool:
    return seed is not None


def describe_replay_open_failure(resolution: ReplayResolution) -> str:
    """User-facing text for a click-time preflight that did not yield a playable path."""

    return OPEN_REPLAY_FAILURE_TEXT.get(resolution.state, OPEN_REPLAY_FAILURE_FALLBACK_TEXT)


def describe_seed_copied(seed: int) -> str:
    return f"Seed {seed} copied"


def describe_open_replay_check_failure(message: str) -> str:
    """A worker-side exception while checking a replay -- never a raw traceback."""

    return f"Replay could not be checked — {message}"


__all__ = [
    "APPROXIMATE_PREFIX",
    "APPROXIMATE_TOOLTIP",
    "CHECKING_REPLAY_TEXT",
    "COLUMN_DATE",
    "COLUMN_ENTRANTS",
    "COLUMN_REPLAY",
    "COLUMN_RESULT",
    "COLUMN_RULESET",
    "COLUMN_SEED",
    "COLUMN_SOURCE",
    "COPY_SEED_TOOLTIP",
    "EMPTY_ERROR_TITLE",
    "EMPTY_FILTERED_BODY",
    "EMPTY_FILTERED_TITLE",
    "EMPTY_NO_HISTORY_BODY",
    "EMPTY_NO_HISTORY_TITLE",
    "EMPTY_PREPARING_BODY",
    "EMPTY_PREPARING_TITLE",
    "ENTRY_HEALTH_LABELS",
    "ENTRY_HEALTH_MARKERS",
    "ENTRY_HEALTH_TOOLTIPS",
    "HISTORY_COLUMNS",
    "LOOSE_NON_DURABLE_NOTE",
    "OPEN_REPLAY_FAILURE_FALLBACK_TEXT",
    "OPEN_REPLAY_FAILURE_TEXT",
    "OPEN_REPLAY_TOOLTIP",
    "REPLAY_FILTER_ANY",
    "REPLAY_FILTER_CHOICES",
    "REPLAY_MISMATCH_BODY",
    "REPLAY_MISMATCH_TITLE",
    "REPLAY_NO_LONGER_AVAILABLE_TEXT",
    "REPLAY_OPENED_TEXT",
    "REPLAY_STATE_LABELS",
    "RESULT_FILTER_ANY",
    "RESULT_FILTER_CHOICES",
    "RESULT_FILTER_TIE",
    "RESULT_FILTER_UNKNOWN",
    "RESULT_FILTER_WINNER",
    "RULESET_FILTER_ANY",
    "RULESET_FILTER_NONE",
    "SOURCE_FILTER_ANY",
    "SOURCE_FILTER_CHOICES",
    "UNAVAILABLE_TEXT",
    "UNKNOWN_TEXT",
    "WORKFLOW_LABELS",
    "DetailField",
    "DetailSection",
    "HistoryColumn",
    "HistoryFilterState",
    "RulesetChoice",
    "build_detail_sections",
    "copy_seed_enabled",
    "day_bounds",
    "describe_cache_state",
    "describe_count",
    "describe_incomplete_scan",
    "describe_open_replay_check_failure",
    "describe_progress",
    "describe_refresh",
    "describe_replay_open_failure",
    "describe_seed_copied",
    "detail_title",
    "format_entrants",
    "format_local_datetime",
    "format_replay",
    "format_result",
    "format_ruleset",
    "format_seed",
    "format_source",
    "format_timestamp",
    "health_marker",
    "is_approximate",
    "is_non_durable",
    "local_moment",
    "non_durable_note",
    "open_replay_enabled",
    "parse_seed_text",
    "row_accessible_text",
    "row_text",
    "row_tooltip",
    "ruleset_filter_choices",
    "ruleset_label",
    "timestamp_tooltip",
    "winner_label",
]
