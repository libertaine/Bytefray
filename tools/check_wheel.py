"""Validate the release-critical contents of a Bytefray wheel.

Starter agents and scaffold templates are deliberately not listed here. The
required set comes from the runtime registries the wheel itself ships --
``battle_engine.starters`` and ``battle_engine.agent_scaffold`` -- so a newly
registered starter or template is required automatically, and a wheel whose
packaging rules omit one fails instead of passing a stale hand-kept list.

The registries are imported from the extracted wheel in a separate isolated
interpreter (``-I``), never from this checkout, so the checker sees exactly the
values an installed runtime sees, however they are computed. Starter content is
compared against the runtime's own pinned digests using the wheel's own
``starter_content_digest``. Those modules import only the standard library, so
this works in a build environment where nothing but the wheel is available.
"""

from __future__ import annotations

import argparse
import configparser
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path
from typing import Any

EXPECTED_FILES = {
    "app/__init__.py",
    "battle_client/__init__.py",
    "battle_engine/__init__.py",
    "app/assets/branding/bytefray-icon.png",
}

DATA_PREFIX = "battle_engine/data/"
STARTER_PREFIX = f"{DATA_PREFIX}starter_agents/"

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

# Runs in the isolated interpreter with the extracted wheel first on sys.path.
_REGISTRY_PROBE = r"""
import json, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from battle_engine import agent_scaffold, starters

for module in (starters, agent_scaffold):
    origin = Path(module.__file__).resolve()
    if root not in origin.parents:
        raise SystemExit(f"{module.__name__} resolved outside the wheel: {origin}")
agents = root / "battle_engine" / "data" / "starter_agents"
print(json.dumps({
    "starters": list(starters.STARTER_AGENT_NAMES),
    "pinned": dict(starters.CURRENT_STARTER_DIGESTS),
    "shipped": {
        name: starters.starter_content_digest(agents / name)
        for name in starters.STARTER_AGENT_NAMES
    },
    "template_files": list(agent_scaffold.TEMPLATE_FILES),
    "templates": [
        [api_version, template, directory]
        for api_version, templates in sorted(agent_scaffold.TEMPLATE_DIRECTORIES_BY_API_VERSION.items())
        for template, directory in sorted(templates.items())
    ],
}))
"""


@dataclass(frozen=True)
class WheelSummary:
    """The registered resources a validated wheel was checked against."""

    starters: tuple[str, ...]
    templates: tuple[str, ...]


def _load_registries(archive: zipfile.ZipFile) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix="bytefray-check-wheel-", ignore_cleanup_errors=True
    ) as extracted:
        archive.extractall(extracted)
        probe = subprocess.run(
            [sys.executable, "-I", "-B", "-c", _REGISTRY_PROBE, extracted],
            cwd=extracted,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    if probe.returncode != 0:
        raise ValueError(
            "Cannot load the wheel's starter/template registries "
            f"(battle_engine.starters, battle_engine.agent_scaffold):\n{probe.stderr.strip()}"
        )
    registries: dict[str, Any] = json.loads(probe.stdout)
    return registries


def _manifest_problems(name: str, files: dict[str, bytes]) -> list[str]:
    prefix = f"{STARTER_PREFIX}{name}/"
    if "agent.yaml" not in files:
        return [f"starter {name!r}: missing {prefix}agent.yaml"]
    try:
        manifest = json.loads(files["agent.yaml"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"starter {name!r}: unreadable {prefix}agent.yaml ({exc})"]
    if not isinstance(manifest, dict):
        return [f"starter {name!r}: {prefix}agent.yaml is not a JSON object"]
    problems = []
    if manifest.get("name") != name:
        problems.append(f"starter {name!r}: agent.yaml declares name {manifest.get('name')!r}")
    entrypoint = manifest.get("entrypoint")
    source = entrypoint.split(":", 1)[0] if isinstance(entrypoint, str) else ""
    if not source or source not in files:
        problems.append(
            f"starter {name!r}: missing implementation {prefix}{source or '?'} "
            f"for entrypoint {entrypoint!r}"
        )
    return problems


def _validate_registered_resources(archive: zipfile.ZipFile, names: set[str]) -> WheelSummary:
    """Every registered starter and template ships complete, and nothing else does."""

    registries = _load_registries(archive)
    starters: tuple[str, ...] = tuple(registries["starters"])
    pinned: dict[str, str] = registries["pinned"]
    shipped: dict[str, str | None] = registries["shipped"]
    template_files: list[str] = registries["template_files"]
    templates: list[list[Any]] = registries["templates"]
    if not starters or not templates or not template_files:
        raise ValueError(f"The wheel's registries are empty: {registries}")

    problems: list[str] = []
    allowed_prefixes: set[str] = set()
    for name in starters:
        prefix = f"{STARTER_PREFIX}{name}/"
        allowed_prefixes.add(prefix)
        files = {
            entry[len(prefix):]: archive.read(entry)
            for entry in names
            if entry.startswith(prefix) and not entry.endswith("/")
        }
        problems.extend(_manifest_problems(name, files))
        if name not in pinned:
            problems.append(f"starter {name!r}: no pinned digest in CURRENT_STARTER_DIGESTS")
        elif files and shipped.get(name) != pinned[name]:
            problems.append(
                f"starter {name!r}: shipped content digest {shipped.get(name)} does not match "
                f"the pinned {pinned[name]} (shipped files: {sorted(files)})"
            )

    labels: list[str] = []
    for api_version, template, directory in templates:
        labels.append(f"{template} (Agent API v{api_version})")
        prefix = f"{DATA_PREFIX}{directory}/"
        allowed_prefixes.add(prefix)
        problems.extend(
            f"template {template!r} (Agent API v{api_version}): missing {prefix}{filename}"
            for filename in template_files
            if f"{prefix}{filename}" not in names
        )
    if problems:
        raise ValueError(
            "Wheel does not ship the registered agent resources:\n  - " + "\n  - ".join(problems)
        )

    unregistered = sorted(
        entry
        for entry in names
        if entry.startswith(DATA_PREFIX)
        and not entry.endswith("/")
        and not entry.startswith(tuple(allowed_prefixes))
    )
    if unregistered:
        raise ValueError(
            "Wheel contains agent resources outside every registered starter and "
            f"template directory: {unregistered}"
        )
    return WheelSummary(starters=starters, templates=tuple(labels))


def _wheel_version(wheel: Path) -> str:
    parts = wheel.name.split("-")
    if len(parts) < 5 or parts[0].replace("_", "-").casefold() != "bytefray":
        raise ValueError(f"Wheel filename does not identify Bytefray: {wheel.name}")
    return parts[1]


def validate_wheel(wheel: Path) -> WheelSummary:
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

        summary = _validate_registered_resources(archive, names)

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
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    arguments = parser.parse_args()
    summary = validate_wheel(arguments.wheel)
    print(f"Validated wheel contents: {arguments.wheel}")
    print(f"  starters ({len(summary.starters)}): {', '.join(summary.starters)}")
    print(f"  templates ({len(summary.templates)}): {', '.join(summary.templates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
