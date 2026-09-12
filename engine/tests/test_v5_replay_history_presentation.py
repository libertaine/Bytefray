"""V5 Phase 7C -- the Qt-free half of the Replay History browser.

Everything the browser decides about *what a history row says* and *what a
filter control means* is decided in ``app.services.replay_history_presentation``
and asserted here, without a display. The widgets in
``app/views/replay_history.py`` render these answers; they do not compute them,
so this module is where the presentation contract is actually pinned down.

The rules these tests exist to hold:

* a fallback timestamp is never shown as authoritative -- it carries ``≈``;
* a synthetic legacy occurrence key is never shown as a persisted UUID;
* ``runs/_loose`` is marked non-durable wherever it appears;
* every filter control maps onto a typed ``HistoryQuery`` and nothing else;
* no formatter raises when an optional backend field is ``None``.

Rows and details here come from the real Phase 7B service wherever the fact
under test is a backend fact, so a change in backend normalization surfaces as
a failure rather than drifting past a hand-built fixture.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from battle_engine.replay_history import (
    ArtifactFingerprint,
    EntryHealth,
    HistoryDetail,
    HistoryEntrant,
    HistoryOccurrence,
    HistoryRow,
    OccurrenceIdentitySource,
    OutcomeState,
    ReplayHistoryService,
    ReplayResolution,
    ReplayState,
    ResultHealth,
    RulesetFacet,
    TimestampConfidence,
    WorkflowSource,
)

from app.services import replay_history_presentation as rp

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

V2_COMPLETED_AT = "2026-09-11T15:42:00+00:00"


def _result_payload(
    *,
    schema_version: int = 2,
    winner: str | None = "B",
    seed: int | None = 4242,
    ruleset_id: str | None = "bytefray-rules-4",
    replay_filename: str | None = "replay.jsonl",
    completed_at: str | None = V2_COMPLETED_AT,
    entrants: tuple[tuple[str, str], ...] = (("A", "Alpha"), ("B", "Beta")),
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "battle2.result",
        "schema_version": schema_version,
        "result_id": "result_aaaaaaaaaaaaaaaaaaaaaa",
        "match_id": "match_aaaaaaaaaaaaaaaaaaaaaaaa",
        "mode": "b2",
        "status": "completed",
        "winner": winner,
        "termination_reason": "tick_limit",
        "ticks": 10,
        "score": {agent_id: 1.0 for agent_id, _ in entrants},
        "entrants": [
            {
                "agent_id": agent_id,
                "name": name,
                "metadata": {
                    "kind": "python",
                    "api_version": 2,
                    "agent_version": "1.0.0",
                    "source_sha256": f"sha-{agent_id}",
                    "parameters": {"reach": 4},
                },
            }
            for agent_id, name in entrants
        ],
        "reproducibility": {
            "seed": seed,
            "arena_size": 512,
            "tick_limit": 1000,
            "action_budget": 8,
            "win_mode": "score_fallback",
            "entrant_order": [agent_id for agent_id, _ in entrants],
        },
        "replay": (
            None
            if replay_filename is None
            else {
                "replay_id": "match_aaaaaaaaaaaaaaaaaaaaaaaa",
                "sha256": "0" * 64,
                "filename": replay_filename,
            }
        ),
        "backend": None,
        "ruleset_id": ruleset_id,
    }
    if schema_version == 2:
        payload["occurrence_id"] = str(uuid.uuid4())
        payload["completed_at"] = completed_at
        payload["product_version"] = "5.0.0a1"
    return payload


def _write_run(runs_root: Path, relative: str, *, with_replay: bool = True, **kwargs: Any) -> Path:
    directory = runs_root / relative
    directory.mkdir(parents=True, exist_ok=True)
    payload = _result_payload(**kwargs)
    (directory / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    if with_replay and payload["replay"] is not None:
        (directory / str(payload["replay"]["filename"])).write_text("{}\n", encoding="utf-8")
    return directory


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    (tmp_path / "runs").mkdir()
    return tmp_path


def _service(root: Path) -> ReplayHistoryService:
    return ReplayHistoryService.open(
        data_root=root, cache_path=root / "cache" / "index.sqlite3"
    )


def _rows(root: Path) -> dict[str, HistoryRow]:
    """Every indexed row, keyed by the last segment of its run directory."""

    with _service(root) as service:
        service.refresh()
        page = service.fetch_page()
        details = {row.location_id: service.fetch_detail(row.location_id) for row in page.rows}
    return {
        Path(details[row.location_id].occurrence.relative_directory).name: row
        for row in page.rows
    }


def _detail(root: Path, relative: str) -> HistoryDetail:
    with _service(root) as service:
        service.refresh()
        for row in service.fetch_page().rows:
            detail = service.fetch_detail(row.location_id)
            assert detail is not None
            if detail.occurrence.relative_directory.replace("\\", "/").endswith(relative):
                return detail
    raise AssertionError(f"no indexed occurrence under {relative}")


def _bare_row(**overrides: Any) -> HistoryRow:
    """A minimally-populated row: every optional backend field left unset.

    Used to prove no formatter depends on a field an artifact may legitimately
    not carry.
    """

    base: dict[str, Any] = {
        "location_id": "loc_test",
        "occurrence_key": "legacy-location_test",
        "occurrence_id": None,
        "occurrence_source": OccurrenceIdentitySource.SYNTHETIC_LOCATION,
        "match_id": None,
        "effective_timestamp": None,
        "effective_timestamp_ns": 0,
        "timestamp_known": False,
        "timestamp_confidence": TimestampConfidence.UNKNOWN,
        "entrant_summary": "",
        "entrant_count": 0,
        "winner": None,
        "outcome_state": OutcomeState.UNKNOWN,
        "ruleset_id": None,
        "ruleset_confidence": "unknown",
        "seed": None,
        "workflow": WorkflowSource.UNKNOWN,
        "durable_location": True,
        "duplicate_occurrence_location": False,
        "replay_state": ReplayState.UNCHECKED,
        "result_health": ResultHealth.MISSING,
        "entry_health": EntryHealth.INCOMPLETE,
        "diagnostic_category": None,
        "diagnostic_message": None,
    }
    base.update(overrides)
    return HistoryRow(**base)


# ----------------------------------------------------------------------
# Columns
# ----------------------------------------------------------------------


def test_columns_are_exactly_the_phase_6_mvp_set() -> None:
    assert [column.title for column in rp.HISTORY_COLUMNS] == [
        "Date",
        "Entrants",
        "Result",
        "Ruleset",
        "Seed",
        "Source",
        "Replay",
    ]


def test_every_column_has_text_for_a_row_with_no_optional_metadata() -> None:
    row = _bare_row()
    for column in rp.HISTORY_COLUMNS:
        assert rp.row_text(row, column.key) != ""


# ----------------------------------------------------------------------
# Timestamps
# ----------------------------------------------------------------------


def test_recorded_timestamp_is_shown_without_an_approximation_marker(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    row = _rows(tree)["run-1"]
    assert row.timestamp_confidence is TimestampConfidence.RECORDED
    assert not rp.is_approximate(row)
    text = rp.format_timestamp(row)
    assert not text.startswith(rp.APPROXIMATE_PREFIX)
    assert "2026" in text


def test_fallback_timestamp_is_prefixed_with_the_approximation_marker(tree: Path) -> None:
    """A v1 artifact has no recorded completion time, so its date must be marked."""

    _write_run(tree / "runs", "otherplace/run-1", schema_version=1)
    row = _rows(tree)["run-1"]
    assert row.timestamp_confidence is not TimestampConfidence.RECORDED
    assert rp.is_approximate(row)
    assert rp.format_timestamp(row).startswith(rp.APPROXIMATE_PREFIX)


def test_directory_inferred_timestamp_is_also_marked_approximate(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/20260911-154200", schema_version=1)
    row = _rows(tree)["20260911-154200"]
    assert row.timestamp_confidence is TimestampConfidence.DIRECTORY_INFERRED
    assert rp.format_timestamp(row).startswith(rp.APPROXIMATE_PREFIX)


def test_unknown_timestamp_reads_as_unavailable_not_as_an_epoch_date() -> None:
    row = _bare_row(timestamp_known=False, effective_timestamp_ns=0)
    assert rp.format_timestamp(row) == "Unknown"
    assert "1970" not in rp.format_timestamp(row)


def test_approximate_tooltip_explains_the_inference() -> None:
    row = _bare_row(
        timestamp_known=True,
        timestamp_confidence=TimestampConfidence.FILESYSTEM_FALLBACK,
        effective_timestamp_ns=1_700_000_000_000_000_000,
    )
    assert "Approximate" in rp.timestamp_tooltip(row)


def test_local_datetime_formatting_has_no_zero_padded_day_or_hour() -> None:
    moment = datetime(2026, 9, 8, 15, 42, tzinfo=timezone.utc).astimezone()
    text = rp.format_local_datetime(moment)
    assert ", 2026 " in text
    assert text.endswith(("AM", "PM"))


# ----------------------------------------------------------------------
# Entrants / result / ruleset / seed / source / replay
# ----------------------------------------------------------------------


def test_two_entrants_read_as_a_versus_pair(tree: Path) -> None:
    _write_run(tree / "runs", "x/run-1", entrants=(("a", "Nemesis"), ("b", "Viper")))
    assert rp.format_entrants(_rows(tree)["run-1"]) == "Nemesis vs Viper"


def test_many_entrants_collapse_to_a_bounded_summary(tree: Path) -> None:
    entrants = tuple((f"a{index}", f"Agent{index}") for index in range(6))
    _write_run(tree / "runs", "x/run-1", entrants=entrants)
    row = _rows(tree)["run-1"]
    text = rp.format_entrants(row)
    assert text == "Agent0 and 5 others"
    # The full list is never lost -- it is the tooltip, and the detail pane.
    assert "Agent5" in rp.row_tooltip(row, rp.COLUMN_ENTRANTS)


def test_tie_and_winner_and_unknown_outcomes_each_read_distinctly() -> None:
    winner = _bare_row(
        outcome_state=OutcomeState.WINNER, winner="Beta", entry_health=EntryHealth.HEALTHY
    )
    tie = _bare_row(outcome_state=OutcomeState.TIE, entry_health=EntryHealth.HEALTHY)
    unknown = _bare_row(outcome_state=OutcomeState.UNKNOWN, entry_health=EntryHealth.HEALTHY)
    assert rp.format_result(winner) == "Beta"
    assert rp.format_result(tie) == "Tie"
    assert rp.format_result(unknown) == "Unknown"


def test_degraded_and_invalid_rows_report_why_rather_than_guessing_a_winner() -> None:
    invalid = _bare_row(entry_health=EntryHealth.INVALID, outcome_state=OutcomeState.UNKNOWN)
    replay_only = _bare_row(entry_health=EntryHealth.INCOMPLETE)
    assert rp.format_result(invalid) == "Invalid metadata"
    assert rp.format_result(replay_only) == "No result recorded"


def test_historical_rulesets_render_readably_not_only_ruleset_4() -> None:
    for ruleset_id, expected in (
        ("bytefray-rules-1", "Ruleset v1"),
        ("bytefray-rules-2", "Ruleset v2"),
        ("bytefray-rules-4", "Ruleset v4"),
        ("bytefray-rules-4-alpha1", "Ruleset v4 alpha1"),
        ("bytefray-rules-3-alpha1", "Ruleset v3 alpha1"),
        ("bytefray-rules-5-r1-alpha1", "Ruleset v5 r1 alpha1"),
    ):
        assert rp.ruleset_label(ruleset_id, "recorded") == expected


def test_unrecognized_ruleset_identifier_falls_back_to_the_exact_id() -> None:
    assert rp.ruleset_label("something-else-entirely", "recorded") == "something-else-entirely"


def test_absent_ruleset_distinguishes_not_applicable_from_unknown() -> None:
    assert rp.ruleset_label(None, "not_applicable") == "N/A"
    assert rp.ruleset_label(None, "unknown") == "Unknown"


def test_ruleset_tooltip_preserves_the_exact_identifier() -> None:
    row = _bare_row(ruleset_id="bytefray-rules-4-alpha2", ruleset_confidence="recorded")
    assert "bytefray-rules-4-alpha2" in rp.row_tooltip(row, rp.COLUMN_RULESET)


def test_seed_shows_the_integer_and_never_implies_it_alone_reproduces_a_match() -> None:
    row = _bare_row(seed=4242)
    assert rp.format_seed(row) == "4242"
    assert "also needs" in rp.row_tooltip(row, rp.COLUMN_SEED)
    assert rp.format_seed(_bare_row(seed=None)) == rp.UNAVAILABLE_TEXT


def test_workflow_values_map_to_readable_source_labels() -> None:
    for workflow in WorkflowSource:
        label = rp.WORKFLOW_LABELS[workflow]
        assert label and not label.islower()
    assert rp.WORKFLOW_LABELS[WorkflowSource.CLI_LATEST] == "CLI Latest"
    assert rp.WORKFLOW_LABELS[WorkflowSource.DEVELOPMENT] == "Agent Test"


def test_every_backend_replay_state_has_a_label_and_an_explanation() -> None:
    for state in ReplayState:
        assert rp.REPLAY_STATE_LABELS[state]
        assert rp.REPLAY_STATE_TOOLTIPS[state]


def test_missing_replay_is_shown_as_a_state_not_as_an_absent_row(tree: Path) -> None:
    _write_run(tree / "runs", "x/run-1", with_replay=False)
    row = _rows(tree)["run-1"]
    assert row.replay_state is ReplayState.MISSING
    assert rp.format_replay(row) == "Missing"
    assert row.entry_health is EntryHealth.DEGRADED


# ----------------------------------------------------------------------
# Health and _loose
# ----------------------------------------------------------------------


def test_health_reaches_the_user_as_words_and_a_marker_not_color_alone() -> None:
    for health in EntryHealth:
        assert rp.ENTRY_HEALTH_LABELS[health]
        assert rp.ENTRY_HEALTH_TOOLTIPS[health]
    assert rp.health_marker(_bare_row(entry_health=EntryHealth.HEALTHY)) == ""
    assert rp.health_marker(_bare_row(entry_health=EntryHealth.DEGRADED)) != ""
    assert rp.health_marker(_bare_row(entry_health=EntryHealth.INVALID)) != ""


def test_unhealthy_row_explains_itself_in_every_column_tooltip() -> None:
    row = _bare_row(entry_health=EntryHealth.DEGRADED)
    for column in rp.HISTORY_COLUMNS:
        assert rp.ENTRY_HEALTH_TOOLTIPS[EntryHealth.DEGRADED] in rp.row_tooltip(row, column.key)


def test_accessible_row_text_states_health_in_words() -> None:
    row = _bare_row(entry_health=EntryHealth.DEGRADED, durable_location=False)
    spoken = rp.row_accessible_text(row)
    assert rp.ENTRY_HEALTH_LABELS[EntryHealth.DEGRADED] in spoken
    assert "not durable" in spoken


def test_loose_run_is_marked_non_durable_in_row_and_detail(tree: Path) -> None:
    _write_run(tree / "runs", "_loose")
    row = _rows(tree)["_loose"]
    assert row.workflow is WorkflowSource.CLI_LATEST
    assert rp.is_non_durable(row)
    assert rp.LOOSE_NON_DURABLE_NOTE in rp.row_tooltip(row, rp.COLUMN_DATE)

    detail = _detail(tree, "_loose")
    assert rp.non_durable_note(detail) == rp.LOOSE_NON_DURABLE_NOTE


def test_loose_notice_is_informational_not_phrased_as_an_error() -> None:
    text = rp.LOOSE_NON_DURABLE_NOTE.lower()
    assert "overwritten" in text
    assert "error" not in text and "corrupt" not in text and "failed" not in text


def test_durable_run_carries_no_non_durable_notice(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    row = _rows(tree)["run-1"]
    assert not rp.is_non_durable(row)
    assert rp.LOOSE_NON_DURABLE_NOTE not in rp.row_tooltip(row, rp.COLUMN_DATE)
    assert rp.non_durable_note(_detail(tree, "run-1")) == ""


def build_section(detail: HistoryDetail, title: str) -> rp.DetailSection:
    for section in rp.build_detail_sections(detail):
        if section.title == title:
            return section
    raise AssertionError(f"no {title!r} section")


# ----------------------------------------------------------------------
# Detail pane
# ----------------------------------------------------------------------


def test_v2_detail_shows_the_authoritative_occurrence_uuid(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    detail = _detail(tree, "run-1")
    assert detail.occurrence.occurrence_source is OccurrenceIdentitySource.RECORDED
    identity = build_section(detail, "Identity")
    occurrence_field = next(f for f in identity.fields if f.label == "Occurrence")
    assert occurrence_field.value == detail.occurrence.occurrence_id
    assert "synthetic" not in occurrence_field.value


def test_v1_detail_labels_its_synthetic_identifier_as_synthetic(tree: Path) -> None:
    """The Phase 6 rule: a cache-local surrogate is never shown as a real UUID."""

    _write_run(tree / "runs", "x/run-1", schema_version=1)
    detail = _detail(tree, "run-1")
    identity = build_section(detail, "Identity")
    occurrence_field = next(f for f in identity.fields if f.label == "Occurrence")
    source_field = next(f for f in identity.fields if f.label == "Identity source")
    assert "synthetic legacy identifier" in occurrence_field.value
    assert "Synthetic legacy identifier" in source_field.value


def test_detail_sections_are_grouped_not_a_raw_field_dump(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    titles = [section.title for section in rp.build_detail_sections(_detail(tree, "run-1"))]
    assert titles == ["Match", "Entrants", "Result", "Replay", "Identity", "Artifact"]


def test_identity_and_artifact_sections_are_marked_advanced(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    sections = {s.title: s for s in rp.build_detail_sections(_detail(tree, "run-1"))}
    assert sections["Identity"].advanced and sections["Artifact"].advanced
    assert not sections["Match"].advanced and not sections["Entrants"].advanced


def test_detail_reports_entrant_api_version_and_resolved_parameters(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    entrants = build_section(_detail(tree, "run-1"), "Entrants")
    rendered = " | ".join(f"{f.label}={f.value}" for f in entrants.fields)
    assert "Agent API v2" in rendered
    assert "reach=4" in rendered


def test_detail_names_the_winner_rather_than_showing_a_bare_agent_id(tree: Path) -> None:
    """``result.json`` records the winner as an agent_id; a reader needs the name."""

    _write_run(
        tree / "runs", "_designer/run-1", winner="B", entrants=(("A", "Nemesis"), ("B", "Viper"))
    )
    result = build_section(_detail(tree, "run-1"), "Result")
    winner = next(f for f in result.fields if f.label == "Winner")
    assert "Viper" in winner.value
    assert "B" in winner.value, "the recorded value must not be discarded"


def test_unmatched_winner_value_is_shown_verbatim_not_guessed() -> None:
    from battle_engine.replay_history import HistoryEntrant as _Entrant

    entrants = (_Entrant(ordinal=0, agent_id="A", display_name="Nemesis"),)
    assert rp.winner_label("Z", entrants) == "Z"
    assert rp.winner_label(None, entrants) == rp.UNAVAILABLE_TEXT


def test_a_tie_does_not_render_a_winner_field(tree: Path) -> None:
    """A tie records ``winner: "tie"``, which read as a competitor's name."""

    _write_run(tree / "runs", "_designer/run-1", winner="tie")
    result = build_section(_detail(tree, "run-1"), "Result")
    labels = [f.label for f in result.fields]
    assert "Winner" not in labels
    assert next(f for f in result.fields if f.label == "Outcome").value == "Tie"


def test_leftover_configuration_keys_stay_out_of_the_match_summary(tree: Path) -> None:
    _write_run(tree / "runs", "_designer/run-1")
    sections = {s.title: s for s in rp.build_detail_sections(_detail(tree, "run-1"))}
    match_labels = [f.label for f in sections["Match"].fields]
    assert "Other configuration" not in match_labels
    assert "Arena size" in match_labels
    assert sections["Artifact"].advanced


def test_detail_of_a_result_only_occurrence_reports_the_missing_replay(tree: Path) -> None:
    _write_run(tree / "runs", "x/run-1", with_replay=False)
    replay = build_section(_detail(tree, "run-1"), "Replay")
    assert replay.fields[0].value == "Missing"


def test_detail_never_dumps_a_traceback_or_the_artifact_body(tree: Path) -> None:
    """A malformed result becomes a bounded explanation, not a parser dump."""

    directory = tree / "runs" / "x" / "broken"
    directory.mkdir(parents=True)
    (directory / "result.json").write_text("{not json at all", encoding="utf-8")
    (directory / "replay.jsonl").write_text("{}\n", encoding="utf-8")
    detail = _detail(tree, "broken")
    rendered = "\n".join(
        f"{field.label}: {field.value}"
        for section in rp.build_detail_sections(detail)
        for field in section.fields
    )
    assert "Traceback" not in rendered
    assert "SELECT" not in rendered
    assert "not json at all" not in rendered
    assert len(rendered) < 4000


def test_detail_formatters_tolerate_every_optional_field_being_none() -> None:
    occurrence = HistoryOccurrence(
        location_id="loc_x",
        occurrence_key="legacy-location_x",
        occurrence_source=OccurrenceIdentitySource.SYNTHETIC_LOCATION,
        entrants=(HistoryEntrant(ordinal=0),),
        result_fingerprint=ArtifactFingerprint(),
        replay_fingerprint=ArtifactFingerprint(),
    )
    detail = HistoryDetail(
        occurrence=occurrence,
        duplicate_occurrence_location=False,
        result_path=None,
        replay_path=None,
        first_seen_at=None,
    )
    sections = rp.build_detail_sections(detail)
    assert sections
    for section in sections:
        for entry in section.fields:
            assert isinstance(entry.value, str) and entry.value


# ----------------------------------------------------------------------
# Filter mapping
# ----------------------------------------------------------------------


def test_default_filter_state_constrains_nothing() -> None:
    query = rp.HistoryFilterState().to_query()
    assert query == type(query)()
    assert rp.HistoryFilterState().is_unfiltered


def test_entrant_text_maps_to_the_entrant_search_and_empty_clears_it() -> None:
    assert rp.HistoryFilterState(entrant_text="  hunter ").to_query().entrant_text == "hunter"
    assert rp.HistoryFilterState(entrant_text="   ").to_query().entrant_text is None


def test_ruleset_filter_maps_an_id_and_the_no_ruleset_sentinel() -> None:
    assert rp.HistoryFilterState(ruleset_value="bytefray-rules-2").to_query().ruleset_ids == (
        "bytefray-rules-2",
    )
    assert rp.HistoryFilterState(ruleset_value=rp.RULESET_FILTER_NONE).to_query().ruleset_ids == (
        None,
    )
    assert rp.HistoryFilterState(ruleset_value=rp.RULESET_FILTER_ANY).to_query().ruleset_ids is None


def test_result_filter_maps_to_outcome_states() -> None:
    assert rp.HistoryFilterState(result_value=rp.RESULT_FILTER_TIE).to_query().outcome_states == (
        OutcomeState.TIE,
    )
    assert rp.HistoryFilterState(
        result_value=rp.RESULT_FILTER_WINNER
    ).to_query().outcome_states == (OutcomeState.WINNER,)
    assert rp.HistoryFilterState(
        result_value=rp.RESULT_FILTER_UNKNOWN
    ).to_query().outcome_states == (OutcomeState.UNKNOWN,)
    assert rp.HistoryFilterState().to_query().outcome_states is None


def test_source_filter_maps_to_a_workflow_enum() -> None:
    query = rp.HistoryFilterState(source_value=WorkflowSource.EVALUATION.value).to_query()
    assert query.workflows == (WorkflowSource.EVALUATION,)


def test_replay_filter_maps_to_a_replay_state_enum() -> None:
    query = rp.HistoryFilterState(replay_value=ReplayState.MISSING.value).to_query()
    assert query.replay_states == (ReplayState.MISSING,)


def test_every_offered_filter_choice_maps_without_raising() -> None:
    """No combo entry can produce an unmappable query."""

    for value, _label in rp.SOURCE_FILTER_CHOICES:
        rp.HistoryFilterState(source_value=value).to_query()
    for value, _label in rp.REPLAY_FILTER_CHOICES:
        rp.HistoryFilterState(replay_value=value).to_query()
    for value, _label in rp.RESULT_FILTER_CHOICES:
        rp.HistoryFilterState(result_value=value).to_query()


def test_seed_filter_accepts_an_integer_and_clears_when_empty() -> None:
    assert rp.HistoryFilterState(seed_text="4242").to_query().seed == 4242
    assert rp.HistoryFilterState(seed_text="").to_query().seed is None
    assert rp.HistoryFilterState(seed_text="  ").to_query().seed is None


def test_partial_seed_input_is_invalid_but_constrains_nothing() -> None:
    """Mid-typing must not silently empty the table, and must not raise."""

    state = rp.HistoryFilterState(seed_text="-")
    assert not state.seed_is_valid
    assert state.to_query().seed is None
    assert rp.parse_seed_text("12x") == (None, False)
    assert rp.parse_seed_text("") == (None, True)


def test_large_seed_values_are_not_truncated() -> None:
    big = 2**63 - 1
    assert rp.HistoryFilterState(seed_text=str(big)).to_query().seed == big


def test_date_bounds_cover_the_whole_local_day() -> None:
    start, end = rp.day_bounds(2026, 9, 11)
    assert start.tzinfo is not None and end.tzinfo is not None
    assert start.hour == 0 and start.minute == 0
    assert end.hour == 23 and end.minute == 59
    assert end - start < timedelta(days=1)


def test_unset_date_bounds_are_supported_independently() -> None:
    start = rp.day_bounds(2026, 9, 1)[0]
    lower_only = rp.HistoryFilterState(start_date=start).to_query()
    upper_only = rp.HistoryFilterState(end_date=start).to_query()
    assert lower_only.start == start and lower_only.end is None
    assert upper_only.end == start and upper_only.start is None


def test_filters_compose_into_one_query() -> None:
    state = rp.HistoryFilterState(
        entrant_text="hunter",
        ruleset_value="bytefray-rules-2",
        result_value=rp.RESULT_FILTER_TIE,
        source_value=WorkflowSource.DESIGNER.value,
        replay_value=ReplayState.AVAILABLE.value,
        seed_text="7",
    )
    query = state.to_query()
    assert query.entrant_text == "hunter"
    assert query.ruleset_ids == ("bytefray-rules-2",)
    assert query.outcome_states == (OutcomeState.TIE,)
    assert query.workflows == (WorkflowSource.DESIGNER,)
    assert query.replay_states == (ReplayState.AVAILABLE,)
    assert query.seed == 7
    assert not state.is_unfiltered


def test_filter_state_is_comparable_so_a_stale_response_can_be_detected() -> None:
    assert rp.HistoryFilterState(entrant_text="a") != rp.HistoryFilterState(entrant_text="b")
    assert rp.HistoryFilterState(entrant_text="a") == rp.HistoryFilterState(entrant_text="a")


# ----------------------------------------------------------------------
# Ruleset facets
# ----------------------------------------------------------------------


def test_ruleset_choices_come_from_the_index_including_historical_ids() -> None:
    facets = (
        RulesetFacet("bytefray-rules-2", "recorded", 31053),
        RulesetFacet("bytefray-rules-3-alpha1", "recorded", 6984),
        RulesetFacet(None, "unknown", 12),
    )
    choices = rp.ruleset_filter_choices(facets)
    values = [choice.value for choice in choices]
    assert values[0] == rp.RULESET_FILTER_ANY
    assert "bytefray-rules-3-alpha1" in values
    assert rp.RULESET_FILTER_NONE in values
    assert "Ruleset v3 alpha1" in choices[2].label
    assert "6,984" in choices[2].label


def test_ruleset_choices_for_an_empty_index_offer_only_all() -> None:
    assert [choice.value for choice in rp.ruleset_filter_choices(())] == [rp.RULESET_FILTER_ANY]


def test_service_reports_the_distinct_rulesets_it_actually_indexed(tree: Path) -> None:
    """The one Phase 7C backend addition, proven against a real index."""

    _write_run(tree / "runs", "x/a", ruleset_id="bytefray-rules-2")
    _write_run(tree / "runs", "x/b", ruleset_id="bytefray-rules-2")
    _write_run(tree / "runs", "x/c", ruleset_id="bytefray-rules-3-alpha1")
    with _service(tree) as service:
        service.refresh()
        facets = service.ruleset_facets()
    identities = {facet.ruleset_id: facet.count for facet in facets}
    assert identities["bytefray-rules-2"] == 2
    assert identities["bytefray-rules-3-alpha1"] == 1
    assert rp.ruleset_filter_choices(facets)[1].value == "bytefray-rules-2"


def test_ruleset_facet_filter_value_round_trips_through_a_real_query(tree: Path) -> None:
    _write_run(tree / "runs", "x/a", ruleset_id="bytefray-rules-3-alpha1")
    _write_run(tree / "runs", "x/b", ruleset_id="bytefray-rules-2")
    with _service(tree) as service:
        service.refresh()
        choice = next(
            c for c in rp.ruleset_filter_choices(service.ruleset_facets())
            if c.value == "bytefray-rules-3-alpha1"
        )
        query = rp.HistoryFilterState(ruleset_value=choice.value).to_query()
        assert service.count(query) == 1


# ----------------------------------------------------------------------
# Status text
# ----------------------------------------------------------------------


def test_cache_recovery_text_never_calls_the_users_history_corrupt() -> None:
    """Only the disposable index is rebuildable; say that, not "your data is broken"."""

    for created, rebuild, persistent in ((True, True, True), (False, True, True)):
        message = rp.describe_cache_state(created, rebuild, persistent)
        lowered = message.lower()
        assert "corrupt" not in lowered
        assert "lost" not in lowered
        assert "history" in lowered or "matches" in lowered


def test_non_persistent_cache_is_reported_as_a_session_only_index() -> None:
    message = rp.describe_cache_state(True, True, persistent=False)
    assert "session" in message.lower()


def test_refresh_summary_reports_what_changed() -> None:
    class _Reconcile:
        committed = True
        added = 12
        updated = 2
        replaced = 1
        removed = 1
        scan_complete = True

    message = rp.describe_refresh(_Reconcile())
    assert "12 added" in message and "3 updated" in message and "1 removed" in message


def test_unchanged_refresh_says_so_rather_than_listing_zeroes() -> None:
    class _Reconcile:
        committed = True
        added = updated = replaced = removed = 0
        scan_complete = True

    assert rp.describe_refresh(_Reconcile()) == "History refreshed — no changes."


def test_cancelled_refresh_is_not_reported_as_an_error() -> None:
    class _Cancelled:
        committed = False

    message = rp.describe_refresh(_Cancelled())
    assert "cancelled" in message.lower()
    assert "error" not in message.lower() and "fail" not in message.lower()


def test_incomplete_scan_is_disclosed_rather_than_implying_completeness() -> None:
    class _Partial:
        scan_complete = False

    assert "incomplete" in rp.describe_incomplete_scan(_Partial()).lower()

    class _Complete:
        scan_complete = True

    assert rp.describe_incomplete_scan(_Complete()) == ""


def test_count_text_distinguishes_loaded_from_matching() -> None:
    assert rp.describe_count(500, 53458) == "Showing 500 of 53,458 matches"
    assert rp.describe_count(12, 12) == "12 matches"
    assert rp.describe_count(1, 1) == "1 match"
    assert rp.describe_count(0, 0) == "No matches"


def test_progress_text_never_exposes_the_storage_engine() -> None:
    for phase in ("rebuild", "reconcile"):
        message = rp.describe_progress(phase, 12000)
        assert "12,000" in message
        assert "sqlite" not in message.lower() and "SELECT" not in message


def test_empty_state_copy_explains_how_history_gets_populated() -> None:
    assert "will appear here" in rp.EMPTY_NO_HISTORY_BODY
    assert "result" in rp.EMPTY_NO_HISTORY_BODY.lower()
    assert "filters" in rp.EMPTY_FILTERED_TITLE.lower()


# ----------------------------------------------------------------------
# Replay actions (Phase 7D): Open Replay / Copy Seed enablement and text
# ----------------------------------------------------------------------


def test_open_replay_is_only_enabled_for_the_available_state() -> None:
    for state in ReplayState:
        expected = state is ReplayState.AVAILABLE
        assert rp.open_replay_enabled(state) is expected, state


def test_copy_seed_enabled_requires_a_concrete_seed() -> None:
    assert rp.copy_seed_enabled(184293) is True
    assert rp.copy_seed_enabled(0) is True  # zero is a legal seed, not "missing"
    assert rp.copy_seed_enabled(-1) is True  # the contract does not reject negatives
    assert rp.copy_seed_enabled(2**63 - 1) is True  # very large seeds stay enabled
    assert rp.copy_seed_enabled(None) is False


def test_seed_copied_text_names_the_exact_seed() -> None:
    assert rp.describe_seed_copied(184293) == "Seed 184293 copied"
    assert rp.describe_seed_copied(0) == "Seed 0 copied"


def test_copy_seed_tooltip_states_the_reproduction_limitation_without_overclaiming() -> None:
    lowered = rp.COPY_SEED_TOOLTIP.lower()
    assert "seed" in lowered
    assert "agents" in lowered and "ruleset" in lowered
    # Phase 6 Sec S is explicit that this must never claim exact reproduction.
    assert "exact" not in lowered or "reproducing the exact match also requires" in lowered
    assert "guarantee" not in lowered


def test_open_replay_tooltip_names_the_viewer_and_makes_no_reproduction_claim() -> None:
    lowered = rp.OPEN_REPLAY_TOOLTIP.lower()
    assert "replay" in lowered
    assert "guarantee" not in lowered and "exact" not in lowered


def _resolution(state: ReplayState, *, path: str | None = None) -> ReplayResolution:
    return ReplayResolution(
        location_id="loc",
        state=state,
        path=path,
        expected_sha256=None,
        replay_id=None,
    )


def test_replay_open_failure_text_covers_every_non_available_state() -> None:
    for state in ReplayState:
        if state is ReplayState.AVAILABLE:
            continue
        assert state in rp.OPEN_REPLAY_FAILURE_TEXT  # no state falls through to the fallback
        message = rp.describe_replay_open_failure(_resolution(state))
        assert message  # never an empty string a status label would swallow


def test_replay_open_failure_text_matches_the_missing_race_wording() -> None:
    """Phase 7D Sec 21 pins this exact user-facing sentence for the missing-replay race."""

    assert rp.describe_replay_open_failure(_resolution(ReplayState.MISSING)) == (
        "Replay file is no longer available."
    )
    assert rp.REPLAY_NO_LONGER_AVAILABLE_TEXT == "Replay file is no longer available."


def test_open_replay_check_failure_text_is_not_a_raw_traceback() -> None:
    message = rp.describe_open_replay_check_failure("disk read error")
    assert "disk read error" in message
    assert "Traceback" not in message


def test_replay_mismatch_dialog_text_explains_without_offering_a_bypass() -> None:
    lowered_body = rp.REPLAY_MISMATCH_BODY.lower()
    assert "no longer matches" in lowered_body
    # Phase 7D Sec 14: no "open anyway" bypass is offered in this phase.
    assert "open anyway" not in lowered_body
    assert "anyway" not in lowered_body
