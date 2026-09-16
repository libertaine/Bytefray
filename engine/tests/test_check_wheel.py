from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from tools.check_wheel import EXPECTED_FILES, validate_wheel

SCRIPT_TARGETS = {
    "bytefray": "battle_engine.command:main",
    "bytefray-cli": "battle_engine.cli:main",
    "bytefray-agent-designer": "app.agent_designer:main",
    "bytefray-replay-viewer": "app.replay_viewer:main",
}
ADDITIONAL_RUNTIME_FILES = {
    "app/assets/branding/bytefray-icon.png",
    "battle_engine/data/agent_template_annotated/agent.py",
    "battle_engine/data/agent_template_annotated/agent.yaml",
    "battle_engine/data/agent_template_v2/agent.py",
    "battle_engine/data/agent_template_v2/agent.yaml",
    "battle_engine/data/agent_template_v2_annotated/agent.py",
    "battle_engine/data/agent_template_v2_annotated/agent.yaml",
}


def _wheel(
    tmp_path: Path,
    *,
    omit: str | None = None,
    scripts: dict[str, str] | None = None,
    metadata_version: str = "5.0.0rc1",
) -> Path:
    wheel = tmp_path / "bytefray-5.0.0rc1-py3-none-any.whl"
    files = (EXPECTED_FILES | ADDITIONAL_RUNTIME_FILES) - ({omit} if omit else set())
    entry_points = "[console_scripts]\n" + "".join(
        f"{name} = {target}\n" for name, target in (scripts or SCRIPT_TARGETS).items()
    )
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in files:
            archive.writestr(name, b"")
        archive.writestr("bytefray-5.0.0rc1.dist-info/entry_points.txt", entry_points)
        archive.writestr(
            "bytefray-5.0.0rc1.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: bytefray\nVersion: {metadata_version}\n",
        )
    return wheel


def test_validator_accepts_the_release_critical_wheel_contract(tmp_path: Path) -> None:
    validate_wheel(_wheel(tmp_path))


@pytest.mark.parametrize(
    "missing",
    [
        "battle_engine/data/agent_template_annotated/agent.py",
        "battle_engine/data/agent_template_v2/agent.yaml",
        "battle_engine/data/agent_template_v2_annotated/agent.py",
        "battle_engine/data/starter_agents/v5_dual_team/agent.py",
        "app/assets/branding/bytefray-icon.png",
    ],
)
def test_validator_rejects_a_missing_runtime_resource(tmp_path: Path, missing: str) -> None:
    with pytest.raises(ValueError, match="missing expected files"):
        validate_wheel(_wheel(tmp_path, omit=missing))


def test_validator_rejects_a_misdirected_console_script(tmp_path: Path) -> None:
    scripts = dict(SCRIPT_TARGETS)
    scripts["bytefray"] = "battle_engine.cli:main"

    with pytest.raises(ValueError, match="console script targets"):
        validate_wheel(_wheel(tmp_path, scripts=scripts))


def test_validator_rejects_metadata_version_disagreement(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="metadata version"):
        validate_wheel(_wheel(tmp_path, metadata_version="5.0.0a1"))
