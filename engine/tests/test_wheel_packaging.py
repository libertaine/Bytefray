"""Built-wheel regression for the bundled agent resources (Pre-RC Remediation 02).

A source checkout and an editable install resolve starter agents and scaffold
templates from the repository tree, so neither can notice a resource the wheel
leaves out. That is how the three V6 teaching agents passed every source-tree
test while their wheel shipped ``agent.py`` without ``agent.yaml``: bootstrap
reported them missing, discovery could not list them, and ``agents create
--template window_scout`` failed with exit 2.

The artifact tests here build a real wheel from this checkout's packaged
sources -- or take a prebuilt one through ``BYTEFRAY_WHEEL``, mirroring
``BYTEFRAY_FROZEN_EXE`` -- and assert against that artifact. Every expectation
is derived from the runtime registries (``STARTER_AGENT_NAMES`` and
``TEMPLATE_DIRECTORIES_BY_API_VERSION``), so a newly registered starter or
template is covered without editing this file.
"""

from __future__ import annotations

import fnmatch
import glob
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION, TEMPLATE_FILES
from battle_engine.starters import STARTER_AGENT_NAMES, starter_content_files

from tools.check_wheel import validate_wheel

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine" / "src" / "battle_engine"
WHEEL_ENV_VAR = "BYTEFRAY_WHEEL"
# What a wheel build reads; everything else in the checkout is irrelevant to it.
BUILD_INPUTS = ("pyproject.toml", "MANIFEST.in", "README.md", "LICENSE", "engine/src", "client/src", "app")
TEMPLATE_IDS = sorted(
    (api_version, template)
    for api_version, templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.items()
    for template in templates
)


def _registered_directories() -> dict[str, Path]:
    """Each registered resource directory, as ``data/...`` relative to the package."""

    directories = {
        f"data/starter_agents/{name}": ENGINE / "data" / "starter_agents" / name
        for name in STARTER_AGENT_NAMES
    }
    for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values():
        for directory in templates.values():
            directories[f"data/{directory}"] = ENGINE / "data" / directory
    return directories


def _registered_resources() -> dict[str, Path]:
    """Every file the registries require, as ``data/...`` relative to the package."""

    resources: dict[str, Path] = {}
    for name in STARTER_AGENT_NAMES:
        agent_dir = (ENGINE / "data" / "starter_agents" / name).resolve()
        for path in starter_content_files(agent_dir):
            resources[f"data/starter_agents/{name}/{path.relative_to(agent_dir).as_posix()}"] = path
    for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values():
        for directory in templates.values():
            for filename in TEMPLATE_FILES:
                resources[f"data/{directory}/{filename}"] = ENGINE / "data" / directory / filename
    return resources


def _text(content: bytes) -> bytes:
    return content.replace(b"\r\n", b"\n")


# --------------------------------------------------------------------------
# Packaging configuration (fast, no build)
# --------------------------------------------------------------------------


def test_package_data_patterns_select_every_registered_resource() -> None:
    """Evaluate ``pyproject.toml``'s package-data globs the way setuptools does.

    An early warning that does not need a build backend: a starter registered
    without a matching pattern fails here, naming the files the wheel would
    lose. The artifact tests below remain the authoritative check.
    """

    tomllib = pytest.importorskip("tomllib")
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools_config = config["tool"]["setuptools"]
    excluded = [
        pattern
        for patterns in setuptools_config.get("exclude-package-data", {}).values()
        for pattern in patterns
    ]
    selected: set[str] = set()
    for pattern in setuptools_config["package-data"]["battle_engine"]:
        for match in glob.glob(str(ENGINE / pattern), recursive=True):
            path = Path(match)
            relative = path.relative_to(ENGINE).as_posix()
            if path.is_file() and not any(
                fnmatch.fnmatch(relative, rule) or fnmatch.fnmatch(path.name, rule)
                for rule in excluded
            ):
                selected.add(relative)

    missing = sorted(set(_registered_resources()) - selected)
    assert not missing, f"no battle_engine package-data pattern selects {missing}"

    # Resources must ship through package-data alone. Namespace-package
    # discovery of battle_engine/data is what made the V6 omission partial
    # (agent.py shipped as a module, agent.yaml did not) and what shipped
    # retired research agents.
    excluded_packages = set(setuptools_config["packages"]["find"].get("exclude", ()))
    assert {"battle_engine.data", "battle_engine.data.*"} <= excluded_packages


# --------------------------------------------------------------------------
# The built artifact
# --------------------------------------------------------------------------


def _setuptools_can_build() -> str | None:
    """Why the current interpreter cannot build the wheel offline, if it cannot."""

    try:
        import setuptools
    except ImportError:
        return "setuptools is not installed"
    version = tuple(int(part) for part in setuptools.__version__.split(".")[:2] if part.isdigit())
    if version < (69,):
        return f"pyproject.toml requires setuptools>=69, found {setuptools.__version__}"
    if version < (70, 1):
        try:
            import wheel  # noqa: F401
        except ImportError:
            return f"setuptools {setuptools.__version__} needs the 'wheel' package"
    return None


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A wheel built from this checkout, or the one ``BYTEFRAY_WHEEL`` names.

    The build uses a copy of the tracked and untracked-but-not-ignored build
    inputs, so ignored debris (bytecode, egg-info, prior ``build/``) cannot
    influence it, and it runs the interpreter's own setuptools without
    network access or build isolation.
    """

    configured = os.environ.get(WHEEL_ENV_VAR, "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            pytest.fail(f"{WHEEL_ENV_VAR}={configured!r} is not an existing file")
        return path.resolve()

    reason = _setuptools_can_build()
    if reason:
        pytest.skip(f"cannot build the wheel offline ({reason}); set {WHEEL_ENV_VAR}")
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *BUILD_INPUTS],
            cwd=ROOT,
            capture_output=True,
            check=True,
            timeout=60,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        pytest.skip(f"copying the build inputs needs a git checkout; set {WHEEL_ENV_VAR}")

    source = tmp_path_factory.mktemp("wheel-source")
    for raw in filter(None, listing.split(b"\0")):
        relative = raw.decode("utf-8")
        if (ROOT / relative).is_file():  # skips deleted-but-unstaged entries
            (source / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, source / relative)

    output = tmp_path_factory.mktemp("wheel-dist")
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    built = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; from setuptools import build_meta; build_meta.build_wheel(sys.argv[1])",
            str(output),
        ],
        cwd=source,
        env=environment,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert built.returncode == 0, f"wheel build failed\n{built.stdout}\n{built.stderr}"
    wheels = sorted(output.glob("*.whl"))
    assert len(wheels) == 1, wheels
    return wheels[0]


def test_built_wheel_passes_the_release_checker(built_wheel: Path) -> None:
    summary = validate_wheel(built_wheel)

    assert summary.starters == STARTER_AGENT_NAMES
    assert len(summary.templates) == len(TEMPLATE_IDS)


def test_built_wheel_ships_every_registered_resource_exactly(built_wheel: Path) -> None:
    """Each registered directory ships exactly its source files, byte for byte.

    Independent of the checker's own registry parsing: the expectation comes
    from this checkout's imported registries and files.
    """

    with zipfile.ZipFile(built_wheel) as archive:
        names = set(archive.namelist())
        problems: list[str] = []
        for relative, source in sorted(_registered_resources().items()):
            entry = f"battle_engine/{relative}"
            if entry not in names:
                problems.append(f"missing {entry}")
            elif _text(archive.read(entry)) != _text(source.read_bytes()):
                problems.append(f"differs from source: {entry}")
        for name in STARTER_AGENT_NAMES:
            prefix = f"battle_engine/data/starter_agents/{name}/"
            agent_dir = (ENGINE / "data" / "starter_agents" / name).resolve()
            shipped = {entry[len(prefix):] for entry in names if entry.startswith(prefix)}
            expected = {path.relative_to(agent_dir).as_posix() for path in starter_content_files(agent_dir)}
            if shipped != expected:
                problems.append(f"{name}: ships {sorted(shipped)}, source has {sorted(expected)}")
    assert not problems, "\n".join(problems)


def test_built_wheel_ships_no_agent_resources_outside_the_registry(built_wheel: Path) -> None:
    allowed = tuple(f"battle_engine/{directory}/" for directory in _registered_directories())
    with zipfile.ZipFile(built_wheel) as archive:
        stray = sorted(
            entry
            for entry in archive.namelist()
            if entry.startswith("battle_engine/data/") and not entry.startswith(allowed)
        )
    assert not stray, f"teaching fixtures, research data or unregistered agents shipped: {stray}"


@pytest.mark.parametrize("name", STARTER_AGENT_NAMES)
def test_checker_fails_the_real_wheel_without_one_starter_manifest(
    built_wheel: Path, tmp_path: Path, name: str
) -> None:
    omitted = f"battle_engine/data/starter_agents/{name}/agent.yaml"
    damaged = tmp_path / built_wheel.name
    with zipfile.ZipFile(built_wheel) as source, zipfile.ZipFile(damaged, "w") as target:
        assert omitted in source.namelist()
        for item in source.infolist():
            if item.filename != omitted:
                target.writestr(item, source.read(item))

    with pytest.raises(ValueError, match="registered agent resources") as failure:
        validate_wheel(damaged)
    assert omitted in str(failure.value)


_INSTALLED_LAYOUT_PROBE = r"""
import importlib.metadata
import json
import sys
from pathlib import Path

site, deps, data, forbidden = sys.argv[1], sys.argv[2], Path(sys.argv[3]), json.loads(sys.argv[4])
sys.path[:0] = [site, deps]

import battle_engine
from battle_engine import paths
from battle_engine.agent_api import load_python_agent
from battle_engine.agent_capabilities import parse_required_capabilities
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION, create_agent
from battle_engine.agents import discover_agents
from battle_engine.starters import (
    CURRENT_STARTER_DIGESTS,
    STARTER_AGENT_NAMES,
    ensure_starter_agents,
    starter_content_digest,
)

checkout = paths._source_checkout_root()
bootstrap = ensure_starter_agents(data_root=data)
created = []
for api_version, templates in sorted(TEMPLATE_DIRECTORIES_BY_API_VERSION.items()):
    for template in sorted(templates):
        agent_id = f"probe_api{api_version}_{template}"
        create_agent(agent_id, data_root=data, template=template, api_version=api_version)
        created.append(agent_id)
specs = discover_agents(data)
loaded = {name: load_python_agent(spec).metadata.api_version for name, spec in sorted(specs.items())}
foreign = sorted(
    module.__file__
    for module in list(sys.modules.values())
    if getattr(module, "__file__", None)
    and any(Path(module.__file__).resolve().is_relative_to(root) for root in forbidden)
)
print(json.dumps({
    "battle_engine": str(Path(battle_engine.__file__).resolve()),
    "resource_root": str(paths.get_resource_root()),
    "checkout_root": None if checkout is None else str(checkout),
    "version": importlib.metadata.version("bytefray"),
    "starters": list(STARTER_AGENT_NAMES),
    "bootstrap_errors": [[error.name, error.message] for error in bootstrap.errors],
    "digest_mismatches": sorted(
        name for name in STARTER_AGENT_NAMES
        if starter_content_digest(data / "agents" / name) != CURRENT_STARTER_DIGESTS[name]
    ),
    "created": created,
    "loaded_api_versions": loaded,
    "required_capabilities": {
        name: sorted(parse_required_capabilities(spec.manifest)) for name, spec in sorted(specs.items())
    },
    "foreign_modules": foreign,
}))
"""


def test_installed_wheel_layout_resolves_every_resource_without_a_checkout(
    built_wheel: Path, tmp_path: Path
) -> None:
    """Bootstrap, discover, scaffold and load from the wheel's files alone.

    The wheel is unpacked the way an installer lays out a pure wheel, then
    exercised in an interpreter started with ``-I -S``: no ``PYTHONPATH``, no
    site-packages and therefore no editable-install finder, no current
    directory -- only the stdlib, the unpacked wheel and a private copy of
    PyYAML. Any module that still resolves from this checkout's source roots
    fails the test.
    """

    import yaml

    site = tmp_path / "site"
    deps = tmp_path / "deps"
    data = tmp_path / "data"
    with zipfile.ZipFile(built_wheel) as archive:
        archive.extractall(site)
    shutil.copytree(
        Path(yaml.__file__).parent,
        deps / "yaml",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    source_roots = [str(ENGINE.parent), str(ROOT / "client" / "src"), str(ROOT / "app")]
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "BYTEFRAY_ROOT"}
    }
    probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            _INSTALLED_LAYOUT_PROBE,
            str(site),
            str(deps),
            str(data),
            json.dumps(source_roots),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert probe.returncode == 0, f"installed-layout probe failed\n{probe.stdout}\n{probe.stderr}"
    report = json.loads(probe.stdout)

    assert Path(report["battle_engine"]).is_relative_to(site.resolve())
    assert Path(report["resource_root"]) == site.resolve()
    assert report["checkout_root"] is None
    assert report["foreign_modules"] == []
    assert report["starters"] == list(STARTER_AGENT_NAMES)
    assert report["bootstrap_errors"] == []
    assert report["digest_mismatches"] == []
    assert set(report["loaded_api_versions"]) == set(STARTER_AGENT_NAMES) | set(report["created"])
    assert set(report["loaded_api_versions"].values()) == {2}
    assert len(report["created"]) == len(TEMPLATE_IDS)
    # A personal copy keeps its starter's capability contract, which is what
    # makes Active Sensing (Alpha) an explicit Ruleset selection for it.
    for api_version, template in TEMPLATE_IDS:
        directory = TEMPLATE_DIRECTORIES_BY_API_VERSION[api_version][template]
        if directory.startswith("starter_agents/"):
            starter = directory.split("/", 1)[1]
            copy = f"probe_api{api_version}_{template}"
            assert report["required_capabilities"][copy] == report["required_capabilities"][starter]
