"""CI selection and event plans cannot silently discard ordinary product tests."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.ci_product import ROOT, reduced_modules


def test_reduced_inventory_is_exactly_the_reviewed_research_modules() -> None:
    modules = reduced_modules()
    reviewed = {p.relative_to(ROOT).as_posix()
                for p in (ROOT / "engine/tests").glob("test_v6_e[2-8]*.py")}
    assert len(modules) == 61
    assert set(modules) == reviewed
    # All regular semantics, runtime, compatibility and evidence guards stay.
    retained = ["test_e2_capture_hold_semantics.py", "test_e3_slot_limited_disruption_semantics.py",
                "test_e4_mirrored_pass_order_semantics.py", "test_e5_anchor_placement_semantics.py",
                "test_e6_priced_sensing_semantics.py", "test_frozen_science_boundary.py",
                "test_release_compatibility_record.py", "test_process_containment.py"]
    assert all((ROOT / "engine/tests" / p).is_file() for p in retained)
    assert all("engine/tests/" + p not in modules for p in retained)


def workflow(name: str) -> dict:
    # BaseLoader preserves YAML's `on` key instead of YAML-1.1 boolean conversion.
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


@pytest.mark.parametrize(("event", "full", "versions", "reduced", "advisories"), [
    ("pull_request", False, ["3.13", "3.11"], ["3.11"], []),
    ("push", False, ["3.13", "3.11", "3.12", "3.14"], ["3.11", "3.12"], []),
    ("schedule", True, ["3.13", "3.11", "3.12", "3.14", "3.15", "3.13"], [],
     ["forward", "latest"]),
    ("workflow_dispatch", True, ["3.13", "3.11", "3.12", "3.14"], [], []),
])
def test_actual_workflow_plan(event: str, full: bool, versions: list[str],
                              reduced: list[str], advisories: list[str], tmp_path: Path) -> None:
    script = workflow("ci.yml")["jobs"]["plan"]["steps"][0]["run"]
    python = script.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    ast.parse(python)
    output = tmp_path / "output"
    env = dict(os.environ, FULL=str(full).lower(), PUSH=str(event == "push").lower(),
               GITHUB_EVENT_NAME=event, GITHUB_OUTPUT=str(output))
    subprocess.run([sys.executable, "-c", python], check=True, env=env)
    matrix = json.loads(output.read_text().split("=", 1)[1])["include"]
    assert [m["python"] for m in matrix] == versions
    assert [m["python"] for m in matrix if m["reduced"]] == reduced
    assert [m["profile"] for m in matrix if m["advisory"]] == advisories


@pytest.mark.parametrize("name", ["ci.yml", "linux-gui-smoke.yml"])
def test_product_events_and_cancellation_are_scoped(name: str) -> None:
    data = workflow(name)
    assert data["on"]["push"]["branches"] == ["main", "development/**"]
    assert "pull_request" in data["on"]
    assert "github.workflow" in data["concurrency"]["group"]
    assert "github.event_name" in data["concurrency"]["group"]
    assert "github.run_id" in data["concurrency"]["group"]
    assert data["concurrency"]["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"


def test_release_reuses_full_checks_and_never_publishes() -> None:
    data = workflow("release-qualification.yml")
    assert set(data["on"]) == {"workflow_dispatch"}
    jobs = data["jobs"]
    for name in ["product-and-windows", "gui"]:
        assert jobs[name]["with"]["full"] == "true"
    assert jobs["linux-package"]["uses"] == "./.github/workflows/linux-package.yml"


def test_designer_pipeline_preserves_pytest_failure() -> None:
    job = workflow("linux-gui-smoke.yml")["jobs"]["designer-x11-smoke"]
    test = next(s for s in job["steps"] if "tee designer.log" in s.get("run", ""))
    assert test["shell"] == "bash"  # GitHub explicitly uses -eo pipefail.
    assert "-m gui tests/" in test["run"]
    assert "faulthandler_timeout=300" in test["run"]
    assert job["timeout-minutes"] == "60"
