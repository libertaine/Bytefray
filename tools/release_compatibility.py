"""Check a release compatibility record against the code and render its summary.

A record under ``docs/releases/*_COMPATIBILITY.json`` is the single
authoritative declaration of which component versions an application release
ships (see docs/COMPONENT_VERSIONING.md). This tool checks every claim in it
that the code can confirm -- Ruleset exposure per surface, display names,
Agent API and format versions, the Spectator presentation contract -- and
renders the Markdown summary between the GENERATED markers of the companion
``.md`` file, so the record and its documentation cannot silently disagree.

    python tools/release_compatibility.py docs/releases/<record>.json --check
    python tools/release_compatibility.py docs/releases/<record>.json --write
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_SCHEMA = ("bytefray.release_compatibility", 1)
BEGIN_MARKER = "<!-- BEGIN GENERATED: tools/release_compatibility.py -->"
END_MARKER = "<!-- END GENERATED -->"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)\.(\d+))?$")
PEP440_PRERELEASE = {"alpha": "a", "beta": "b", "rc": "rc"}


def load_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def companion_markdown(record_path: Path) -> Path:
    return record_path.with_suffix(".md")


def python_package_version(version: str) -> str:
    """``5.1.0-alpha.1`` -> ``5.1.0a1`` (the PEP 440 form packaging writes)."""

    match = SEMVER.match(version)
    if match is None:
        raise ValueError(f"not a supported application version: {version!r}")
    major, minor, patch, stage, number = match.groups()
    suffix = "" if stage is None else f"{PEP440_PRERELEASE[stage]}{number}"
    return f"{major}.{minor}.{patch}{suffix}"


def _accepted(parse: Any, candidates: Iterable[str]) -> list[str]:
    accepted = []
    for candidate in candidates:
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                parse(candidate)
            except SystemExit:
                continue
        accepted.append(candidate)
    return sorted(accepted)


def _choices(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if "--ruleset" in action.option_strings:
            return set(action.choices or ())
    raise AssertionError(f"{parser.prog} has no --ruleset option")


def surface_rulesets() -> dict[str, list[str]]:
    """Every executable Ruleset each product surface actually accepts."""

    from battle_engine import agent_test, agent_validation, cli, evaluation_cli, tournament_cli
    from battle_engine import ruleset_policy as rp

    from app.services import ruleset_options as options

    # Historical identities are candidates too: accepting one would be a defect.
    candidates = sorted(
        set(rp._RULESET_POLICIES) | rp.HISTORICAL_READONLY_RULESET_IDS | {"bytefray-rules-1"}
    )

    def ids(chosen: Iterable[Any]) -> list[str]:
        return [option.ruleset_id for option in chosen]

    return {
        "bytefray run": _accepted(lambda value: cli.parse_args(["--ruleset", value]), candidates),
        "bytefray agents test": sorted(_choices(agent_test._parser())),
        "bytefray agents validate": sorted(_choices(agent_validation._parser())),
        "bytefray agents evaluate": sorted(_choices(evaluation_cli._parser())),
        "bytefray tournament": sorted(_choices(tournament_cli._parser())),
        "Designer Simple": ids(options.SIMPLE_RULESET_OPTIONS),
        # Advanced and Development both populate from the default option set.
        "Designer Advanced": ids(options.DESIGNER_RULESET_OPTIONS),
        "Designer Development": ids(options.DESIGNER_RULESET_OPTIONS),
        "Designer Evaluation": ids(options.EVALUATION_RULESET_OPTIONS),
    }


def runtime_problems(record: dict[str, Any]) -> list[str]:
    """Every claim in ``record`` the code contradicts (empty when consistent)."""

    from battle_client import spectator_export as spectator
    from battle_engine import (
        agent_api,
        agent_package,
        agent_trace,
        evaluation_contracts,
        replay,
        result_model,
        tournament_service,
    )
    from battle_engine import ruleset_policy as rp
    from battle_engine.agent_capabilities import KNOWN_CAPABILITIES
    from battle_engine.project_info import get_project_info
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
    from battle_engine.ruleset_names import RULESET_DISPLAY_NAMES

    from app.services.ruleset_options import DEFAULT_DESIGNER_RULESET_ID

    problems: list[str] = []

    def expect(label: str, declared: object, actual: object) -> None:
        if declared != actual:
            problems.append(f"{label}: record says {declared!r}, code has {actual!r}")

    expect("record schema", (record.get("schema"), record.get("schema_version")), RECORD_SCHEMA)
    app = record["application"]
    try:
        expect("python_package_version", app["python_package_version"], python_package_version(app["version"]))
    except ValueError as exc:
        problems.append(str(exc))
    expect("git_tag", app["git_tag"], f"v{app['version']}")
    classifiers = re.findall(
        r'"Programming Language :: Python :: (3\.\d+)"',
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    expect("python", app["python"], classifiers)

    rulesets = record["rulesets"]
    product = rp.PUBLIC_STABLE_RULESET_IDS | rp.PUBLIC_EXPERIMENTAL_RULESET_IDS
    expect("default ruleset (omitted --ruleset)", rulesets["default"], rp.OMITTED_RULESET_CANDIDATES[0])
    expect("default ruleset (Designer)", rulesets["default"], DEFAULT_DESIGNER_RULESET_ID)
    offered = {entry["id"]: entry for entry in rulesets["offered"]}
    expect("offered rulesets", set(offered), product)
    for ruleset_id, entry in offered.items():
        expect(f"{ruleset_id} display name", entry["display_name"], RULESET_DISPLAY_NAMES.get(ruleset_id))
        stability = "stable" if ruleset_id in rp.PUBLIC_STABLE_RULESET_IDS else "experimental"
        expect(f"{ruleset_id} stability", entry["stability"], stability)
    research = rp.ACTIVE_RESEARCH_RULESET_IDS | rp.RETIRED_RESEARCH_RULESET_IDS
    actual_surfaces = surface_rulesets()
    expect("surfaces", set(rulesets["surfaces"]), set(actual_surfaces))
    for surface, actual in actual_surfaces.items():
        declared = rulesets["surfaces"].get(surface)
        expect(f"{surface} rulesets", declared, sorted(set(actual) & product))
        if surface != "bytefray agents evaluate":
            expect(f"{surface} research exposure", [], sorted(set(actual) & research))
    evaluate_research = set(actual_surfaces["bytefray agents evaluate"]) - product
    expect("research rulesets selectable by evaluate", evaluate_research, research)
    expect("research ruleset count", rulesets["research_only"]["count"], len(research))
    historical = rulesets["historical_readable_not_executable"]
    expect("historical rulesets", set(historical), rp.HISTORICAL_READONLY_RULESET_IDS | {"bytefray-rules-1"})
    for ruleset_id in historical:
        try:
            rp.resolve_ruleset_policy(ruleset_id)
        except rp.UnknownRulesetError:
            continue
        problems.append(f"{ruleset_id} is declared historical but is executable")

    api = record["agent_api"]
    expect("agent_api executable", set(api["executable"]), set(agent_api.SUPPORTED_AGENT_API_VERSIONS))
    expect("agent_api current", agent_api.AGENT_API_VERSION in api["executable"], True)
    expect("capabilities known", set(api["manifest_capabilities"]["known"]), set(KNOWN_CAPABILITIES))

    formats = record["formats"]
    expect(
        "replay",
        formats["replay"],
        {"schema": replay.SCHEMA_NAME, "writes": replay.SCHEMA_VERSION, "reads": list(replay.SUPPORTED_SCHEMA_VERSIONS)},
    )
    expect(
        "result",
        formats["result"],
        {
            "schema": result_model.SCHEMA_NAME,
            "writes": result_model.SCHEMA_VERSION,
            "reads": list(result_model.SUPPORTED_SCHEMA_VERSIONS),
        },
    )
    expect(
        "trace",
        formats["trace"],
        {
            "schema": agent_trace.TRACE_SCHEMA,
            "writes": agent_trace.TRACE_SCHEMA_VERSION_V2,
            "reads": [agent_trace.TRACE_SCHEMA_VERSION, agent_trace.TRACE_SCHEMA_VERSION_V2],
        },
    )
    expect(
        "evaluation",
        formats["evaluation"],
        {"schema": evaluation_contracts.SCHEMA_NAME, "writes": evaluation_contracts.SCHEMA_VERSION},
    )
    expect(
        "tournament",
        formats["tournament"],
        {"schema": tournament_service.SCHEMA_NAME, "writes": tournament_service.SCHEMA_VERSION},
    )
    expect(
        "agent_package",
        formats["agent_package"],
        {"schema": agent_package.PACKAGE_SCHEMA, "writes": agent_package.PACKAGE_SCHEMA_VERSION},
    )
    info = get_project_info()
    expect("bytefray --version Agent API", info.agent_api_version, agent_api.AGENT_API_VERSION)
    expect("bytefray --version result schema", info.result_schema_version, formats["result"]["writes"])
    expect("bytefray --version replay schema", info.replay_schema_version, formats["replay"]["writes"])

    protocol = record["spectator"]["presentation_protocol"]
    expect("manifest schema", protocol["manifest_schema"], spectator.MANIFEST_SCHEMA)
    expect("manifest version written", protocol["bytefray_writes"], spectator.MANIFEST_SCHEMA_VERSION)
    expect("Spectator reads what Bytefray writes", protocol["bytefray_writes"] in protocol["spectator_reads"], True)
    expect("provenance", protocol["provenance"], spectator.PROVENANCE)
    expect(
        "presentation documents",
        protocol["documents"],
        {
            key: {"schema": schema, "schema_version": spectator.DOCUMENT_SCHEMA_VERSION}
            for key, schema in spectator.DOCUMENT_SCHEMAS.items()
        },
    )
    matches = record["spectator"]["supported_matches"]
    expect("Spectator rulesets", matches["rulesets"], [BYTEFRAY_RULESET_V6_ALPHA1_ID])
    expect("Spectator entrants", matches["entrants"], list(spectator.SUPPORTED_ENTRANTS))
    expect("Spectator perspectives", matches["perspectives"], list(spectator.PRESENTATION_FILES))
    return problems


def _ids(values: Iterable[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def _ruleset(entry: dict[str, Any]) -> str:
    return f"{entry['display_name']} (`{entry['id']}`)"


def render_markdown(record: dict[str, Any]) -> str:
    """The generated summary block (without its markers)."""

    app = record["application"]
    rulesets = record["rulesets"]
    offered = {entry["id"]: entry for entry in rulesets["offered"]}
    api = record["agent_api"]
    formats = record["formats"]
    spectator = record["spectator"]
    protocol = spectator["presentation_protocol"]
    source = spectator["application"]["compatible_development_source"]
    matches = spectator["supported_matches"]

    def fmt(name: str) -> str:
        entry = formats[name]
        reads = entry.get("reads")
        text = f"`{entry['schema']}` writes {entry['writes']}"
        return text if reads is None else f"{text}; reads {', '.join(str(v) for v in reads)}"

    def joined(values: Iterable[object], prefix: str = "") -> str:
        return ", ".join(f"{prefix}{value}" for value in values)

    research = rulesets["research_only"]
    capabilities = api["manifest_capabilities"]
    distribution = spectator["application"]["distribution"]
    launch = spectator["designer_launch"]
    application = (
        f"{app['name']} {app['version']} (Python package `{app['python_package_version']}`, "
        f"tag `{app['git_tag']}`); previous release {app['previous_release']}; "
        f"Python {joined(app['python'])}"
    )
    offered_text = "; ".join(
        f"{_ruleset(entry)} — {entry['stability']}, {entry['selection']}" for entry in rulesets["offered"]
    )
    research_text = f"{research['count']}, selectable only by {research['selection']}. {research['promise']}"
    agent_api_text = (
        f"{joined(api['executable'], 'v')} executable; "
        f"{joined(api['retired_from_execution'], 'v')} retired from execution; "
        f"manifest capabilities v{capabilities['version']} ({_ids(capabilities['known'])})"
    )
    spectator_text = (
        f"{spectator['application']['release_status']}. Compatible development source: "
        f"`{source['repository']}` `{source['branch']}` `{source['commit'][:7]}`. "
        f"{distribution[0].upper()}{distribution[1:]}"
    )
    documents = joined(
        f"{key} `{doc['schema']}` v{doc['schema_version']}" for key, doc in protocol["documents"].items()
    )
    protocol_text = (
        f"`{protocol['manifest_schema']}`: Bytefray writes {protocol['bytefray_writes']}, "
        f"Spectator reads {joined(protocol['spectator_reads'])}; provenance "
        f"`{protocol['provenance']}`; documents {documents}"
    )
    match_text = (
        f"{_ids(matches['rulesets'])} with entrants {joined(matches['entrants'])}; "
        f"perspectives {joined(matches['perspectives'])}"
    )
    dispatch_text = (
        f"Prefers Spectator: {joined(launch['prefers_spectator'])}. "
        f"Always Pygame: {joined(launch['always_pygame'])}"
    )
    rows = [
        ("Status", f"**{record['status']}** — {record['status_note']}"),
        ("Application", application),
        ("Default Ruleset", _ruleset(offered[rulesets["default"]])),
        ("Offered Rulesets", offered_text),
        ("Research Rulesets", research_text),
        ("Historical Rulesets (readable, not executable)", _ids(rulesets["historical_readable_not_executable"])),
        ("Agent API", agent_api_text),
        ("Replay format", fmt("replay")),
        ("Result format", fmt("result")),
        ("Trace format", fmt("trace")),
        ("Other persisted formats", "; ".join(fmt(name) for name in ("evaluation", "tournament", "agent_package"))),
        ("Spectator application", spectator_text),
        ("Spectator presentation protocol", protocol_text),
        ("Spectator match support", match_text),
        ("Designer viewer dispatch", dispatch_text),
    ]
    lines = ["| Component | Declaration |", "| --- | --- |"]
    lines += [f"| {name} | {value} |" for name, value in rows]
    lines += ["", "| Surface | Rulesets offered for new matches |", "| --- | --- |"]
    for surface, ids in rulesets["surfaces"].items():
        lines.append(f"| {surface} | {'; '.join(_ruleset(offered[i]) for i in ids)} |")
    lines += ["", "| Platform | Bytefray | Spectator |", "| --- | --- | --- |"]
    lines += [f"| {p['platform']} | {p['bytefray']} | {p['spectator']} |" for p in record["platforms"]]
    lines += ["", "**Known limitations**", ""]
    lines += [f"- {item}" for item in record["limitations"]]
    lines += ["", "**Unsupported**", ""]
    lines += [f"- {item}" for item in record["unsupported"]]
    return "\n".join(lines) + "\n"


def generated_block(markdown: str) -> str | None:
    start = markdown.find(BEGIN_MARKER)
    end = markdown.find(END_MARKER)
    if start < 0 or end < start:
        return None
    return markdown[start + len(BEGIN_MARKER) : end].strip("\n") + "\n"


def write_block(markdown: str, block: str) -> str:
    start = markdown.index(BEGIN_MARKER) + len(BEGIN_MARKER)
    end = markdown.index(END_MARKER)
    return f"{markdown[:start]}\n{block}{markdown[end:]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("record", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if the record or its summary is stale")
    mode.add_argument("--write", action="store_true", help="regenerate the summary block")
    args = parser.parse_args(argv)
    record = load_record(args.record)
    problems = runtime_problems(record)
    markdown_path = companion_markdown(args.record)
    markdown = markdown_path.read_text(encoding="utf-8")
    block = render_markdown(record)
    if args.write:
        markdown_path.write_bytes(write_block(markdown, block).encode("utf-8"))
    elif generated_block(markdown) != block:
        problems.append(f"{markdown_path.name}: generated summary is stale; rerun with --write")
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
