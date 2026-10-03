"""Validate the release-critical contents of a Bytefray wheel."""

from __future__ import annotations

import argparse
import configparser
import io
import zipfile
from email.parser import Parser
from pathlib import Path

EXPECTED_FILES = {
    "app/__init__.py",
    "battle_client/__init__.py",
    "battle_engine/__init__.py",
    # The only executable starter population: Agent API v2 agents for the
    # stable Ruleset 4 runtime.
    "battle_engine/data/starter_agents/v4_claimer/agent.yaml",
    "battle_engine/data/starter_agents/v4_claimer/agent.py",
    "battle_engine/data/starter_agents/v4_concentrated_attacker/agent.yaml",
    "battle_engine/data/starter_agents/v4_concentrated_attacker/agent.py",
    "battle_engine/data/starter_agents/v4_defender_scout/agent.yaml",
    "battle_engine/data/starter_agents/v4_defender_scout/agent.py",
    "battle_engine/data/starter_agents/v4_local_defender/agent.yaml",
    "battle_engine/data/starter_agents/v4_local_defender/agent.py",
    "battle_engine/data/starter_agents/v4_quorum/agent.yaml",
    "battle_engine/data/starter_agents/v4_quorum/agent.py",
    "battle_engine/data/starter_agents/v4_scout/agent.yaml",
    "battle_engine/data/starter_agents/v4_scout/agent.py",
    # Agent API v2 educational ladder added in v5.0.0a1 (V5 Alpha 1 Phase C).
    "battle_engine/data/starter_agents/v5_region_attacker/agent.yaml",
    "battle_engine/data/starter_agents/v5_region_attacker/agent.py",
    "battle_engine/data/starter_agents/v5_scout_striker/agent.yaml",
    "battle_engine/data/starter_agents/v5_scout_striker/agent.py",
    "battle_engine/data/starter_agents/v5_core_defender/agent.yaml",
    "battle_engine/data/starter_agents/v5_core_defender/agent.py",
    "battle_engine/data/starter_agents/v5_dual_team/agent.yaml",
    "battle_engine/data/starter_agents/v5_dual_team/agent.py",
    "battle_engine/data/agent_template_v2/agent.yaml",
    "battle_engine/data/agent_template_v2/agent.py",
    "battle_engine/data/agent_template_v2_annotated/agent.yaml",
    "battle_engine/data/agent_template_v2_annotated/agent.py",
    "app/assets/branding/bytefray-icon.png",
}

# Phase 2B.12 removes these execution resources from distributable payloads,
# rather than merely unregistering them at runtime.
FORBIDDEN_FILES = {
    "battle_engine/builtins/__init__.py",
    "battle_engine/builtins/registry.py",
    "battle_engine/instructions.py",
    "battle_engine/match.py",
    "battle_engine/reference_agents.py",
    "battle_engine/data/agent_template/agent.py",
    "battle_engine/data/agent_template/agent.yaml",
    "battle_engine/data/agent_template_annotated/agent.py",
    "battle_engine/data/agent_template_annotated/agent.yaml",
}
FORBIDDEN_PREFIXES = (
    "battle_engine/data/benchmarks/",
    "battle_engine/data/reference_agents/",
    "battle_engine/data/v3_closeout_agents/",
    "battle_engine/data/v3_phase7_agents/",
)
FORBIDDEN_STARTER_IDS = frozenset(
    {
        "adaptive",
        "claimer",
        "hunter",
        "raider",
        "runner",
        "seeker",
        "sentinel",
        "spiral",
        "strider",
        "wanderer",
        "writer",
    }
)
EXPECTED_SCRIPTS = {
    "bytefray": "battle_engine.command:main",
    "bytefray-cli": "battle_engine.cli:main",
    "bytefray-agent-designer": "app.agent_designer:main",
    "bytefray-replay-viewer": "app.replay_viewer:main",
}
# V6 retired the pMARS integration entirely (docs/research/v6's Phase 2B.6
# retirement report); this guard is kept permanently as a negative
# anti-regression check now that nothing is allow-listed.
ALLOWED_PMARS_PATHS: frozenset[str] = frozenset()


def _wheel_version(wheel: Path) -> str:
    parts = wheel.name.split("-")
    if len(parts) < 5 or parts[0].replace("_", "-").casefold() != "bytefray":
        raise ValueError(f"Wheel filename does not identify Bytefray: {wheel.name}")
    return parts[1]


def validate_wheel(wheel: Path) -> None:
    wheel_version = _wheel_version(wheel)
    dist_info = f"bytefray-{wheel_version}.dist-info"
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        missing_files = sorted(EXPECTED_FILES - names)
        if missing_files:
            raise ValueError(f"Wheel is missing expected files: {missing_files}")

        forbidden_files = sorted(
            name
            for name in names
            if name in FORBIDDEN_FILES
            or name.startswith(FORBIDDEN_PREFIXES)
            or (
                name.startswith("battle_engine/data/starter_agents/")
                and name.split("/", 4)[3] in FORBIDDEN_STARTER_IDS
            )
        )
        if forbidden_files:
            raise ValueError(
                "Wheel contains retired execution resources: "
                f"{forbidden_files}"
            )

        unexpected_pmars = sorted(
            name
            for name in names
            if "pmars" in name.casefold() and name not in ALLOWED_PMARS_PATHS
        )
        if unexpected_pmars:
            raise ValueError(
                "Wheel unexpectedly contains pMARS distribution material: "
                f"{unexpected_pmars}"
            )

        stray_bytecode = sorted(
            name for name in names if "__pycache__" in name or name.endswith(".pyc")
        )
        if stray_bytecode:
            raise ValueError(
                f"Wheel unexpectedly contains compiled bytecode/cache: {stray_bytecode}"
            )

        entry_points_name = f"{dist_info}/entry_points.txt"
        if entry_points_name not in names:
            raise ValueError("Wheel is missing dist-info/entry_points.txt")
        parser = configparser.ConfigParser()
        parser.read_file(io.StringIO(archive.read(entry_points_name).decode("utf-8")))
        if not parser.has_section("console_scripts"):
            raise ValueError("Wheel is missing the console_scripts entry-point group")
        scripts = {name: target.strip() for name, target in parser["console_scripts"].items()}
        missing_scripts = sorted(EXPECTED_SCRIPTS.keys() - scripts.keys())
        if missing_scripts:
            raise ValueError(f"Wheel is missing console scripts: {missing_scripts}")
        wrong_targets = {
            name: {"expected": target, "actual": scripts.get(name)}
            for name, target in EXPECTED_SCRIPTS.items()
            if scripts.get(name) != target
        }
        if wrong_targets:
            raise ValueError(f"Wheel has incorrect console script targets: {wrong_targets}")

        metadata_name = f"{dist_info}/METADATA"
        if metadata_name not in names:
            raise ValueError("Wheel is missing dist-info/METADATA")
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        if metadata.get("Name", "").casefold() != "bytefray":
            raise ValueError(f"Wheel metadata name is not Bytefray: {metadata.get('Name')!r}")
        if metadata.get("Version") != wheel_version:
            raise ValueError(
                "Wheel metadata version does not match its filename: "
                f"{metadata.get('Version')!r} != {wheel_version!r}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    arguments = parser.parse_args()
    validate_wheel(arguments.wheel)
    print(f"Validated wheel contents: {arguments.wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
