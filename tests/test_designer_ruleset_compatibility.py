"""GUI regression coverage for the Phase 2 M1 compatibility convergence.

Before this, only the Simple tab asked the engine's Agent-API-aware
compatibility question. Advanced asked a narrower runtime-kind-only one (so
an Agent API v2 agent was offered Ruleset v2, which cannot run it), and
Development/Evaluation asked nothing at all, offering every Ruleset and
relying on the engine to reject the match after launch.

These pin the converged behavior at each surface. The *rules* themselves
are pinned once, headlessly, against the engine policy in
``engine/tests/test_designer_ruleset_options.py``; what these add is that
each view actually applies them, including selection repair and the
fail-closed empty state.

Marked ``gui`` like the other Designer tests: excluded from the default
headless run, exercised by the dedicated display-backed workflow.
"""

from __future__ import annotations

import os

import pytest

BYTEFRAY_RULESET_ID = "bytefray-rules-1"
BYTEFRAY_RULESET_V2_ID = "bytefray-rules-2"
BYTEFRAY_RULESET_V4_ALPHA1_ID = "bytefray-rules-4-alpha1"
BYTEFRAY_RULESET_V4_ALPHA2_ID = "bytefray-rules-4-alpha2"
BYTEFRAY_RULESET_V4_ID = "bytefray-rules-4"
#: All three v4 identities accept the identical roster -- Python-only,
#: Agent API v2 -- so every surface that offers one on compatibility
#: grounds must offer all three (v4.0.0-rc1 Phase 2 added the permanent
#: stable identity alongside the two prerelease alphas). Which of them a
#: surface *prefers* is the product decision each test below pins
#: separately.
ALL_V4_IDENTITIES = {BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V4_ALPHA1_ID, BYTEFRAY_RULESET_V4_ALPHA2_ID}


def _make_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _row(name: str, kind: str, api_version: int | None = None):
    from app.services.agent_catalog import AgentRow

    meta: dict[str, object] = {"name": name, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(name, f"/agents/{name}", None, meta, agent_id=name)


def _offered(combo) -> set[str]:
    """Ruleset ids the combo presents as selectable."""

    model = combo.model()
    return {
        str(combo.itemData(index))
        for index in range(combo.count())
        if model is None or model.item(index) is None or model.item(index).isEnabled()
    }


# ---------------------------------------------------------------------------
# Advanced
# ---------------------------------------------------------------------------
#
# Phase 2 (RC2->final) inverted Advanced's selection order: the Ruleset is
# now the controlling selector, exactly like Simple, instead of being
# derived from whichever agents happened to be selected. The tests below pin
# that inverted model (UX-14 through UX-19); the pre-Phase-2 "agents choose
# the Ruleset" behavior they replace remains visible in git history.


@pytest.mark.gui
@pytest.mark.parametrize(
    ("ruleset_id", "expected_agents"),
    [
        (BYTEFRAY_RULESET_V2_ID, ["legacy"]),
        (BYTEFRAY_RULESET_V4_ID, ["proc"]),
        (BYTEFRAY_RULESET_ID, ["legacy", "vm_agent"]),
    ],
)
def test_advanced_offers_only_agents_the_selected_ruleset_can_run(
    tmp_path, ruleset_id, expected_agents
):
    """UX-15/UX-16: Agent A/B are derived from the selected Ruleset via the
    same ``agent_row_supported_by_ruleset`` predicate Simple already uses
    (UX-19 parity), not from a hand-maintained Advanced-only matrix."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(
            [
                _row("legacy", "python", 1),
                _row("proc", "python", 2),
                _row("vm_agent", "builtin"),
            ]
        )
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(ruleset_id))
        listed = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        assert listed == expected_agents
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_preserves_compatible_agent_and_replaces_only_the_incompatible_one(tmp_path):
    """UX-17 items 2/3: Ruleset v1 admits both Python API v1 and VM/blob
    agents, so a mixed A/B selection survives it; switching to the
    Python-only Ruleset v2 must then replace only the now-incompatible VM
    entrant, leaving the still-compatible Python one untouched."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("vm_agent", "builtin")])
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("vm_agent"))

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        assert panel.agentA.currentData() == "legacy"  # preserved
        assert panel.agentB.currentData() not in (None, "vm_agent")  # replaced
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_replaces_both_selections_when_neither_remains_compatible(tmp_path):
    """UX-17 items 4/5: an Agent API v1 pair has no representative under an
    Agent API v2 Ruleset, so both selections -- not just one -- are replaced
    by the deterministic first compatible option."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents(
            [
                _row("legacy", "python", 1),
                _row("legacy2", "python", 1),
                _row("proc", "python", 2),
                _row("proc2", "python", 2),
            ]
        )
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        panel.agentA.setCurrentIndex(panel.agentA.findData("legacy"))
        panel.agentB.setCurrentIndex(panel.agentB.findData("legacy2"))

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        assert panel.agentA.currentData() == "proc"
        assert panel.agentB.currentData() == "proc2"
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_advanced_handles_zero_compatible_agents_without_crashing_or_stale_selection(tmp_path):
    """UX-18 / the empty-degenerate case: a Ruleset with no discovered
    compatible agent must disable Run, show an explanation, and never
    retain a stale selection from before the Ruleset change. Returning to
    the previous Ruleset must recover cleanly (F.6)."""

    _make_app()
    from app.views.advanced import AdvancedPanel

    panel = AdvancedPanel(catalog=None, data_root=tmp_path)
    try:
        panel.setAgents([_row("legacy", "python", 1)])
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        assert panel.btnRun.isEnabled()

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V4_ID))
        assert not panel.btnRun.isEnabled()
        assert panel.agentA.itemText(0) == "(none found)"
        assert panel.agentB.itemText(0) == "(none found)"
        assert "No compatible agents" in panel.rulesetExplanation.text()

        # Becoming idle must not quietly re-enable an impossible match.
        panel.setBusy(True)
        panel.setBusy(False)
        assert not panel.btnRun.isEnabled()

        panel.ruleset.setCurrentIndex(panel.ruleset.findData(BYTEFRAY_RULESET_V2_ID))
        assert panel.btnRun.isEnabled()
        assert panel.agentA.currentData() == "legacy"
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Simple (known-good reference: behavior must not change)
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.parametrize(
    ("ruleset_id", "expected_agents"),
    [
        (BYTEFRAY_RULESET_V2_ID, ["legacy"]),
        (BYTEFRAY_RULESET_V4_ID, ["proc"]),
    ],
)
def test_simple_still_filters_agents_by_the_selected_ruleset(
    ruleset_id, expected_agents
):
    """Simple's Ruleset-first UX is the reference this phase converged on;
    it must be unchanged by the shared-helper extraction."""

    _make_app()
    from app.views.simple import SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.ruleset.setCurrentIndex(panel.ruleset.findData(ruleset_id))
        listed = [panel.agentA.itemData(i) for i in range(panel.agentA.count())]
        assert listed == expected_agents
        assert panel.btnRun.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_simple_offers_current_gameplay_only_and_not_the_historical_v4_alphas():
    """Simple's policy since v3.0.0-alpha2 is one current Ruleset per Agent
    API generation. v4.0.0-rc1 Phase 2: the permanent stable identity now
    occupies that slot, and neither v4 alpha is offered here -- they are
    not removed from the product, only from the surface whose whole
    promise is the gameplay you get without thinking about it."""

    _make_app()
    from app.views.simple import SimplePanel

    panel = SimplePanel(catalog=None)
    try:
        offered = _offered(panel.ruleset)
        assert BYTEFRAY_RULESET_V4_ID in offered
        assert BYTEFRAY_RULESET_V4_ALPHA2_ID not in offered
        assert BYTEFRAY_RULESET_V4_ALPHA1_ID not in offered
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.parametrize(
    ("api_version", "expected_offered"),
    [
        (1, {BYTEFRAY_RULESET_V2_ID, BYTEFRAY_RULESET_ID}),
        (2, ALL_V4_IDENTITIES),
    ],
)
def test_development_offers_only_rulesets_the_selected_agent_can_run(
    api_version, expected_offered
):
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("probe", "python", api_version)])
        panel.selectAgent("probe")
        assert _offered(panel.rulesetCombo) == expected_offered
        assert panel.selected_ruleset_id() in expected_offered
        assert panel.btnTest.isEnabled()
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_keeps_listing_every_python_agent_regardless_of_api_version():
    """Only the Ruleset choices narrow: this tab must stay usable for
    historical Agent API v1 agents and current Agent API v2 ones alike."""

    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        listed = [panel.agentCombo.itemData(i) for i in range(panel.agentCombo.count())]
        assert listed == ["legacy", "proc"]
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_reapplies_compatibility_when_the_selection_changes():
    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.selectAgent("legacy")
        assert panel.selected_ruleset_id() == BYTEFRAY_RULESET_V2_ID

        panel.selectAgent("proc")
        assert panel.selected_ruleset_id() == BYTEFRAY_RULESET_V4_ID
        assert _offered(panel.rulesetCombo) == ALL_V4_IDENTITIES
    finally:
        panel.deleteLater()


@pytest.mark.gui
def test_development_disables_test_for_an_incompatible_explicit_opponent():
    """An explicitly chosen opponent is a real entrant, so a mixed Agent API
    pairing must fail closed in the UI -- the internal Reference opponent,
    which adapts to the resolved Ruleset, must not."""

    _make_app()
    from app.views.development import AgentDevelopmentPanel

    panel = AgentDevelopmentPanel()
    try:
        panel.setAgents([_row("legacy", "python", 1), _row("proc", "python", 2)])
        panel.selectAgent("proc")
        assert panel.selected_opponent_id() is None  # Reference
        assert panel.btnTest.isEnabled()

        panel.opponentCombo.setCurrentIndex(panel.opponentCombo.findData("legacy"))
        assert _offered(panel.rulesetCombo) == set()
        assert not panel.btnTest.isEnabled()

        # Returning to the adaptable Reference opponent restores it.
        panel.opponentCombo.setCurrentIndex(panel.opponentCombo.findData(None))
        assert panel.btnTest.isEnabled()
    finally:
        panel.deleteLater()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _evaluation_dialog(tmp_path, default_candidate, with_metadata=True):
    from app.views.evaluation import EvaluationDialog

    metadata = {
        "legacy": {"kind": "python", "api_version": 1},
        "proc": {"kind": "python", "api_version": 2},
    }
    return EvaluationDialog(
        [("legacy", "legacy"), ("proc", "proc")],
        default_candidate=default_candidate,
        default_output=tmp_path / "out",
        agent_metadata=metadata if with_metadata else None,
    )


@pytest.mark.gui
@pytest.mark.parametrize(
    ("candidate", "expected_offered"),
    [
        ("legacy", {BYTEFRAY_RULESET_V2_ID, BYTEFRAY_RULESET_ID}),
        # v4.0.0-rc1 Phase 2: all three v4 identities now, since `agents
        # evaluate` accepts alpha2/the stable identity under the stable v4
        # seeded-placement methodology, and alpha1 under its own historical
        # one -- see test_evaluation_defaults_to_stable_v4_for_api_v2_roster
        # below for which one is selected by default.
        ("proc", ALL_V4_IDENTITIES),
    ],
)
def test_evaluation_offers_only_rulesets_the_candidate_can_run(
    tmp_path, candidate, expected_offered
):
    _make_app()
    dialog = _evaluation_dialog(tmp_path, candidate)
    try:
        assert _offered(dialog.pairwiseRulesetCombo) == expected_offered
        assert dialog.pairwise_ruleset_id() in expected_offered
        assert dialog.runButton.isEnabled()
    finally:
        dialog.deleteLater()


@pytest.mark.gui
def test_evaluation_defaults_to_stable_v4_for_api_v2_roster(tmp_path):
    """An Agent API v2 candidate defaults to the permanent stable v4
    identity, not either prerelease alpha -- mirrors the engine's own
    OMITTED_RULESET_CANDIDATES product-preference order (v4.0.0-rc1
    Phase 2). alpha2/alpha1 remain selectable (see the ALL_V4_IDENTITIES
    offered-set test above) for reproducing an earlier prerelease
    evaluation."""

    _make_app()
    dialog = _evaluation_dialog(tmp_path, "proc")
    try:
        assert dialog.pairwise_ruleset_id() == BYTEFRAY_RULESET_V4_ID
    finally:
        dialog.deleteLater()


@pytest.mark.gui
def test_evaluation_evaluates_compatibility_across_the_whole_roster(tmp_path):
    """Not just the candidate: an incompatible opponent narrows the choices
    exactly as an incompatible candidate does."""

    from PySide6.QtCore import Qt

    _make_app()
    dialog = _evaluation_dialog(tmp_path, "proc")
    try:
        assert _offered(dialog.pairwiseRulesetCombo) == ALL_V4_IDENTITIES
        for index in range(dialog.opponentsList.count()):
            item = dialog.opponentsList.item(index)
            if item.data(Qt.UserRole) == "legacy":
                item.setSelected(True)
        assert _offered(dialog.pairwiseRulesetCombo) == set()
        assert not dialog.runButton.isEnabled()
    finally:
        dialog.deleteLater()


@pytest.mark.gui
def test_evaluation_without_supplied_metadata_keeps_previous_behavior(tmp_path):
    """A programmatic caller or test double that supplies no metadata must
    not have every Ruleset silently disabled by its absence."""

    _make_app()
    dialog = _evaluation_dialog(tmp_path, "proc", with_metadata=False)
    try:
        assert len(_offered(dialog.pairwiseRulesetCombo)) == dialog.pairwiseRulesetCombo.count()
        assert dialog.runButton.isEnabled()
    finally:
        dialog.deleteLater()
