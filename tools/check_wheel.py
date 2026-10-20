"""Validate the release-critical contents of a Bytefray wheel.

Starter agents and scaffold templates are deliberately not listed here. The
required set is read from the runtime registries the wheel itself ships --
``battle_engine.starters`` and ``battle_engine.agent_scaffold`` -- so a newly
registered starter or template is required automatically, and a wheel whose
packaging rules omit one fails instead of passing a stale hand-kept list. The
registries are parsed, not imported: validation never executes code from the
artifact under inspection and needs none of its runtime dependencies.
"""

from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path, PurePosixPath

EXPECTED_FILES = {
    "app/__init__.py",
    "battle_client/__init__.py",
    "battle_engine/__init__.py",
    "app/assets/branding/bytefray-icon.png",
}

STARTER_REGISTRY_MODULE = "battle_engine/starters.py"
TEMPLATE_REGISTRY_MODULE = "battle_engine/agent_scaffold.py"
DATA_PREFIX = "battle_engine/data/"
STARTER_PREFIX = f"{DATA_PREFIX}starter_agents/"

# The battle_engine.starters.starter_content_digest scheme this checker
# reproduces. A wheel recording another version fails loudly rather than being
# compared under the wrong rules.
STARTER_CONTENT_DIGEST_VERSION = 1

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


@dataclass(frozen=True)
class WheelSummary:
    """The registered resources a validated wheel was checked against."""

    starters: tuple[str, ...]
    templates: tuple[str, ...]


class _NotLiteral(Exception):
    pass


def _literal(node: ast.expr, scope: Mapping[str, object]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_literal(item, scope) for item in node.elts)
    if isinstance(node, ast.List):
        return [_literal(item, scope) for item in node.elts]
    if isinstance(node, ast.Set):
        return {_literal(item, scope) for item in node.elts}
    if isinstance(node, ast.Dict):
        result: dict[object, object] = {}
        for key, value in zip(node.keys, node.values):
            if key is None:  # ``**mapping`` unpacking
                raise _NotLiteral
            result[_literal(key, scope)] = _literal(value, scope)
        return result
    if isinstance(node, ast.Name) and node.id in scope:
        return scope[node.id]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        and len(node.args) == 1
        and not node.keywords
    ):
        items = _literal(node.args[0], scope)
        if isinstance(items, (set, tuple, list)):
            return frozenset(items)
    raise _NotLiteral


def _module_literals(source: str) -> dict[str, object]:
    """Module-level names bound to literal values, in definition order.

    A name later rebound to something non-literal, or mutated in place at
    module level, is dropped rather than kept at its earlier value -- together
    with every name whose value was built from it, since the runtime shares
    that object -- so a registry this parser cannot read reliably is reported
    as unreadable instead of being read stale.
    """

    scope: dict[str, object] = {}
    uses: dict[str, set[str]] = {}

    def drop(name: str) -> None:
        if name in scope:
            del scope[name]
            for other, used in uses.items():
                if name in used:
                    drop(other)

    for statement in ast.parse(source).body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign):
            targets, value = list(statement.targets), statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, value = [statement.target], statement.value
        elif isinstance(statement, ast.AugAssign):
            targets = [statement.target]
        elif (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
        ):
            targets = [statement.value.func.value]
        for target in targets:
            base = target
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if not isinstance(base, ast.Name):
                continue
            if base is target and value is not None:
                try:
                    literal = _literal(value, scope)
                except _NotLiteral:
                    pass
                else:
                    drop(base.id)
                    scope[base.id] = literal
                    uses[base.id] = {
                        node.id for node in ast.walk(value) if isinstance(node, ast.Name)
                    }
                    continue
            drop(base.id)
    return scope


class _Registry:
    """Typed access to one registry module's literal bindings in the wheel."""

    def __init__(self, archive: zipfile.ZipFile, module: str) -> None:
        try:
            source = archive.read(module).decode("utf-8")
        except KeyError:
            raise ValueError(f"Wheel is missing its registry module {module}") from None
        try:
            self.scope = _module_literals(source)
        except SyntaxError as exc:
            raise ValueError(f"Cannot parse registry module {module} in the wheel: {exc}") from None
        self.module = module

    def value(self, name: str) -> object:
        if name not in self.scope:
            raise ValueError(
                f"Cannot read {name} as a literal from {self.module} in the wheel; keep "
                "it a literal or update tools/check_wheel.py"
            )
        return self.scope[name]

    def names(self, name: str) -> tuple[str, ...]:
        value = self.value(name)
        if not (
            isinstance(value, tuple)
            and value
            and all(isinstance(item, str) for item in value)
            and len(set(value)) == len(value)
        ):
            raise ValueError(f"{name} in {self.module} is not a non-empty unique name tuple")
        return value

    def suffixes(self, name: str) -> frozenset[str]:
        value = self.value(name)
        if not (isinstance(value, frozenset) and all(isinstance(item, str) for item in value)):
            raise ValueError(f"{name} in {self.module} is not a frozenset of suffixes")
        return value

    def string_map(self, name: str, value: object | None = None) -> dict[str, str]:
        value = self.value(name) if value is None else value
        if not (
            isinstance(value, dict)
            and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items())
        ):
            raise ValueError(f"{name} in {self.module} is not a string-to-string mapping")
        return value


def _starter_digest(
    files: Mapping[str, bytes],
    *,
    text_suffixes: frozenset[str],
    bytecode_suffixes: frozenset[str],
) -> str:
    """Reproduce ``battle_engine.starters.starter_content_digest`` over wheel entries."""

    hasher = hashlib.sha256()
    hasher.update(str(STARTER_CONTENT_DIGEST_VERSION).encode("ascii"))
    for relative in sorted(files):
        path = PurePosixPath(relative)
        if any(part.lower() == "__pycache__" for part in path.parts):
            continue
        if path.suffix.lower() in bytecode_suffixes:
            continue
        content = files[relative]
        if path.suffix.lower() in text_suffixes:
            content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        hasher.update(b"\0")
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(hashlib.sha256(content).digest())
    return hasher.hexdigest()


def _starter_problems(
    name: str, files: Mapping[str, bytes], pinned: str | None, starters: _Registry
) -> list[str]:
    prefix = f"{STARTER_PREFIX}{name}/"
    problems: list[str] = []
    manifest: object = None
    if "agent.yaml" not in files:
        problems.append(f"starter {name!r}: missing {prefix}agent.yaml")
    else:
        try:
            manifest = json.loads(files["agent.yaml"].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            problems.append(f"starter {name!r}: unreadable {prefix}agent.yaml ({exc})")
        else:
            if not isinstance(manifest, dict):
                problems.append(f"starter {name!r}: {prefix}agent.yaml is not a JSON object")
    if isinstance(manifest, dict):
        if manifest.get("name") != name:
            problems.append(
                f"starter {name!r}: agent.yaml declares name {manifest.get('name')!r}"
            )
        entrypoint = manifest.get("entrypoint")
        source = entrypoint.split(":", 1)[0] if isinstance(entrypoint, str) else ""
        if not source or source not in files:
            problems.append(
                f"starter {name!r}: missing implementation {prefix}{source or '?'} "
                f"for entrypoint {entrypoint!r}"
            )
    if pinned is None:
        problems.append(f"starter {name!r}: no pinned digest in CURRENT_STARTER_DIGESTS")
    elif files:
        actual = _starter_digest(
            files,
            text_suffixes=starters.suffixes("_TEXT_SUFFIXES"),
            bytecode_suffixes=starters.suffixes("_BYTECODE_SUFFIXES"),
        )
        if actual != pinned:
            problems.append(
                f"starter {name!r}: shipped content digest {actual} does not match the "
                f"pinned {pinned} (shipped files: {sorted(files)})"
            )
    return problems


def _validate_registered_resources(archive: zipfile.ZipFile, names: set[str]) -> WheelSummary:
    """Every registered starter and template ships complete, and nothing else does."""

    starters = _Registry(archive, STARTER_REGISTRY_MODULE)
    starter_names = starters.names("STARTER_AGENT_NAMES")
    pins = starters.string_map("CURRENT_STARTER_DIGESTS")
    digest_version = starters.value("STARTER_CONTENT_DIGEST_VERSION")
    if digest_version != STARTER_CONTENT_DIGEST_VERSION:
        raise ValueError(
            f"Wheel uses starter content digest version {digest_version!r}; this checker "
            f"implements version {STARTER_CONTENT_DIGEST_VERSION}"
        )

    scaffold = _Registry(archive, TEMPLATE_REGISTRY_MODULE)
    template_files = scaffold.names("TEMPLATE_FILES")
    templates_by_api = scaffold.value("TEMPLATE_DIRECTORIES_BY_API_VERSION")
    if not (isinstance(templates_by_api, dict) and templates_by_api):
        raise ValueError("TEMPLATE_DIRECTORIES_BY_API_VERSION is not a non-empty mapping")

    problems: list[str] = []
    allowed_prefixes: set[str] = set()
    for name in starter_names:
        prefix = f"{STARTER_PREFIX}{name}/"
        allowed_prefixes.add(prefix)
        files = {
            entry[len(prefix):]: archive.read(entry)
            for entry in names
            if entry.startswith(prefix) and not entry.endswith("/")
        }
        problems.extend(_starter_problems(name, files, pins.get(name), starters))

    template_labels: list[str] = []
    for api_version, directories in sorted(templates_by_api.items()):
        mapping = scaffold.string_map("TEMPLATE_DIRECTORIES_BY_API_VERSION", directories)
        if not mapping:
            raise ValueError(f"Agent API v{api_version} declares no scaffold templates")
        for template, directory in sorted(mapping.items()):
            template_labels.append(f"{template} (Agent API v{api_version})")
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
    return WheelSummary(starters=starter_names, templates=tuple(template_labels))


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
