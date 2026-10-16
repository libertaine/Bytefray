"""M2-4: symmetric A/B/Omni sensing views, static help cards and layout.

Ordinary product matches (``_pair``) and the published M2-2/M2-3 evidence
bodies only; no research harness, private input or retained local run.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from battle_client import cli
from battle_client.renderers.sensing_renderer import SensingReplayRenderer, contains, intersects
from battle_client.sensing import OmniscientView, SensingCursor, SensingView
from battle_client.sensing_presentation import (
    ALPHA1_SENSING_GUIDE,
    CARD_SCOPE_NOTE,
    PERSPECTIVE_LABELS,
    PERSPECTIVE_ORDER,
    SCENARIO_CARDS,
    SELECTOR_LABELS,
    SELECTOR_ORDER,
    SensingPresentation,
    entrant_scene,
    load_sensing_presentation,
    sensing_guide_lines,
)
from battle_client.session import ReplaySession
from battle_engine.sensing_playback import ExchangePhase
from test_v6_alpha_sensing import _pair

EVIDENCE = Path(__file__).resolve().parents[2] / "docs" / "v6" / "evidence"
BODIES = {
    ("keeper", "A"): EVIDENCE / "m2_2" / "keeper" / "seat_A",
    ("keeper", "B"): EVIDENCE / "m2_2" / "keeper" / "seat_B",
    ("reacquirer", "A"): EVIDENCE / "m2_3" / "reacquirer" / "seat_A",
    ("reacquirer", "B"): EVIDENCE / "m2_3" / "reacquirer" / "seat_B",
}
SIZES = ((900, 650), (1000, 700), (1100, 750))


def _presentation(tmp_path, a, b=(), **kwargs) -> SensingPresentation:
    cursor, _, _ = _pair(tmp_path, a, b, **kwargs)
    return SensingPresentation(cursor, "Recorded end", interval=0.05)


def _seated(tmp_path, seat, own, other=(), **kwargs) -> SensingPresentation:
    """Put the script under test in ``seat`` and select that delivered view."""
    a, b = (own, other) if seat == "A" else (other, own)
    presentation = _presentation(tmp_path, a, b, **kwargs)
    presentation.select(seat)
    return presentation


def _walk(presentation):
    views = []
    for index in range(len(presentation.controller.positions)):
        presentation.seek_index(index)
        views.append(presentation.current_view)
    return views


def _load(body: Path) -> SensingPresentation:
    session = ReplaySession()
    session.load(body / "replay.jsonl")
    presentation, reason = load_sensing_presentation(
        session, body / "replay.jsonl", body / "trace.jsonl", result=body / "result.json"
    )
    assert presentation is not None, reason
    return presentation


# --- R4-01 / R4-08: explicit selection, labels, cycle and keys -------------------


def test_selector_order_labels_and_number_key_mapping():
    assert SELECTOR_ORDER == ("A", "B", None)
    assert " | ".join(SELECTOR_LABELS[c] for c in SELECTOR_ORDER) == "A | B | Omni"
    # dispatch_key index 0/1/2 is number key 1/2/3.
    assert PERSPECTIVE_ORDER == (None, "A", "B")
    assert PERSPECTIVE_LABELS == {
        "A": "Agent A — delivered information",
        "B": "Agent B — delivered information",
        None: "Omniscient — full world state",
    }


def test_explicit_selection_cycle_and_compatibility_toggle(tmp_path):
    presentation = _presentation(tmp_path, [("sense", 91)], [("sense", 0)])
    assert presentation.selected == "A"
    for choice in ("B", None, "A"):
        presentation.select(choice)
        assert presentation.selected == choice
        assert presentation.current_view.label == PERSPECTIVE_LABELS[choice]
        assert isinstance(presentation.current_view, OmniscientView if choice is None else SensingView)
    with pytest.raises(ValueError):
        presentation.select("C")
    presentation.select(None)
    seen = []
    for _ in range(3):
        presentation.cycle()
        seen.append(presentation.selected)
    assert seen == ["A", "B", None]
    presentation.select("B")
    presentation.switch(False)
    assert presentation.selected is None
    presentation.switch(True)
    assert presentation.selected == "B", "the toggle returns to the last delivered entrant"


# --- R4-02 / R4-03: symmetric boundaries, ages, navigation and pacing --------------


@pytest.mark.parametrize("seat", ["A", "B"])
def test_no_receipt_or_history_crosses_seats(tmp_path, seat):
    # Each scanner samples the other's anchor; only its own view may show it.
    target = {"A": 91, "B": 0}
    other = "B" if seat == "A" else "A"
    presentation = _seated(tmp_path, seat, [("sense", target[seat]), ("read", 0 if seat == "A" else 91)])
    views = _walk(presentation)
    assert any(v.samples for v in views)
    presentation.select(other)
    other_core = range(8) if other == "A" else range(91, 99)
    for view in _walk(presentation):
        assert isinstance(view, SensingView) and view.entrant_id == other
        assert not view.samples and not view.contacts
        assert all(r.address in other_core and r.owner == other for r in view.reads)
        assert all(e.kind in {"observation", "read"} for e in view.events)
        text = " ".join(entrant_scene(view).lines)
        assert "Anonymous sample" not in text and "Scan positive" not in text


@pytest.mark.parametrize("seat", ["A", "B"])
def test_receipt_age_and_history_at_observation_action_and_tick_end(tmp_path, seat):
    target = {"A": 91, "B": 0}[seat]
    own_core = {"A": 0, "B": 91}[seat]
    presentation = _seated(
        tmp_path, seat, [("sense", target), ("read", own_core), ("move", 8), ("sense", target)], ticks=2
    )
    views = _walk(presentation)
    assert all(isinstance(v, SensingView) and v.entrant_id == seat for v in views)
    by = {(v.position.tick, v.position.callback, v.position.phase): v for v in views}
    request = by[(1, 1, ExchangePhase.ACTION)]
    assert not request.samples and request.events[-1].sample_status.value == "PENDING"
    assert "1 action spent" in " ".join(entrant_scene(request).lines), "cost must be visible"
    receipt = by[(1, 2, ExchangePhase.OBSERVATION)]
    assert receipt.receipt_status.value == "POSITIVE"
    (contact,) = receipt.contacts
    assert (contact.sampled_at.callback, contact.received_at.callback) == (1, 2)
    assert (contact.age_ticks, contact.age_callbacks) == (0, 1)
    read = by[(1, 3, ExchangePhase.OBSERVATION)]
    assert read.reads[-1].owner == seat and read.contacts[0].age_callbacks == 2
    moved = by[(1, 3, ExchangePhase.ACTION)]
    start = {"A": 0, "B": 91}[seat]
    assert moved.own_processes[0].anchor == (start + 8) % 512
    tick_end = by[(1, None, ExchangePhase.TICK_END)]
    tick2 = by[(2, None, ExchangePhase.TICK_END)]
    assert tick_end.contacts[0].address == contact.address
    assert tick2.contacts[0].age_ticks == 1, "age advances with the entrant's own clock"
    # Ordinals are this entrant's own callbacks: consecutive, with no opponent rows.
    ordinals = [v.position.callback for v in views if v.position.phase == ExchangePhase.OBSERVATION]
    assert ordinals == list(range(1, len(ordinals) + 1))


@pytest.mark.parametrize("seat", ["A", "B"])
def test_backward_seek_scrub_restart_and_omni_transitions_rebuild_only_the_prefix(tmp_path, seat):
    target = {"A": 91, "B": 0}[seat]
    presentation = _seated(tmp_path, seat, [("sense", target), ("sense", (target + 30) % 512), ("read", target)], ticks=3)
    forward = _walk(presentation)
    positions = presentation.controller.positions
    for index in [len(forward) - 1, 3, 9, 0, 14, 5, len(forward) // 2]:  # scrub / backward seek
        presentation.seek_index(index)
        assert presentation.current_view == forward[index]
    presentation.seek_index(10)
    presentation.restart()
    assert presentation.current_view == forward[0]
    for index in (4, 11, len(forward) - 1):
        presentation.seek_index(index)
        presentation.select(None)
        omni = presentation.current_view
        assert isinstance(omni, OmniscientView)
        presentation.select(seat)
        assert presentation.current_view == forward[index], "entrant -> Omni -> entrant round trip"
    # Omni -> entrant maps to the last permitted phase of that entrant, never a later one.
    presentation.select(None)
    for omni_index in range(0, len(presentation.controller.positions), 7):
        presentation.select(None)
        presentation.seek_index(omni_index)
        omni_tick = presentation.current_view.tick
        presentation.select(seat)
        view = presentation.current_view
        assert view in forward and view.position.tick <= max(omni_tick, positions[0].tick)
    other = "B" if seat == "A" else "A"
    presentation.select(other)
    assert all(not v.samples for v in _walk(presentation)), "switching seats keeps no prior receipts"


@pytest.mark.parametrize("seat", ["A", "B"])
def test_hidden_opponent_divergence_keeps_payload_navigation_and_pacing(tmp_path, seat):
    own = {"A": [("read", 0), ("sense", 450)], "B": [("read", 91), ("sense", 160)]}[seat]
    hidden = {
        "A": ([("move", 8)], [("write", 92, 7)], [("read", 91)]),
        "B": ([("move", 8)], [("write", 1, 7)], [("read", 0)]),
    }[seat]
    runs = [_seated(tmp_path / str(i), seat, own, other, ticks=3) for i, other in enumerate(hidden)]
    reference = runs[0]
    for presentation in runs[1:]:
        assert presentation.controller.positions == reference.controller.positions
    walks = [[entrant_scene(v) for v in _walk(p)] for p in runs]
    assert walks[1] == walks[0] and walks[2] == walks[0]
    for presentation in runs:
        presentation.restart()
        presentation.controller.play()
        presentation.controller.update(0.275)
        assert presentation.terminal_text is None
    assert len({p.index for p in runs}) == 1, "pacing must not depend on hidden opponent activity"
    for presentation in runs:
        presentation.seek_index(len(presentation.controller.positions) - 2)
        assert presentation.terminal_text is None, "no outcome before the recorded end"
        presentation.jump_to_end()
        assert presentation.terminal_text == "Recorded end"


def test_suppressed_opportunities_add_no_blank_steps_or_pauses(tmp_path):
    # A writes B's core each callback; B only ever sees its own actual callbacks.
    presentation = _presentation(tmp_path, [("write", 91, 7)] * 12, [("read", 91)] * 12, ticks=3)
    for seat in ("A", "B"):
        presentation.select(seat)
        positions = presentation.controller.positions
        ordinals = [p.callback for p in positions if p.phase == ExchangePhase.OBSERVATION]
        assert ordinals == list(range(1, len(ordinals) + 1))
        assert all(p.callback is not None for p in positions if p.phase != ExchangePhase.TICK_END)
        steps = min(5, len(positions) - 2)
        presentation.restart()
        presentation.controller.play()
        presentation.controller.update(0.05 * steps + 0.001)
        assert presentation.index == steps, "one constant interval per permitted phase"


# --- R4-05: symmetric fallback ----------------------------------------------------


@pytest.mark.parametrize("failing", ["A", "B"])
def test_either_seat_projection_failure_disables_both_delivered_views(tmp_path, monkeypatch, failing):
    _, session, _ = _pair(tmp_path, [("sense", 91)], [("sense", 0)])
    original = SensingCursor._build_frames

    def fail_for_one_seat(self):
        if self._entrant == failing:
            raise ValueError("entrant-specific projection failure")
        return original(self)

    monkeypatch.setattr(SensingCursor, "_build_frames", fail_for_one_seat)
    presentation, reason = load_sensing_presentation(session, tmp_path / "replay.jsonl", tmp_path / "trace.jsonl")
    assert presentation is None
    assert reason.startswith("Omniscient — replay only.") and "delivered perspectives disabled" in reason
    assert "entrant-specific" not in reason


@pytest.mark.parametrize("problem", ["missing_trace", "corrupt_trace", "wrong_result", "no_trace"])
def test_required_binding_failures_disable_both_views_without_details(tmp_path, problem):
    _, session, _ = _pair(tmp_path, [("sense", 91)], [("sense", 0)])
    trace, result = tmp_path / "trace.jsonl", None
    if problem == "missing_trace":
        trace = tmp_path / "absent.jsonl"
    elif problem == "corrupt_trace":
        trace.write_bytes(trace.read_bytes()[:-40])
    elif problem == "wrong_result":
        result = tmp_path / "result_missing.json"
    elif problem == "no_trace":
        trace = None
    presentation, reason = load_sensing_presentation(session, tmp_path / "replay.jsonl", trace, result=result)
    assert presentation is None
    assert reason.startswith("Omniscient — replay only.") and "delivered perspectives disabled" in reason
    assert str(tmp_path) not in reason


def test_invalid_optional_sidecar_keeps_both_delivered_views(tmp_path):
    _, session, _ = _pair(tmp_path, [("sense", 91)], [("sense", 0)])
    bad = tmp_path / "demo.json"
    bad.write_text('{"private": "DO NOT DISPLAY"}', encoding="utf-8")
    presentation, reason = load_sensing_presentation(session, tmp_path / "replay.jsonl", tmp_path / "trace.jsonl", demo=bad)
    assert presentation is not None and not reason
    assert not presentation.sidecar_verified
    for seat in ("A", "B"):
        presentation.select(seat)
        assert isinstance(presentation.current_view, SensingView)
        assert presentation.current_view.label == PERSPECTIVE_LABELS[seat]
    assert "DO NOT DISPLAY" not in presentation.notice


# --- Q3: CLI perspective values ---------------------------------------------------


@pytest.mark.parametrize("value,warned", [("A", False), ("B", False), ("omniscient", False), ("broadcast", False), ("C", True)])
def test_cli_alpha_perspective_values(tmp_path, monkeypatch, capsys, value, warned):
    _pair(tmp_path, [("sense", 91)], [("sense", 0)])
    seen = {}

    class Renderer:
        def run(self, session, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(cli, "_resolve_renderer", lambda name: Renderer)
    assert cli.main(["--renderer", "pygame", "--replay", str(tmp_path / "replay.jsonl"), "--perspective", value]) == 0
    assert seen["initial_perspective"] == value
    assert isinstance(seen["sensing_presentation"], SensingPresentation)
    assert ("Requested perspective unavailable" in capsys.readouterr().err) is warned


# --- Published evidence bodies: both seats, both starters ---------------------------


@pytest.mark.parametrize("scenario", ["keeper", "reacquirer"])
@pytest.mark.parametrize("seat", ["A", "B"])
def test_published_bodies_keep_fixture_seat_free_of_starter_receipts(scenario, seat):
    presentation = _load(BODIES[(scenario, seat)])
    fixture = "B" if seat == "A" else "A"
    presentation.select(seat)
    presentation.jump_to_end()
    starter_end = presentation.current_view
    assert starter_end.samples, "the sensing starter's own receipts are delivered"
    presentation.select(fixture)
    presentation.jump_to_end()
    fixture_end = presentation.current_view
    assert not fixture_end.samples and not fixture_end.contacts
    assert all(e.kind != "sense" for e in fixture_end.events)


def test_reacquirer_seats_with_identical_delivered_information_present_identically():
    a = _load(BODIES[("reacquirer", "A")])
    b = _load(BODIES[("reacquirer", "B")])
    b.select("B")

    def scenes(presentation, seat):
        out = []
        for index, position in enumerate(presentation.controller.positions):
            if position.callback is not None and position.callback > 8:
                break
            presentation.seek_index(index)
            scene = entrant_scene(presentation.current_view)
            # The starter's own entrant ID is the only seat-dependent delivered fact.
            lines = tuple(line.replace(f"owner {seat};", "owner SELF;") for line in scene.lines)
            out.append((position, replace(scene, label="", lines=lines)))
        return out

    left, right = scenes(a, "A"), scenes(b, "B")
    assert [p for p, _ in left] == [p for p, _ in right] and len(left) == 18
    assert left == right
    receipts = {p.callback: s for p, s in left if p.phase == ExchangePhase.OBSERVATION}
    assert "Receipt now: positive" in receipts[2].lines
    assert any("Anonymous sample at 91" in line and "absent in newer scan" in line for line in receipts[6].lines)
    assert any(line.startswith("Anonymous sample at 155") for line in receipts[8].lines)
    assert not any(re.search(r"same|moved|reacquired|identity", line, re.IGNORECASE) for _, s in left for line in s.lines)


# --- Q1 / Q2 / R4-09: one static guide and two cards ---------------------------------


def test_exactly_two_static_cards_bound_to_reviewed_inputs():
    from battle_engine.sensing_demo import resolve_teaching_agent_dir
    from battle_engine.starters import CURRENT_STARTER_DIGESTS, starter_content_digest

    assert [c.title for c in SCENARIO_CARDS] == [
        "Scenario card: Watchful Keeper", "Scenario card: Roaming Reacquirer"
    ]
    for card, body in zip(SCENARIO_CARDS, (BODIES[("keeper", "A")], BODIES[("reacquirer", "A")])):
        starter_dir = resolve_teaching_agent_dir(card.starter)
        assert card.starter_digest == CURRENT_STARTER_DIGESTS[card.starter] == starter_content_digest(starter_dir)
        assert card.fixture_digest == starter_content_digest(resolve_teaching_agent_dir(card.fixture))
        manifest = yaml.safe_load((starter_dir / "agent.yaml").read_text(encoding="utf-8"))
        assert card.parameters == tuple((k, v["default"]) for k, v in manifest["parameters"].items())
        demo = json.loads((body / "demo.json").read_text(encoding="utf-8"))
        assert demo["config"] == {"arena_size": 512, "action_budget": 8, "max_ticks": 100, "seed": 0}
        assert demo["ruleset_id"] == "bytefray-rules-6-alpha1"
        assert [e["name"] for e in demo["entrants"]] == [card.starter, card.fixture]
        assert dict(card.parameters) == demo["entrants"][0]["parameters"]
    assert [c.predicate for c in SCENARIO_CARDS] == ["keeper-K1", "reacquirer-R1"]


def test_cards_and_guide_cover_required_topics_without_state_or_verification_claims():
    guide = " ".join(ALPHA1_SENSING_GUIDE).lower()
    for topic in ("paid active sensing", "sample and delayed receipt", "anonymous locations and information age",
                  "competing action opportunities", "delivered versus omniscient", "informational"):
        assert topic in guide
    for card in SCENARIO_CARDS:
        text = "\n".join(card.lines())
        for section in ("Policy rule:", "Evidence it receives:", "Paid action alternative:",
                        "What its observations do not prove:", "What to look for:"):
            assert section in text
        assert CARD_SCOPE_NOTE in text and "personal copy" in CARD_SCOPE_NOTE
    lines = sensing_guide_lines()
    assert lines == sensing_guide_lines() and isinstance(lines, tuple)
    text = "\n".join(lines)
    assert "{" not in text and "verified demonstration" not in text.lower()
    assert sum(line.startswith("Scenario card:") for line in lines) == 2


def test_help_content_never_enters_the_entrant_payload(tmp_path):
    presentation = _presentation(tmp_path, [("sense", 91), ("read", 0)], [("sense", 0)])
    card_words = ("Scenario card", "Policy rule", "Paid action alternative", "informational summary")
    for seat in ("A", "B"):
        presentation.select(seat)
        for view in _walk(presentation):
            joined = " ".join(entrant_scene(view).lines)
            assert not any(word in joined for word in card_words)


# --- R4-06 / R4-07 / R4-08: rendered layout, labels and controls (offscreen) --------


def _renderer(pg, size, font):
    renderer = SensingReplayRenderer()
    renderer.pg = pg
    renderer.screen = pg.Surface(size)
    renderer.font = font
    return renderer


def _assert_layout(renderer, size):
    width, height = size
    leaf = {k: v for k, v in renderer.layout.items() if k not in {"content", "help", "arena_note"}}
    names = sorted(leaf)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            assert not intersects(leaf[first], leaf[second]), (first, second, size)
    texts = renderer.rendered_text
    for value, rect in texts:
        assert contains((0, 0, width, height), rect), (value, size)
        assert any(contains(region, rect) for region in renderer.layout.values()), (value, size)
    for i, (first, a) in enumerate(texts):
        for second, b in texts[i + 1:]:
            assert not intersects(a, b), (first, second, size)
    labels = [rect for _, rect in renderer.marker_label_rects]
    for i, a in enumerate(labels):
        assert contains(renderer._map_rect, a)
        assert not any(intersects(a, glyph) for glyph in renderer.marker_glyph_rects)
        assert not any(intersects(a, b) for b in labels[i + 1:])
        assert not any(intersects(a, rect) for _, rect in texts)


def _fonts(pg):
    # Product request (Consolas on Windows, DejaVu Sans Mono on the qualified
    # Linux host), the bundled fallback font, and a wider bundled stand-in so a
    # width-sensitive overflow fails on any platform, not only where it ships.
    return (pg.font.SysFont("consolas", 15), pg.font.Font(None, 15), pg.font.Font(None, 26))


@pytest.mark.gui
@pytest.mark.parametrize("scenario,seat", [("keeper", "A"), ("reacquirer", "B")])
def test_long_history_layout_all_sizes_views_and_terminal_state(scenario, seat):
    pg = pytest.importorskip("pygame")
    pg.init()
    try:
        presentation = _load(BODIES[(scenario, seat)])
        for choice in ("A", "B", None):
            presentation.select(choice)
            for at_end in (False, True):
                presentation.jump_to_end() if at_end else presentation.seek_index(len(presentation.controller.positions) // 2)
                for font in _fonts(pg):
                    for size in SIZES:
                        renderer = _renderer(pg, size, font)
                        renderer.draw(presentation)
                        _assert_layout(renderer, size)
                        drawn = " ".join(v for v, _ in renderer.rendered_text)
                        assert PERSPECTIVE_LABELS[choice] in drawn
                        assert "Space: play/pause" in drawn and "?: help" in drawn
                        assert ("Recorded end:" in drawn) is at_end
                        if choice is not None:
                            assert "Receipt now:" in drawn and "Markers are delivered facts only" in drawn
                            assert "Operator verification" not in drawn
                        else:
                            assert "Operator verification" in drawn
    finally:
        pg.quit()


@pytest.mark.gui
def test_dense_sample_labels_never_intersect_and_history_keeps_every_fact(tmp_path):
    """C2 shape: many nearby anonymous samples on one map row (ordinary match)."""
    pg = pytest.importorskip("pygame")
    presentation = _presentation(tmp_path, [("sense", 91)] * 40, [("move", 1)] * 40, ticks=10)
    presentation.jump_to_end()
    view = presentation.current_view
    assert len(view.contacts) >= 8
    pg.init()
    try:
        for font in _fonts(pg):
            for size in SIZES:
                renderer = _renderer(pg, size, font)
                renderer.draw(presentation)
                _assert_layout(renderer, size)
                labelled = len(renderer.marker_label_rects)
                requests = sum(m.kind == "request" for m in renderer.last_markers)
                assert labelled >= 1
                assert labelled + renderer.omitted_marker_labels == len(view.contacts) + requests
                if renderer.omitted_marker_labels:
                    assert "see history" in " ".join(v for v, _ in renderer.rendered_text)
                # The history list remains the complete delivered record.
                listed = [line for line in renderer.last_lines if line.startswith("Anonymous sample at")]
                assert len(listed) == len(view.contacts)
    finally:
        pg.quit()


@pytest.mark.gui
def test_selector_keys_cycle_mouse_and_state_reset(tmp_path):
    pg = pytest.importorskip("pygame")
    pg.init()
    try:
        presentation = _presentation(tmp_path, [("sense", 91), ("sense", 91), ("sense", 91)], [("read", 91)])
        presentation.seek_index(7)
        renderer = _renderer(pg, (1000, 700), pg.font.SysFont("consolas", 15))
        renderer.draw(presentation)

        def key(value):
            renderer.handle_event(pg.event.Event(pg.KEYDOWN, key=value, mod=0), presentation)
            renderer.draw(presentation)

        assert set(renderer._selector_rects) == {"A", "B", None}
        renderer.scroll_offset = 5
        key(pg.K_3)
        assert presentation.selected == "B" and renderer.scroll_offset == 0
        assert not any(m.kind in {"historical", "receipt", "request"} for m in renderer.last_markers)
        key(pg.K_1)
        assert presentation.selected is None and renderer.last_lines == ()
        key(pg.K_2)
        assert presentation.selected == "A"
        cycle = []
        for value in (pg.K_v, pg.K_p, pg.K_v):
            key(value)
            cycle.append(presentation.selected)
        assert cycle == ["B", None, "A"]
        for choice in ("B", None, "A"):
            x, y, w, h = renderer._selector_rects[choice]
            renderer.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(x + w // 2, y + h // 2)), presentation)
            renderer.draw(presentation)
            assert presentation.selected == choice
            assert presentation.current_view.label == PERSPECTIVE_LABELS[choice]
        # Pause/step, speed, restart and End are unchanged across perspectives.
        key(pg.K_3)
        key(pg.K_RIGHT)
        index = presentation.index
        key(pg.K_LEFT)
        assert presentation.index == index - 1
        key(pg.K_PLUS)
        assert presentation.speed == 2
        key(pg.K_END)
        assert presentation.at_end and presentation.terminal_text == "Recorded end"
        key(pg.K_HOME)
        assert presentation.index == 0 and presentation.terminal_text is None
    finally:
        pg.quit()


@pytest.mark.gui
def test_help_page_shows_the_shared_cards_outside_the_arena_in_every_view(tmp_path):
    pg = pytest.importorskip("pygame")
    pg.init()
    try:
        presentation = _presentation(tmp_path, [("sense", 91)], [("sense", 0)])
        presentation.seek_index(5)
        pages = {}
        for choice in ("A", "B", None):
            presentation.select(choice)
            for size in SIZES:
                renderer = _renderer(pg, size, pg.font.SysFont("consolas", 15))
                renderer.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_SLASH, mod=pg.KMOD_SHIFT), presentation)
                assert renderer.help_visible
                renderer.draw(presentation)
                _assert_layout(renderer, size)
                assert "help" in renderer.layout and not renderer.marker_label_rects
                help_text = [v for v, r in renderer.rendered_text if contains(renderer.layout["help"], r)]
                assert help_text[0].startswith("Help (? closes it")
                assert not any("Anonymous sample" in v for v in help_text)
                seen = list(help_text)
                for _ in range(40):
                    renderer.handle_event(pg.event.Event(pg.MOUSEWHEEL, y=-1), presentation)
                    renderer.draw(presentation)
                    seen += [v for v, r in renderer.rendered_text if contains(renderer.layout["help"], r)]
                joined = " ".join(seen)
                assert "Scenario card: Watchful Keeper" in joined and "Scenario card: Roaming Reacquirer" in joined
                assert "What its observations do not prove:" in joined
                # Visible height differs by view (disclaimer rows); the full page must not.
                pages[(choice, size)] = tuple(dict.fromkeys(seen))
        for size in SIZES:
            assert pages[("A", size)] == pages[("B", size)] == pages[(None, size)], "help is view-independent"
    finally:
        pg.quit()


@pytest.mark.gui
def test_real_sdl_loop_initial_b_perspective_and_queued_switches(tmp_path, monkeypatch):
    """Bounded real window/event loop; scripted input is not a human result."""
    pg = pytest.importorskip("pygame")
    _pair(tmp_path, [("sense", 91)], [("sense", 0), ("read", 91)])
    draw = SensingReplayRenderer.draw
    keys = iter([pg.K_RIGHT, pg.K_RIGHT, pg.K_RIGHT, pg.K_1, pg.K_2, pg.K_3, pg.K_v, pg.K_v, pg.K_v,
                 pg.K_QUESTION, pg.K_QUESTION, pg.K_HOME, pg.K_END])
    frames = []

    def bounded_draw(renderer, presentation):
        draw(renderer, presentation)
        frames.append((presentation.selected, presentation.position, renderer.help_visible))
        key = next(keys, None)
        pg.event.post(pg.event.Event(pg.QUIT) if key is None else pg.event.Event(pg.KEYDOWN, key=key, mod=0))

    monkeypatch.setattr(SensingReplayRenderer, "draw", bounded_draw)
    assert cli.main(["--renderer", "pygame", "--replay", str(tmp_path / "replay.jsonl"), "--paused", "--perspective", "B"]) == 0
    selected = [f[0] for f in frames]
    assert selected[0] == "B"
    assert selected[4:10] == [None, "A", "B", None, "A", "B"]
    assert any(f[2] for f in frames)
