"""Resource-availability coverage for the bundled ``agents create`` templates.

This module exists because of a real, publication-blocking defect that every
other scaffold test missed: ``tools/bytefray.spec`` enumerated the scaffold
template directories by literal name, so when the Agent API v2 template pair
(``agent_template_v2``/``agent_template_v2_annotated``) was added to the
product, the frozen Windows executable silently shipped without it. Both
``bytefray agents create <id> --api-version 2`` invocations failed with
``Agent template resource directory not found`` (exit 2) from the real
distributed application, while the source checkout and the installed wheel
both worked.

The reason the existing suite could not catch it is structural, not an
oversight in any one test: ``engine/tests/test_agent_scaffold.py`` passes an
explicit ``resource_root=ROOT`` into every call, which pins lookups to the
repository's own source tree and therefore proves nothing about what a built
artifact actually contains. The tests here deliberately do the opposite --
they resolve templates through the product's own
:func:`battle_engine.paths.get_resource_root`, with nothing injected, so they
assert the *resource contract of the environment they run in*:

* run from a source checkout, they cover the source tree;
* run from a clean installed wheel, they cover that wheel's package data;
* run with ``BYTEFRAY_FROZEN_EXE`` pointing at a built executable, the smoke
  tests at the bottom cover the frozen artifact itself, out of process.

None of them assert that a line of text exists in a ``.spec`` file; the
spec's own data list is covered separately by
``engine/tests/test_windows_packaging_spec.py``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from battle_engine.agent_api import SUPPORTED_AGENT_API_VERSIONS, load_python_agent
from battle_engine.agent_scaffold import (
    TEMPLATE_DIRECTORIES_BY_API_VERSION,
    TEMPLATE_FILES,
    create_agent,
    template_resource_dir,
)
from battle_engine.agents import discover_agents
from battle_engine.paths import get_resource_root

# Every (api_version, template) pair the product claims to support, derived
# from the canonical inventory rather than restated, so adding a template or
# an Agent API generation extends this coverage automatically instead of
# leaving a silently untested one behind -- the exact failure mode that
# produced the defect above.
SCAFFOLD_VARIANTS = tuple(
    (api_version, template)
    for api_version in sorted(TEMPLATE_DIRECTORIES_BY_API_VERSION)
    for template in sorted(TEMPLATE_DIRECTORIES_BY_API_VERSION[api_version])
)


def _variant_id(variant: tuple[int, str]) -> str:
    api_version, template = variant
    return f"api{api_version}-{template}"


# --------------------------------------------------------------------------
# Resource inventory contract (in-process, real resource root)
# --------------------------------------------------------------------------


def test_scaffold_variants_cover_every_supported_api_version() -> None:
    """Guard the derivation above against silently shrinking to nothing."""

    assert SCAFFOLD_VARIANTS
    assert {api_version for api_version, _ in SCAFFOLD_VARIANTS} == set(
        SUPPORTED_AGENT_API_VERSIONS
    )


@pytest.mark.parametrize("variant", SCAFFOLD_VARIANTS, ids=_variant_id)
def test_every_supported_template_is_present_in_this_environment(
    variant: tuple[int, str],
) -> None:
    """Each supported template must resolve through the *real* resource root.

    No ``resource_root`` is injected. In a frozen application this resolves
    under ``sys._MEIPASS``, in an installed wheel under ``site-packages``,
    and in a checkout under the repository -- so the same assertion covers
    whichever artifact the suite is executed from, and fails if a template
    directory is missing from it.
    """

    api_version, template = variant
    directory = template_resource_dir(
        get_resource_root(), template, api_version=api_version
    )

    assert directory.is_dir()
    missing = [name for name in TEMPLATE_FILES if not (directory / name).is_file()]
    assert not missing, (
        f"template {template!r} for Agent API v{api_version} resolved to "
        f"{directory}, which is missing {missing}"
    )


def test_every_supported_template_resolves_to_a_distinct_directory() -> None:
    """A missing directory must never be masked by another one's contents."""

    resolved = {
        variant: template_resource_dir(
            get_resource_root(), variant[1], api_version=variant[0]
        )
        for variant in SCAFFOLD_VARIANTS
    }
    assert len(set(resolved.values())) == len(resolved), (
        f"scaffold templates share a resource directory: {resolved}"
    )


# --------------------------------------------------------------------------
# Real creation through the real resource root
# --------------------------------------------------------------------------


@pytest.mark.parametrize("variant", SCAFFOLD_VARIANTS, ids=_variant_id)
def test_creation_through_the_real_resource_root_is_structurally_usable(
    variant: tuple[int, str], tmp_path: Path
) -> None:
    """Create each supported variant with no injected resource root, then
    take the created agent through the normal discovery/load path.

    ``test_agent_scaffold.py`` already covers creation semantics in depth;
    what this adds is that the bytes come from whatever artifact is under
    test, and that the result is loadable rather than merely written.
    """

    api_version, template = variant
    result = create_agent(
        "packaged_probe",
        data_root=tmp_path,
        template=template,
        api_version=api_version,
    )

    assert result.manifest_path.is_file()
    assert result.source_path.is_file()

    spec = discover_agents(tmp_path)["packaged_probe"]
    assert spec.kind == "python"
    assert spec.api_version == api_version

    loaded = load_python_agent(spec)
    assert loaded.metadata.api_version == api_version


# --------------------------------------------------------------------------
# Frozen-artifact smoke (out of process, against a built executable)
# --------------------------------------------------------------------------

FROZEN_EXE_ENV_VAR = "BYTEFRAY_FROZEN_EXE"


def _frozen_executable() -> Path:
    """The built executable to smoke, or skip if none was supplied.

    Opt-in by design: a PyInstaller build takes minutes and cannot be a
    precondition of the default suite, but when a build has been produced
    (by ``tools/build_win.ps1`` or a release qualification) these tests are
    the artifact-level proof that source-level coverage cannot give.
    """

    configured = os.environ.get(FROZEN_EXE_ENV_VAR, "").strip()
    if not configured:
        pytest.skip(f"set {FROZEN_EXE_ENV_VAR} to a built executable to run frozen smokes")
    path = Path(configured).expanduser()
    if not path.is_file():
        pytest.fail(f"{FROZEN_EXE_ENV_VAR}={configured!r} is not an existing file")
    return path.resolve()


def _frozen_run(
    executable: Path, args: list[str], *, data_root: Path, cwd: Path
) -> subprocess.CompletedProcess[str]:
    """Run the frozen executable with the repository excluded from lookup.

    ``PYTHONPATH`` is removed and the working directory is a temporary one
    outside the checkout, so a pass cannot come from the frozen process
    falling back to repository files -- the failure this whole module exists
    to catch would otherwise be masked whenever the suite happens to run
    from the source tree.
    """

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["BYTEFRAY_ROOT"] = str(data_root)
    return subprocess.run(
        [str(executable), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


@pytest.mark.parametrize("variant", SCAFFOLD_VARIANTS, ids=_variant_id)
def test_frozen_executable_creates_every_supported_variant(
    variant: tuple[int, str], tmp_path: Path
) -> None:
    """The blocking regression, asserted against the real distributed binary.

    Before the packaging fix this failed for both Agent API v2 rows with
    exit code 2 and ``Agent template resource directory not found``, while
    the v1 rows passed -- reproducing the shipped defect exactly.
    """

    executable = _frozen_executable()
    api_version, template = variant
    agent_id = f"frozen_api{api_version}_{template}"
    data_root = tmp_path / "data"
    work_dir = tmp_path / "work"
    data_root.mkdir()
    work_dir.mkdir()

    args = ["agents", "create", agent_id, "--api-version", str(api_version)]
    if template != "blank":
        args += ["--template", template]

    created = _frozen_run(executable, args, data_root=data_root, cwd=work_dir)
    assert created.returncode == 0, (
        f"frozen `agents create` failed for Agent API v{api_version} template "
        f"{template!r} (exit {created.returncode})\n"
        f"stdout: {created.stdout}\nstderr: {created.stderr}"
    )

    agent_dir = data_root / "agents" / agent_id
    for name in TEMPLATE_FILES:
        assert (agent_dir / name).is_file(), f"{name} missing from {agent_dir}"

    validated = _frozen_run(
        executable, ["agents", "validate", agent_id], data_root=data_root, cwd=work_dir
    )
    assert validated.returncode == 0, (
        f"frozen `agents validate` failed for the scaffold just created for "
        f"Agent API v{api_version} template {template!r} (exit "
        f"{validated.returncode})\nstdout: {validated.stdout}\n"
        f"stderr: {validated.stderr}"
    )


def test_frozen_executable_bundles_every_supported_template_directory(
    tmp_path: Path,
) -> None:
    """Inventory check against the frozen payload's own resource tree.

    Complements the behavioral tests above by naming what is absent when a
    template is dropped, rather than only reporting a non-zero exit.
    """

    executable = _frozen_executable()
    expected = sorted(
        {
            directory
            for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values()
            for directory in templates.values()
        }
    )
    # PyInstaller 6 onedir builds place collected data beside the launcher in
    # `_internal`; older layouts placed it directly beside the executable.
    roots = (executable.parent / "_internal", executable.parent)
    for root in roots:
        data_dir = root / "battle_engine" / "data"
        if data_dir.is_dir():
            break
    else:  # pragma: no cover - defensive, means the build layout changed
        pytest.fail(
            "no battle_engine/data directory found in the frozen payload; "
            f"looked under {[str(root) for root in roots]}"
        )

    missing = [name for name in expected if not (data_dir / name).is_dir()]
    assert not missing, (
        f"the frozen payload at {data_dir} is missing scaffold template "
        f"directories {missing}; `bytefray agents create` will fail for them"
    )


def test_frozen_smoke_is_not_silently_satisfied_by_the_source_tree() -> None:
    """Prove the frozen smokes above are actually exercising an artifact.

    A frozen executable resolves resources under its own payload, never the
    checkout. If the configured binary were really the development console
    script, the smokes would pass for the wrong reason, so pin that the
    executable lives outside this repository's source tree.
    """

    executable = _frozen_executable()
    repo_src = Path(__file__).resolve().parents[2] / "engine" / "src"
    assert not str(executable).startswith(str(repo_src)), (
        f"{FROZEN_EXE_ENV_VAR} points inside the repository source tree "
        f"({executable}); the frozen smoke must run a built artifact"
    )
    assert shutil.which(sys.executable) != str(executable)
