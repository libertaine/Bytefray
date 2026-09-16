"""V5 Alpha 1 Phase E -- the Qt-free half of the Designer's parameter layer.

Everything the Agent Designer decides about parameters and seeds is decided
here, in ``app.services.designer_workflows``, so it can be asserted without a
display. The widgets in ``app/widgets/agent_parameters.py`` render these
answers; they do not compute them.

The rule this module exists to hold: **the Designer implements no parameter
semantics of its own.** Coercion, bounds, unknown-key policy and the
``defaults < preset < overrides`` precedence rule all belong to Phase D's
``agent_parameters.resolve_parameters``, and every function here routes
through it.
"""

from __future__ import annotations

import pytest
from battle_engine.agent_parameters import (
    EMPTY_PARAMETER_SCHEMA,
    parse_parameter_schema,
    resolve_parameters,
)
from battle_engine.starters import ensure_starter_agents

from app.services.agent_catalog import AgentCatalog, AgentRow
from app.services.designer_workflows import (
    DesignerValidationError,
    agent_parameter_schema,
    agent_receives_parameters,
    describe_effective_parameters,
    parameter_launch_overrides,
    random_match_seed,
    resolve_agent_parameters,
    validate_entrant_parameters,
)

SCHEMA_BODY = {
    "reach": {"type": "integer", "default": 16, "minimum": 10, "maximum": 64},
    "share": {"type": "number", "default": 0.5, "minimum": 0.0, "maximum": 1.0},
    "mode": {"type": "choice", "default": "sweep", "choices": ["sweep", "hold"]},
}
PRESETS = {"aggressive": {"values": {"reach": 48, "mode": "hold"}}}


def _schema(body=None, presets=None):
    manifest: dict = {"api_version": 2, "parameters": body or SCHEMA_BODY}
    if presets is not None:
        manifest["presets"] = presets
    return parse_parameter_schema(manifest)


def _row(name="agent", api_version=2, schema=None, kind="python"):
    meta: dict[str, object] = {"name": name, "kind": kind}
    if api_version is not None:
        meta["api_version"] = api_version
    return AgentRow(
        name,
        f"/agents/{name}",
        None,
        meta,
        agent_id=name,
        parameter_schema=schema if schema is not None else EMPTY_PARAMETER_SCHEMA,
    )


# ---------------------------------------------------------------------------
# The catalog carries the parsed schema
# ---------------------------------------------------------------------------


def test_the_catalog_carries_each_agents_parsed_schema(tmp_path):
    """The Designer must read the parsed model the engine already built, not
    re-interpret the raw manifest -- two parsers is two answers."""

    ensure_starter_agents(data_root=tmp_path)

    rows = {row.agent_id: row for row in AgentCatalog(tmp_path).list_agents()}

    attacker = agent_parameter_schema(rows["v5_region_attacker"])
    assert attacker.declaration_order() == ("attacker_reach",)
    assert attacker.parameters["attacker_reach"].minimum == 10
    assert "far_sighted" in attacker.preset_names()
    # Every historical starter stays schema-less, so the Designer keeps
    # showing it the free-form surface it has always had.
    assert agent_parameter_schema(rows["v4_scout"]).is_empty
    assert agent_parameter_schema(rows["runner"]).is_empty


def test_a_row_built_without_a_schema_still_answers(tmp_path):
    """Rows are constructed positionally in older tests and by callers that
    predate this field; asking one what it exposes must never raise."""

    legacy = AgentRow("x", "/agents/x", None, {"name": "x"}, agent_id="x")

    assert agent_parameter_schema(legacy) is EMPTY_PARAMETER_SCHEMA


# ---------------------------------------------------------------------------
# Resolution goes through the canonical resolver
# ---------------------------------------------------------------------------


def test_resolution_matches_the_canonical_resolver_exactly():
    schema = _schema(presets=PRESETS)

    assert resolve_agent_parameters(schema, preset="aggressive", overrides={"reach": 20}) == (
        resolve_parameters(schema, preset="aggressive", overrides={"reach": 20})
    )


def test_precedence_is_defaults_then_preset_then_overrides():
    schema = _schema(presets=PRESETS)

    assert resolve_agent_parameters(schema) == {"reach": 16, "share": 0.5, "mode": "sweep"}
    assert resolve_agent_parameters(schema, preset="aggressive") == {
        "reach": 48,
        "share": 0.5,
        "mode": "hold",
    }
    assert resolve_agent_parameters(
        schema, preset="aggressive", overrides={"reach": 20}
    ) == {"reach": 20, "share": 0.5, "mode": "hold"}


def test_only_non_default_values_are_exported_to_the_match():
    schema = _schema(presets=PRESETS)

    assert parameter_launch_overrides(schema, resolve_agent_parameters(schema)) == {}
    assert parameter_launch_overrides(
        schema, resolve_agent_parameters(schema, preset="aggressive")
    ) == {"reach": 48, "mode": "hold"}


def test_exported_overrides_reproduce_the_same_effective_values():
    """The property that makes exporting only the differences safe: the child
    CLI applies the same schema's defaults underneath them, so a partial
    export and the full effective set resolve identically."""

    schema = _schema(presets=PRESETS)
    effective = resolve_agent_parameters(schema, preset="aggressive", overrides={"share": 0.25})

    exported = parameter_launch_overrides(schema, effective)

    assert resolve_parameters(schema, overrides=exported) == effective


def test_effective_values_are_described_in_declaration_order():
    schema = _schema()

    text = describe_effective_parameters(resolve_agent_parameters(schema))

    assert text == "reach=16, share=0.5, mode='sweep'"


# ---------------------------------------------------------------------------
# The launch gate
# ---------------------------------------------------------------------------


def test_an_unknown_parameter_key_is_refused_before_launch():
    row = _row(schema=_schema())

    with pytest.raises(DesignerValidationError, match="Unknown parameter 'nonsense'"):
        validate_entrant_parameters(row, {"nonsense": 1}, slot="A")


def test_an_out_of_range_value_is_refused_before_launch():
    row = _row(schema=_schema())

    with pytest.raises(DesignerValidationError, match="below the declared minimum"):
        validate_entrant_parameters(row, {"reach": 2}, slot="B")


def test_the_slot_letter_is_named_so_the_user_knows_which_agent():
    row = _row(schema=_schema())

    with pytest.raises(DesignerValidationError, match=r"^Agent C: "):
        validate_entrant_parameters(row, {"reach": 999}, slot="C")


def test_a_valid_selection_passes_the_gate():
    row = _row(schema=_schema())

    validate_entrant_parameters(row, {"reach": 32, "mode": "hold"}, slot="A")


def test_no_parameters_at_all_is_always_accepted():
    validate_entrant_parameters(_row(schema=_schema()), None, slot="A")
    validate_entrant_parameters(_row(schema=_schema()), {}, slot="A")


# ---------------------------------------------------------------------------
# Legacy and Agent API v1 compatibility
# ---------------------------------------------------------------------------


def test_agent_api_v1_free_form_parameters_stay_a_harmless_no_op():
    """The Phase D regression, guarded at the Designer boundary too.

    Advanced has always exported its Agent Params field for whatever agent is
    selected, and an Agent API v1 agent has always ignored it. ``cli.py``
    warns and ignores; rejecting here would break a working user path to
    enforce a rule that arrived after it.
    """

    v1 = _row(api_version=1)

    assert not agent_receives_parameters(v1)
    validate_entrant_parameters(v1, {"anything": "at all"}, slot="A")


def test_a_vm_agent_with_free_form_parameters_is_not_rejected():
    vm = _row(kind="vm", api_version=None)

    validate_entrant_parameters(vm, {"byte": 1, "ptr": 4}, slot="B")


def test_an_api_v2_agent_without_a_schema_keeps_free_form_passthrough():
    """The six ``v4_*`` starters are Agent API v2 and declare no parameters.
    Phase D's resolver treats an empty schema as the historical unvalidated
    path, and the Designer must not be stricter than the engine."""

    v2_no_schema = _row(api_version=2)

    assert agent_receives_parameters(v2_no_schema)
    validate_entrant_parameters(v2_no_schema, {"undeclared": 1}, slot="A")


# ---------------------------------------------------------------------------
# The real starters, end to end through the service layer
# ---------------------------------------------------------------------------


def test_the_shipped_starters_resolve_their_declared_presets(tmp_path):
    ensure_starter_agents(data_root=tmp_path)
    rows = {row.agent_id: row for row in AgentCatalog(tmp_path).list_agents()}

    attacker = agent_parameter_schema(rows["v5_region_attacker"])

    assert resolve_agent_parameters(attacker) == {"attacker_reach": 16}
    assert resolve_agent_parameters(attacker, preset="standard") == {"attacker_reach": 16}
    assert resolve_agent_parameters(attacker, preset="far_sighted") == {"attacker_reach": 32}
    # The 'standard' preset resolves to exactly the declared defaults, so
    # selecting it exports nothing and cannot move a match identity.
    assert parameter_launch_overrides(
        attacker, resolve_agent_parameters(attacker, preset="standard")
    ) == {}


def test_an_unknown_preset_for_a_shipped_starter_is_refused(tmp_path):
    ensure_starter_agents(data_root=tmp_path)
    rows = {row.agent_id: row for row in AgentCatalog(tmp_path).list_agents()}

    with pytest.raises(Exception, match="Unknown parameter preset"):
        resolve_agent_parameters(
            agent_parameter_schema(rows["v5_core_defender"]), preset="nope"
        )


# ---------------------------------------------------------------------------
# E2 -- seed generation
# ---------------------------------------------------------------------------


def test_a_generated_seed_lies_inside_the_requested_range():
    assert all(1 <= random_match_seed(1, 10) <= 10 for _ in range(200))


def test_a_generated_seed_is_never_the_engine_default_sentinel():
    """Advanced reads 0 as "use the engine's own default seed", so a
    randomizer that can return 0 sometimes means the opposite of randomizing.
    """

    assert all(random_match_seed() != 0 for _ in range(500))


def test_a_single_value_range_is_legal_and_deterministic():
    assert random_match_seed(7, 7) == 7


def test_an_empty_range_is_refused_rather_than_silently_reordered():
    with pytest.raises(ValueError, match="Seed range is empty"):
        random_match_seed(10, 1)


def test_generation_spans_its_range_rather_than_returning_one_value():
    assert len({random_match_seed(1, 1_000_000) for _ in range(100)}) > 1


# ---------------------------------------------------------------------------
# E4 -- effective parameters survive into the result presentation
# ---------------------------------------------------------------------------


def _write_result(path, entrants):
    """A minimal but real ``battle2.result`` envelope.

    Built through the engine's own writer rather than by hand, so these tests
    exercise the same reader path the product does and cannot drift from the
    result schema.
    """

    from battle_engine.result_model import ResultEnvelope, write_json_atomic

    write_json_atomic(
        path,
        ResultEnvelope(
            result_id="r",
            match_id="m",
            mode="process",
            winner="A",
            termination_reason="ticks",
            ticks=10,
            entrants=tuple(entrants),
        ).as_dict(),
    )


def test_recorded_parameters_reach_the_results_presentation(tmp_path):
    from app.services.designer_workflows import read_match_presentation

    result_path = tmp_path / "result.json"
    _write_result(
        result_path,
        [
            {
                "agent_id": "A",
                "name": "v5_region_attacker",
                "alive": True,
                "score": 12.0,
                "metadata": {"api_version": 2, "parameters": {"attacker_reach": 32}},
            }
        ],
    )

    presentation = read_match_presentation(result_path)

    assert presentation.entrants[0].parameters == {"attacker_reach": 32}


def test_a_result_written_before_phase_d_still_opens(tmp_path):
    """No replay or result schema changed for this, so every pre-existing
    artifact must read back with an empty parameter mapping rather than
    failing or inventing one."""

    from app.services.designer_workflows import read_match_presentation

    result_path = tmp_path / "result.json"
    _write_result(
        result_path,
        [
            {
                "agent_id": "A",
                "name": "claimer",
                "alive": True,
                "score": 5.0,
                "metadata": {"api_version": 1, "entry_point": "agent.py:create_agent"},
            },
            {"agent_id": "B", "name": "writer", "alive": False, "score": 1.0},
        ],
    )

    presentation = read_match_presentation(result_path)

    assert presentation.entrants[0].parameters == {}
    assert presentation.entrants[1].parameters == {}


def test_a_malformed_parameters_block_is_ignored_rather_than_fatal(tmp_path):
    from app.services.designer_workflows import read_match_presentation

    result_path = tmp_path / "result.json"
    _write_result(
        result_path,
        [
            {
                "agent_id": "A",
                "name": "odd",
                "alive": True,
                "score": 0.0,
                "metadata": {"parameters": ["not", "a", "mapping"]},
            }
        ],
    )

    assert read_match_presentation(result_path).entrants[0].parameters == {}
