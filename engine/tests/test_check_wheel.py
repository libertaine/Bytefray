"""Contract tests for ``tools/check_wheel.py``.

The synthetic wheels below carry this checkout's real ``battle_engine``
package modules -- so the checker imports real registries from them -- and the
real bundled bytes of every registered starter and template. The omission
cases are generated from those registries, so a newly registered starter or
template gets its own failure case without anyone editing this file -- the
property whose absence let the three V6 teaching agents ship without their
manifests (Pre-RC Remediation 02).
"""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path

import pytest
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION, TEMPLATE_FILES
from battle_engine.starters import STARTER_AGENT_NAMES, starter_content_files

from tools.check_wheel import EXPECTED_FILES, validate_wheel

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine" / "src" / "battle_engine"
STARTERS_MODULE = "battle_engine/starters.py"
SCAFFOLD_MODULE = "battle_engine/agent_scaffold.py"

SCRIPT_TARGETS = {
    "bytefray": "battle_engine.command:main",
    "bytefray-cli": "battle_engine.cli:main",
    "bytefray-agent-designer": "app.agent_designer:main",
    "bytefray-replay-viewer": "app.replay_viewer:main",
}


def _source(relative: str) -> str:
    # A Windows checkout may hold CRLF; the registry text edits below assume LF.
    return (ENGINE / relative).read_text(encoding="utf-8").replace("\r\n", "\n")


def _package_modules() -> dict[str, bytes]:
    """The real ``battle_engine`` code, so the checker can import its registries."""

    return {
        f"battle_engine/{path.relative_to(ENGINE).as_posix()}": path.read_bytes()
        for path in sorted(ENGINE.rglob("*.py"))
        if "__pycache__" not in path.parts and path.relative_to(ENGINE).parts[0] != "data"
    }


def _registered_resources() -> dict[str, bytes]:
    """Every file the runtime registries require, keyed by its wheel path."""

    files: dict[str, bytes] = {}
    for name in STARTER_AGENT_NAMES:
        agent_dir = (ENGINE / "data" / "starter_agents" / name).resolve()
        for path in starter_content_files(agent_dir):
            relative = path.relative_to(agent_dir).as_posix()
            files[f"battle_engine/data/starter_agents/{name}/{relative}"] = path.read_bytes()
    for directories in TEMPLATE_DIRECTORIES_BY_API_VERSION.values():
        for directory in directories.values():
            for filename in TEMPLATE_FILES:
                path = ENGINE / "data" / directory / filename
                files[f"battle_engine/data/{directory}/{filename}"] = path.read_bytes()
    return files


PACKAGE_MODULES = _package_modules()
REGISTERED_RESOURCES = _registered_resources()
TEMPLATE_COUNT = sum(len(templates) for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values())


def _wheel(
    tmp_path: Path,
    *,
    omit: frozenset[str] = frozenset(),
    replace: Mapping[str, bytes | str] | None = None,
    scripts: dict[str, str] | None = None,
    metadata_version: str = "5.0.0rc1",
) -> Path:
    wheel = tmp_path / "bytefray-5.0.0rc1-py3-none-any.whl"
    files: dict[str, bytes | str] = {name: b"" for name in EXPECTED_FILES}
    files.update(PACKAGE_MODULES)
    files.update(REGISTERED_RESOURCES)
    files.update(replace or {})
    for name in omit:
        del files[name]
    entry_points = "[console_scripts]\n" + "".join(
        f"{name} = {target}\n" for name, target in (scripts or SCRIPT_TARGETS).items()
    )
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
        archive.writestr("bytefray-5.0.0rc1.dist-info/entry_points.txt", entry_points)
        archive.writestr(
            "bytefray-5.0.0rc1.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: bytefray\nVersion: {metadata_version}\n",
        )
    return wheel


def _edited(module: str, old: str, new: str) -> dict[str, bytes | str]:
    source = _source(module)
    assert source.count(old) == 1, f"registry layout changed; update this test's anchor {old!r}"
    return {f"battle_engine/{module}": source.replace(old, new)}


def _appended(module: str, code: str) -> dict[str, bytes | str]:
    return {f"battle_engine/{module}": _source(module) + "\n\n" + code}


def test_registered_inventory_is_not_empty() -> None:
    """Guard the derivations above against silently shrinking to nothing."""

    assert STARTER_AGENT_NAMES and TEMPLATE_COUNT
    assert {"v6_window_scout", "v6_watchful_keeper", "v6_roaming_reacquirer"} <= set(
        STARTER_AGENT_NAMES
    )


def test_validator_accepts_a_wheel_shipping_every_registered_resource(tmp_path: Path) -> None:
    summary = validate_wheel(_wheel(tmp_path))

    assert summary.starters == STARTER_AGENT_NAMES
    assert len(summary.templates) == TEMPLATE_COUNT


def test_validator_accepts_crlf_resources_from_a_windows_checkout(tmp_path: Path) -> None:
    """The pinned digests normalize text line endings, exactly as the runtime does."""

    crlf = {
        name: content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        for name, content in REGISTERED_RESOURCES.items()
    }
    validate_wheel(_wheel(tmp_path, replace=crlf))


@pytest.mark.parametrize("missing", sorted(REGISTERED_RESOURCES))
def test_validator_rejects_any_missing_registered_resource(tmp_path: Path, missing: str) -> None:
    with pytest.raises(ValueError, match="registered agent resources") as failure:
        validate_wheel(_wheel(tmp_path, omit=frozenset({missing})))

    assert missing.split("/")[-2] in str(failure.value)


@pytest.mark.parametrize("missing", sorted(EXPECTED_FILES))
def test_validator_rejects_a_missing_package_marker_or_branding(
    tmp_path: Path, missing: str
) -> None:
    with pytest.raises(ValueError, match="missing expected files"):
        validate_wheel(_wheel(tmp_path, omit=frozenset({missing})))


def test_a_newly_registered_starter_is_required_without_editing_the_checker(
    tmp_path: Path,
) -> None:
    """Registering a starter that packaging does not ship must fail the wheel."""

    registry = _edited(
        "starters.py",
        "STARTER_AGENT_NAMES = (\n",
        'STARTER_AGENT_NAMES = (\n    "v9_unpackaged",\n',
    )

    with pytest.raises(ValueError, match="registered agent resources") as failure:
        validate_wheel(_wheel(tmp_path, replace=registry))

    message = str(failure.value)
    assert "starter_agents/v9_unpackaged/agent.yaml" in message
    assert "'v9_unpackaged': no pinned digest" in message


def test_a_newly_registered_template_is_required_without_editing_the_checker(
    tmp_path: Path,
) -> None:
    registry = _edited(
        "agent_scaffold.py",
        "TEMPLATE_DIRECTORIES = {\n",
        'TEMPLATE_DIRECTORIES = {\n    "v9_template": "agent_template_v9",\n',
    )

    with pytest.raises(ValueError, match="registered agent resources") as failure:
        validate_wheel(_wheel(tmp_path, replace=registry))

    assert "battle_engine/data/agent_template_v9/agent.yaml" in str(failure.value)


@pytest.mark.parametrize(
    ("module", "code", "expected"),
    [
        (
            "starters.py",
            'STARTER_AGENT_NAMES += ("v9_late",)\n',
            "starter_agents/v9_late/agent.yaml",
        ),
        (
            "agent_scaffold.py",
            'if True:\n    TEMPLATE_DIRECTORIES["extra"] = "agent_template_extra"\n',
            "data/agent_template_extra/agent.yaml",
        ),
        (
            "agent_scaffold.py",
            (
                "def _register_late() -> None:\n"
                '    TEMPLATE_DIRECTORIES_BY_API_VERSION[2]["late"] = "agent_template_late"\n'
                "\n\n_register_late()\n"
            ),
            "data/agent_template_late/agent.yaml",
        ),
    ],
    ids=["augmented-roster", "conditional-template", "registered-by-call"],
)
def test_registrations_made_while_the_registry_imports_are_required(
    tmp_path: Path, module: str, code: str, expected: str
) -> None:
    """The checker sees the registry the runtime builds, however it is built."""

    with pytest.raises(ValueError, match="registered agent resources") as failure:
        validate_wheel(_wheel(tmp_path, replace=_appended(module, code)))

    assert expected in str(failure.value)


def test_a_computed_registry_is_read_as_the_runtime_computes_it(tmp_path: Path) -> None:
    registry = _appended("starters.py", "STARTER_AGENT_NAMES = tuple(sorted(STARTER_AGENT_NAMES))\n")

    summary = validate_wheel(_wheel(tmp_path, replace=registry))

    assert summary.starters == tuple(sorted(STARTER_AGENT_NAMES))


@pytest.mark.parametrize(
    "unloadable",
    [
        {STARTERS_MODULE: "STARTER_AGENT_NAMES = (\n"},
        {SCAFFOLD_MODULE: "raise RuntimeError('registry failed to import')\n"},
    ],
    ids=["syntax-error", "import-error"],
)
def test_validator_rejects_registries_that_cannot_load(
    tmp_path: Path, unloadable: dict[str, str]
) -> None:
    with pytest.raises(ValueError, match="Cannot load the wheel's starter/template registries"):
        validate_wheel(_wheel(tmp_path, replace=unloadable))


@pytest.mark.parametrize("module", [STARTERS_MODULE, SCAFFOLD_MODULE])
def test_validator_rejects_a_wheel_without_its_registry_module(
    tmp_path: Path, module: str
) -> None:
    with pytest.raises(ValueError, match="Cannot load the wheel's starter/template registries"):
        validate_wheel(_wheel(tmp_path, omit=frozenset({module})))


@pytest.mark.parametrize(
    "extra",
    [
        "battle_engine/data/starter_agents/v6_unregistered/agent.py",
        "battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.py",
        "battle_engine/data/teaching_fixtures/v6_stationary_opponent/agent.yaml",
        "battle_engine/data/research/notes.json",
    ],
)
def test_validator_rejects_unregistered_agent_resources(tmp_path: Path, extra: str) -> None:
    with pytest.raises(ValueError, match="outside every registered"):
        validate_wheel(_wheel(tmp_path, replace={extra: b"x"}))


def test_validator_rejects_modified_bundled_starter_content(tmp_path: Path) -> None:
    path = "battle_engine/data/starter_agents/v6_window_scout/agent.py"

    with pytest.raises(ValueError, match="does not match the pinned"):
        validate_wheel(_wheel(tmp_path, replace={path: REGISTERED_RESOURCES[path] + b"\n# x\n"}))


def test_validator_rejects_a_manifest_naming_another_agent(tmp_path: Path) -> None:
    path = "battle_engine/data/starter_agents/v6_watchful_keeper/agent.yaml"
    manifest = REGISTERED_RESOURCES[path].replace(
        b'"name": "v6_watchful_keeper"', b'"name": "someone_else"'
    )
    assert manifest != REGISTERED_RESOURCES[path]

    with pytest.raises(ValueError, match="declares name 'someone_else'"):
        validate_wheel(_wheel(tmp_path, replace={path: manifest}))


@pytest.mark.parametrize(
    "retired",
    [
        "battle_engine/instructions.py",
        "battle_engine/data/agent_template/agent.py",
        "battle_engine/data/benchmarks/v2_baseline.json",
        "battle_engine/data/reference_agents/core_seeker/agent.py",
        "battle_engine/data/v3_closeout_agents/turtle_core_refresher/agent.py",
        "battle_engine/data/v3_phase7_agents/core_tracker_offset/agent.py",
        "battle_engine/data/starter_agents/claimer/agent.py",
    ],
)
def test_validator_rejects_retired_execution_resources(
    tmp_path: Path, retired: str
) -> None:
    wheel = _wheel(tmp_path)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr(retired, b"")

    with pytest.raises(ValueError, match="retired execution resources"):
        validate_wheel(wheel)


def test_validator_rejects_a_misdirected_console_script(tmp_path: Path) -> None:
    scripts = dict(SCRIPT_TARGETS)
    scripts["bytefray"] = "battle_engine.cli:main"

    with pytest.raises(ValueError, match="console script targets"):
        validate_wheel(_wheel(tmp_path, scripts=scripts))


def test_validator_rejects_metadata_version_disagreement(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="metadata version"):
        validate_wheel(_wheel(tmp_path, metadata_version="5.0.0a1"))
